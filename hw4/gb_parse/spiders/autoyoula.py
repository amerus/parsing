import re
import scrapy
import pymongo
from base64 import b64decode

class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']

    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 10,
        'CONCURRENT_REQUESTS': 5,
        'CLOSESPIDER_ITEMCOUNT': 5
    }

    ccs_query = {
        'brands': 'div.ColumnItemList_container__5gTrc div.ColumnItemList_column__5gjdt a.blackLink',
        'pagination': '.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'ads': 'article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = pymongo.MongoClient()['parse_gb_11'][self.name]

    def parse(self, response):
        for brand in response.css(self.ccs_query['brands']):
            yield response.follow(brand.attrib.get('href'), callback=self.brand_page_parse)

    def brand_page_parse(self, response):
        for pag_page in response.css(self.ccs_query['pagination']):
            yield response.follow(pag_page.attrib.get('href'), callback=self.brand_page_parse)

        for ads_page in response.css(self.ccs_query['ads']):
            yield response.follow(ads_page.attrib.get('href'), callback=self.ads_parse)

    def ads_parse(self, response):
        data = {
            'title': response.xpath('//div[contains(@class, "AdvertCard_advertTitle__1S1Ak")]/text()').get(),
            'images': [x.attrib["src"] for x in response.xpath('//figure[contains(@class, "PhotoGallery_photo__36e_r")]//img')],
            'description': response.xpath('//div[contains(@class, "AdvertCard_descriptionInner__KnuRi")]/text()').get(),
            'url': response.url,
            'author': self.js_decoder_author(response),
            'tel': self.get_phone(response),
            'specification': self.get_specifications(response),
        }

        self.db.insert_one(data)

    def get_specifications(self, response):
        return {itm.css('.AdvertSpecs_label__2JHnS::text').get(): itm.css(
            '.AdvertSpecs_data__xK2Qx::text').get() or itm.css('a::text').get() for itm in
                response.css('.AdvertSpecs_row__ljPcX')}

    def js_decoder_author(self, response):
        script = response.xpath('//script[contains(text(), "window.transitState =")]/text()').get()
        re_str = re.compile(r"youlaId%22%2C%22([0-9|a-zA-Z]+)%22%2C%22avatar")
        result = re.findall(re_str, script)
        return f'https://youla.ru/user/{result[0]}' if result else None

    def get_phone(self, response):
        script = response.xpath('//script[contains(text(), "window.transitState =")]/text()').get()
        phone_re = re.compile(r'(%22)([A-Za-z0-9+/]*)(%3D%3D)')
        matched = re.findall(phone_re, script)
        return b64decode(b64decode(f'{matched[0][1]}+"=="')).decode('UTF-8') if matched else None
