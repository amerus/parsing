# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class HhruProjectItem(scrapy.Item):
    _id = scrapy.Field()
    name = scrapy.Field()
    salary = scrapy.Field()
    description = scrapy.Field()
    requirements = scrapy.Field()
    author = scrapy.Field()
    company_url = scrapy.Field()
    company_name = scrapy.Field()
    company_description = scrapy.Field()

