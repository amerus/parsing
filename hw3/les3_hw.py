import bs4
import requests
from urllib.parse import urljoin
from database import DataBase
import json


class GbBlogParse:

    def __init__(self, start_url: str, db: DataBase):
        self.start_url = start_url
        self.page_done = set()
        self.db = db
        self.c_link = 'https://geekbrains.ru/api/v2/comments?commentable_type=Post&commentable_id=&order=desc'

    def __get(self, url) -> bs4.BeautifulSoup:
        response = requests.get(url)
        self.page_done.add(url)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def run(self, url=None):
        #  Если начальный адрес не задан при вызове функции, то используем адрес класса
        if not url:
            url = self.start_url

        # Если адреса еще нет в сете page_done, то получаем обьект суп и обрабатываем функцией parse
        if url not in self.page_done:
            soup = self.__get(url)
            posts, pagination = self.parse(soup)

            for post_url in posts:
                page_data = self.page_parse(self.__get(post_url), post_url)
                self.save(page_data)
            for p_url in pagination:
                self.run(p_url)

    def parse(self, soup):
        ul_pag = soup.find('ul', attrs={'class': 'gb__pagination'})
        paginations = set(
            urljoin(self.start_url, url.get('href')) for url in ul_pag.find_all('a') if url.attrs.get('href'))
        posts = set(
            urljoin(self.start_url, url.get('href')) for url in soup.find_all('a', attrs={'class': 'post-item__title'}))
        return posts, paginations

    def page_parse(self, soup, url) -> dict:
        data = {
            'post_data': {
                'url': url,
                'title': soup.find('h1').text,
                'image': soup.find('div', attrs={'class': 'blogpost-content'}).find('img').get('src') if soup.find(
                    'div', attrs={'class': 'blogpost-content'}).find('img') else None,
                'date': soup.find('div', attrs={'class': 'blogpost-date-views'}).find('time').get('datetime'),
            },
            'writer': {'name': soup.find('div', attrs={'itemprop': 'author'}).text,
                       'url': urljoin(self.start_url,
                                      soup.find('div', attrs={'itemprop': 'author'}).parent.get('href'))},

            'tags': [],
            'comments': [],

        }

        # Находим идентификатор страницы для каждого дерева комментарий
        page_id = soup.find('div', attrs={'class': 'm-t-xl'}).find('comments')['commentable-id']
        c_params = {'commentable_id': page_id}
        # Получаем response страницы комментариев от API
        comments = requests.get(self.c_link, params=c_params)
        # Разбиваем response супом
        comments_soup = bs4.BeautifulSoup(comments.text, 'lxml')

        def get_comments(comments_soup) -> str:
            """Функция для извлечения комментарий страницы из супа"""
            comments_list = []
            try:
                # Проходим по списку детей и загружаем в формате json библиотекой json
                for item in comments_soup.children:
                    my_json = json.loads(item.text)
                # Извлекаем только текст комментариев из my_json
                for index, item in enumerate(my_json):
                    comments_list.append(my_json[index]["comment"]["body"])
            # Если изначальный суп пуст, то ловим ошибку
            except json.decoder.JSONDecodeError:
                 pass
            # Возвращаем строку комментариев, разбитых дефисами и переносами строк
            # Если список комментариев пуст, то возвращаем None
            return '\n---\n'.join(comments_list) if len(comments_list) > 0 else None

        # Создаем словарь с ключами модели (в models.py)
        for index, value in enumerate(comments):
            comment_data = {
                # строка комментариев или None от функции get_comments
                'text': get_comments(comments_soup),
                # Идентификатор дерева комметрариев
                'post_id': page_id,
                # Адрес родительской статьи
                'url': data['post_data']['url']
            }
            data['comments'].append(comment_data)

        for tag in soup.find_all('a', attrs={'class': "small"}):
            tag_data = {
                'url': urljoin(self.start_url, tag.get('href')),
                'name': tag.text
            }
            data['tags'].append(tag_data)

        return data

    def save(self, page_data: dict):
        self.db.create_post(page_data)


if __name__ == '__main__':
    db = DataBase('sqlite:///gb_blog_with_comments.db')
    parser = GbBlogParse('https://geekbrains.ru/posts', db)

    parser.run()
