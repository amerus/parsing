# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class Insta(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    data = scrapy.Field()
    img = scrapy.Field()

class InstaTag(Insta):
    images = scrapy.Field()

class InstaPost(Insta):
    _id = scrapy.Field()
    images = scrapy.Field()
