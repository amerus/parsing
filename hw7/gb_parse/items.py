# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GbParseItem(scrapy.Item):
    pass

class Insta(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    data = scrapy.Field()
    img = scrapy.Field()

class InstaUser(Insta):
# класс доаолняет Insta
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    following_user_name = scrapy.Field()

class InstaFollow(scrapy.Item):
    _id = scrapy.Field()
    # date_parse = scrapy.Field()
    user_name = scrapy.Field()
    user_id = scrapy.Field()
    following_user_name = scrapy.Field()
