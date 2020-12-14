import scrapy
from scrapy.http import HtmlResponse
from ..items import HhruProjectItem
from ..loaders import HHCompanyLoader
from urllib.parse import urljoin


class HhruSpider(scrapy.Spider):
    name = 'hhru'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 10,
        'CONCURRENT_REQUESTS': 5,
        'CLOSESPIDER_ITEMCOUNT': 5
    }

    company_xpath = {
        'company_name': '//h1/span[contains(@class, "company-header-title-name")]/text()',
        'company_url': '//a[contains(@data-qa, "company-site")]/@href',
        'company_description': '//div[contains(@data-qa, "company-description")]//text()',
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
        name = response.xpath('//div[contains(@class,"vacancy-title")]//text()').get()
        sal_uni = response.xpath('//p[contains(@class,"vacancy-salary")]//text()').extract()
        salary = ' '.join(sal_uni).replace('\xa0', '')
        desc = response.xpath('//div[contains(@data-qa,"vacancy-description")]//text()').extract()
        desc_str = ''.join(desc)
        skills = response.xpath('//div[contains(@data-qa, "skills-element")]//text()').extract()
        author = response.xpath('//a[contains(@class,"vacancy-company-name")]').attrib['href']
        author_full = urljoin(response.url, author)

        yield HhruProjectItem(name=name, salary=salary, description=desc_str, requirements=skills, author=author_full)
        yield response.follow(response.xpath('//a[@data-qa="vacancy-company-name"]/@href').get(), callback=self.company_parse)

    def company_parse(self, response, **kwargs):
        loader = HHCompanyLoader(response=response)
        loader.add_value('company_url', response.url)
        for key, value in self.company_xpath.items():
            loader.add_xpath(key, value)

        yield loader.load_item()
