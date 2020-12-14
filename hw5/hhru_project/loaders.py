import re
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
#from .items import HhruProjectItem
from .items import HhruCompanyItem


class HHCompanyLoader(ItemLoader):
    #default_item_class = HhruProjectItem
    default_item_class = HhruCompanyItem
    company_url = TakeFirst()
    company_name = TakeFirst()
    company_description = TakeFirst()
