import scrapy
import re
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Compose

from otomoto.items import OtomotoItem

from scrapy import Field
from scrapy import Item
import json
import os.path
import time

from datetime import datetime

SET_NAMES_OF_VISITED_SITED = "visited.json"

def filter_out_array(x):
    x = x.strip()
    return None if x == '' else x

def remove_spaces(x):
    return x.replace(' ', '')


def convert_to_integer(x):
    return int(float(x.replace(",", ".")))


class OtomotoCarLoader(ItemLoader):
    default_output_processor = TakeFirst()

    features_out = MapCompose(filter_out_array)
    images2s_out = MapCompose(filter_out_array)
    price_out = Compose(TakeFirst(), remove_spaces, convert_to_integer)


class ImageItem(Item):
    image_urls = Field()
    images = Field()

class OtomotoSpider(scrapy.Spider):

    allowed_domains = ('otomoto.pl',)
    name = 'otomoto'
    start_urls = ['https://www.otomoto.pl/osobowe/bmw/?search%5Bfilter_enum_damaged%5D=0&page=' + str(i) for i in range(4, 15)] #['https://www.otomoto.pl/osobowe/?page=12']
    #start_urls = start_urls + start_urls
    set_mAll = set()

    def __init__(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("Starting Time =", current_time)

        super(OtomotoSpider, self).__init__()
        self.set_names_of_visited_sited = set([])


        if os.path.isfile(SET_NAMES_OF_VISITED_SITED):
            with open(SET_NAMES_OF_VISITED_SITED, 'r') as f:
                a = json.loads(f.read())
                self.set_names_of_visited_sited = set(a)


    def __del__(self):

        print("Destructor called")
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("Ending Time =", current_time)
        with open(SET_NAMES_OF_VISITED_SITED, 'w') as f:
            f.write(json.dumps(list(self.set_names_of_visited_sited)))



    def parse(self, response):
        m= re.findall(r'https://www.otomoto.pl/oferta/[A-Za-z0-9\-_\\/]*\.html', response.text)
        set_m = set(m)

        print("Number of finded links:",len(set_m), response)

        if len(set_m) == 0:
            print("Saved to wrong.html problematic site")
            with open("wrong.html", 'w') as f:
                f.write(response.text)

        for car_page in set_m:
            if not car_page in self.set_names_of_visited_sited:
                print("add car info")
                yield response.follow(car_page, self.parse_car_page)

        self.set_names_of_visited_sited.update(set_m)

    def parse_car_page(self, response):
        from datetime import datetime

        now = datetime.now()

        current_time = now.strftime("%H:%M:%S")
        print("(get car info) Current Time =", current_time)
        property_list_map = {
            'Marka pojazdu': 'brand',
            'Model pojazdu': 'model',
            'Rok produkcji': 'year',
            'Wersja': 'version',
            'Generacja': 'generation',
            'Przebieg': 'mileage',
            'Pojemność skokowa': 'capacity',
            'Moc': 'horse_power',
            'Rodzaj paliwa': 'fuel_type',
            'Skrzynia biegów': 'transmission',
            'Typ nadwozia': 'type',
            'Liczba drzwi': 'number_of_doors',
            'Kraj pochodzenia': 'origin_country',
            'Kolor': 'color',
            'Rodzaj koloru': 'color_type',
            'Pierwszy właściciel': 'first_owner',
            'Bezwypadkowy': 'no_accidents',
            'Serwisowany w ASO': 'aso',
            'Stan': 'condition',
            'Napęd': 'drive',
            'Emisja CO2': 'co2'
        }

        loader = OtomotoCarLoader(OtomotoItem(), response=response)

        for params in response.css('.offer-params__item'):
            property_name = params.css('.offer-params__label::text').extract_first().strip()
            if property_name in property_list_map:
                css = params.css('.offer-params__value::text').extract_first().strip()
                if css == '':
                    css = params.css('a::text').extract_first().strip()
                loader.add_value(property_list_map[property_name], css)

        loader.add_css('price', '.offer-price__number::text')
        loader.add_css('price_currency', '.offer-price__currency::text')

        loader.add_css('features', '.offer-features__item::text')
        loader.add_value('url', response.url)

        m = re.findall(r'https:\\/\\/ireland\.apollo\.olxcdn\.com\\/v1\\/files\\/[A-Za-z0-9\-.\\/_]*;', response.text)

        set_m = set(m)

        list_m = [car_img.replace("\\/", '/') for car_img in set_m]

        print("We find:", len(list(set_m)), "photos for", response)

        loader.add_value("images2s", list_m)

        for car_img in list_m:
            yield {'image_urls': [car_img]}
            print("Saved image from:", car_img)
        yield loader.load_item()