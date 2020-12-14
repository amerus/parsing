from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from hhru_project import settings
from hhru_project.spiders.hhru import HhruSpider

if __name__ == '__main__':
    crawl_settings = Settings()
    crawl_settings.setmodule(settings)
    crawl_proc = CrawlerProcess(settings=crawl_settings)
    crawl_proc.crawl(HhruSpider)
    crawl_proc.start()
