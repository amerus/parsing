import scrapy
from scrapy.http import HtmlResponse
from ..items import HhruProjectItem
from ..loaders import HHProjectLoader
from urllib.parse import urljoin


class HhruSpider(scrapy.Spider):
    name = 'hhru'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 15,
        'CONCURRENT_REQUESTS': 5,
        'CLOSESPIDER_ITEMCOUNT':15
    }

    ads_xpath = {
        'name': '//h1[@data-qa="vacancy-title"]/text()',
        'salary': '//p[contains(@class,"vacancy-salary")]//text()',
        'description': '//div[contains(@data-qa,"vacancy-description")]//text()',
        'requirements': '//div[contains(@data-qa, "skills-element")]//text()',
        'author': '//a[@data-qa="vacancy-company-name"]/@href'
    }

    company_xpath = {
        'company_name': '//h1/span[contains(@class, "company-header-title-name")]//text()'
                        ' | //h3[contains(@class, "b-employerpage-vacancies-title")]//text()''',
        'company_url': '//a[@data-qa="sidebar-company-site"]/@href',
        'company_description': 'normalize-space((//div[contains(@class, "company-description")]'
                               ' | //div[contains(@class, "tmpl_hh_about_text")]'
                               ' | //div[contains(@class, "tmpl_hh_about__text")]'
                               ' | //div[contains(@class, "tmpl_hh_about_content")]'
                               ' | //div[contains(@class, "tmpl_hh_about__content")]'
                               ' | //div[contains(@class, "tmpl_hh_subtab__content")]'
                               ' | //div[contains(@class, "_page_slider_content")]'')[1])'
    }

    def parse(self, response):
        next_page = response.css('a.HH-Pager-Controls-Next::attr(href)').extract_first()
        yield response.follow(next_page, callback=self.parse)

        vacancy = response.css( \
            'div.vacancy-serp div.vacancy-serp-item div.vacancy-serp-item__row_header a.bloko-link::attr(href)' \
            ).extract()

        for url in vacancy:
            print(url)
            yield response.follow(url=url, callback=self.vacancy_parse)

    def vacancy_parse(self, response):
        loader = HHProjectLoader(response=response)
        for key, value in self.ads_xpath.items():
            loader.add_xpath(key, value)
        yield response.follow(response.xpath('//a[@data-qa="vacancy-company-name"]/@href').get(), callback=self.company_parse, cb_kwargs=dict(loader=loader))

    def company_parse(self, response, loader):
        loader = loader
        for key, value in self.company_xpath.items():
            loader.add_value(key, response.xpath(value).extract())
        yield loader.load_item()
