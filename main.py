from scrapy import cmdline

cmdline.execute("scrapy crawl -L WARNING otomoto -o otomoto.json".split())