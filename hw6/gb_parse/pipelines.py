# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient
import os

class GbParsePipeline:
    def __init__(self):
        self.db = MongoClient()['m']
    
    def process_item(self, item, spider):
        collection = self.db[spider.name]
        collection.insert_one(item)
        return item


class GbImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        try:
            media_url = item.get('data').get('thumbnail_src')
        except (ValueError, TypeError):
            media_url = None
        finally:
            if media_url:
                yield Request(media_url)

    def item_completed(self, results, item, info):
        item['images'] = [itm[1] for itm in results]
        return item
