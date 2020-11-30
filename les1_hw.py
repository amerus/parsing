import os
import json
import time
import requests

from pathlib import Path

class Parse5ka:
    _headers = {
        # Прописываем агент клиента для избежания блокировки автоматических запросов
        # По-умолчанию, это значение у requests - "python-requests"
        'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0",
    }
    _params = {
        # Запрашиваем по 50 наименований товара в словаре _params, но сервер будет ограничивать верхний порог
        # самостоятельно
        'records_per_page': 50,
    }

    def __init__(self, start_url):
        self.start_url = start_url

    @staticmethod
    # Определяем метод, как staticmethod, так как он сам не использует других составляющих класса
    # Метод также protected, так как правильнее вызывать метод run, который обратится к parse, а тот к _get
    def _get(*args, **kwargs) -> requests.Response:
        while True:
            try:
                # Пробуем сделать запрос к ресурсу
                response = requests.get(*args, **kwargs)
                # Нужный для нас код - это только 200
                # Если ответ не 200, то возводим ошибку, которая будет перехвачена для паузы в 1/4 секунды
                if response.status_code != 200:
                    # todo класс исключение (Exception) должен быть заточен под именно данную ошибку
                    raise Exception
                # Если ответ получен с кодом 200, то возвращаем response
                return response
            except Exception:
                time.sleep(0.25)

    def parse(self, url):
        # Данная функция - генератор, которая продолжает выдавать данные до тех пор, пока переменная url не False
        # url становится False, когда значение 'next' в ответе json не найдено
        params = self._params
        while url:
            response: requests.Response = self._get(url, params=params, headers=self._headers)
            # Переопределяем словарь params, чтобы избежать задвоение параметров в следующем проходе цикла
            if params:
                params = {}
            data: dict = response.json()
            url = data.get('next')
            yield data.get('results')

    def run(self):
        # Функция пользуется результатами генератора parse для сохранения промежуточных данных сразу
        for products in self.parse(self.start_url):
            for product in products:
                self._save_to_file(product, product['id'])
            time.sleep(0.1)

    @staticmethod
    def _save_to_file(product, file_name):
        path = Path(os.path.dirname(__file__)).joinpath('products').joinpath(f'{file_name}.json')
        # Папаметр encoding='UTF-8' необходим при запуске на Windows OS
        with open(path, 'w', encoding='UTF-8') as file:
            json.dump(product, file, ensure_ascii=False)


class ParserCatalog(Parse5ka):

    def __init__(self, start_url, category_url):
        # Перегружаем инит для принятия адреса со списком категорий
        self.category_url = category_url
        super().__init__(start_url)

    def get_categories(self, url):
        # Получаем список категорий в формате JSON
        response = self._get(url, headers=self._headers)
        return response.json()

    def run(self):
        for category in self.get_categories(self.category_url):
            # Промежуточный словарь для потребления меньшего количества памяти при большом количестве категорий
            # Каждая категория товара будет выведена и сохранена в отдельный файл
            data = {
                "name": category['parent_group_name'],
                'code': category['parent_group_code'],
                "products": [],
            }
            # Добавляем код категории товара в словарь _params,  унаследованный из класса  Parse5ka
            self._params['categories'] = category['parent_group_code']

            for products in self.parse(self.start_url):
                # Идем по списку товров (products), добавляя каждый в словарь data и сохраняя в отдельный файл
                # под названием категории товара
                data["products"].extend(products)
            self._save_to_file(
                data,
                category['parent_group_code']
            )


if __name__ == '__main__':
    parser = ParserCatalog('https://5ka.ru/api/v2/special_offers/', 'https://5ka.ru/api/v2/categories/')
    parser.run()
