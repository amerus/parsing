import os
import time
import datetime as dt
import requests
import bs4
import pymongo
import dotenv
from urllib.parse import urljoin

dotenv.load_dotenv('.env')

MONTHS = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "май": 5,
    "мая": 5,
    "июн": 6,
    "июл": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12,
}


class MagnitParse:
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0",
    }

    def __init__(self, start_url):

        self.start_url = start_url
        client = pymongo.MongoClient(os.getenv('DATA_BASE'))
        self.db = client['gb_parse_11']

    def get_product(self, product_soup):
        dt_parser = self.date_parse(product_soup.find('div', attrs={'class': 'card-sale__date'}).text)

        product_template = {
            'url': lambda soup: urljoin(self.start_url, soup.get('href')),
            'promo_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__header'}).text,
            'product_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__title'}).text,
            'image_url': lambda soup: urljoin(self.start_url, soup.find('img').get('data-src')),
            'date_from': lambda _: next(dt_parser),
            'date_to': lambda _: next(dt_parser),
        }

        product_result = {}
        for key, value in product_template.items():
            try:
                product_result[key] = value(product_soup)
            except (AttributeError, ValueError, StopIteration):
                continue

        return product_result

    @staticmethod
    def _get(*args, **kwargs):
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code != 200:
                    raise Exception
                return response
            except Exception:
                time.sleep(0.5)

    def soup(self, url) -> bs4.BeautifulSoup:
        response = self._get(url, headers=self.headers)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self):
        soup = self.soup(self.start_url)
        for product in self.parse(soup):
            self.save(product)

    @staticmethod
    def date_parse(date_string: str):
        date_list = date_string.replace('с ', '', 1).replace('\n', '').split('до')
        # Месяц старта акции
        act_from = MONTHS[date_list[0].split()[1][:3]]
        # Месяц окончания акции
        act_to = MONTHS[date_list[1].split()[1][:3]]
        # Значение года по-умолчанию
        year = dt.datetime.now().year
        for key, date in enumerate(date_list[:]):
            tmp_date = date.split()
            # Сохраняем цифровое значение месяца
            month = MONTHS[tmp_date[1][:3]]
            # Добавляем год по-умолчанию
            date_list[key] = tmp_date[0] + " " + str(month) + " " + str(year)
            # Если значение старта акции больше ее окончания, то увеличиваем значение года на 1
            if act_to < act_from:
                date_list[-1] = tmp_date[0] + " " + str(month) + " " + str(year + 1)

        for date in date_list:
             temp_date = date.split()
             yield dt.datetime(year=int(temp_date[2]), day=int(temp_date[0]), month=int(temp_date[1]))

    def parse(self, soup: bs4.BeautifulSoup) -> dict:
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})

        for product in catalog.findChildren('a'):
            try:
                pr_data = self.get_product(product)
            except AttributeError:
                continue
            yield pr_data

    def save(self, product):
        collection = self.db["magnit_11"]
        collection.insert_one(product)


if __name__ == '__main__':
    parser = MagnitParse('https://magnit.ru/promo/?geo=moskva')
    parser.run()
