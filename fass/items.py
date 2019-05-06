# -*- coding: utf-8 -*-

# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Product(scrapy.Item):
    name = scrapy.Field()
    id = scrapy.Field()
    url = scrapy.Field()
    atc = scrapy.Field()
    shape = scrapy.Field()
    desc = scrapy.Field()
    weight = scrapy.Field()
    available = scrapy.Field()
    prescription = scrapy.Field()
    company_id = scrapy.Field()
    company_name = scrapy.Field()
    substances_ids = scrapy.Field()
    text = scrapy.Field()
    

class Substance(scrapy.Item):
    name = scrapy.Field()
    id = scrapy.Field()
    url = scrapy.Field()
    chemical = scrapy.Field()
    keywords = scrapy.Field()


class Company(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()
    id = scrapy.Field()
    text = scrapy.Field()
