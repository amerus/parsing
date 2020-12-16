from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from .items import HhruProjectItem
from urllib.parse import urljoin
import re

def clean_salary(data:list):
    return ' '.join(data).replace('\xa0', '')

def get_url(data: list):
    part = str(''.join(data))
    return urljoin("https://hh.ru", part)

def get_name(data: list):
    try:
        data_sub = re.sub(r'Вакансии компании', "", ''.join(data))
        return data_sub
    except ValueError:
        return data
    return data

def get_description(data: list):
    return ' '.join(data)

class HHProjectLoader(ItemLoader):
    default_item_class = HhruProjectItem
    name_in = ''.join
    name_out = TakeFirst()
    salary_in = MapCompose(clean_salary)
    salary_out = clean_salary
    description_in = ''.join
    description_out = TakeFirst()
    requirements = TakeFirst()
    author_in = MapCompose(get_url)
    author_out = get_url
    company_url_out = TakeFirst()
    company_name_in = MapCompose(get_name)
    company_name_out = get_name
    company_description_in = MapCompose(get_description)
    company_description_out = TakeFirst()

