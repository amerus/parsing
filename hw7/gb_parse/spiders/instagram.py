import datetime as dt
import json
import scrapy
from ..items import InstaUser, InstaFollow

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    api_url = '/graphql/query/'
    query_hash = {
        # хэш для окна "following"
        'following': "d04b0a864b4b54837c0d870b0e77e076"
    }

    def __init__(self, login, enc_password, *args, **kwargs):
        # список пользователей, которых необходимо изучить
        self.users = ['motoroffamerus', 'nasahubble']
        # пользователь и пароль, сохраненные в .env
        self.login = login
        self.enc_passwd = enc_password
        super().__init__(*args, **kwargs)
    
    def parse(self, response, **kwargs):
        try:
        # заполняем поля авторизации
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.enc_passwd,
                },
                headers={'X-CSRFToken': js_data['config']['csrf_token']}
            )
        # обходим список пользователей функцией user_page_parse
        except AttributeError as e:
            if response.json().get('authenticated'):
                for user in self.users:
                    yield response.follow(f'/{user}', callback=self.user_page_parse)

    def user_page_parse(self, response):
        # извлекаем graphql
        original_user_data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        yield InstaUser(
            date_parse=dt.datetime.utcnow(),
            data=original_user_data
        )

        yield from self.get_api_follow_request(response, original_user_data)

    def get_api_follow_request(self, response, original_user_data, variables=None):
        if not variables:
            variables = {
                'id': original_user_data['id'],
                'first': 50,
            }
        # Запрашиваем хэш и дополнительные параметры
        url = f'{self.api_url}?query_hash={self.query_hash["following"]}&variables={json.dumps(variables)}'
        # Обращаемся к API фунции с original_user_data
        yield response.follow(url, callback=self.get_api_follow, cb_kwargs={'original_user_data': original_user_data})

    def get_api_follow(self, response, original_user_data):
        if b'application/json' in response.headers['Content-Type']:
            data = response.json()
            yield from self.get_follow_item(original_user_data, data['data']['user']['edge_follow']['edges'])
            # Ловим пагинацию ключом 'has_next_page'
            if data['data']['user']['edge_follow']['page_info']['has_next_page']:
                variables = {
                    'id': original_user_data['id'],
                    'first': 50,
                    'after': data['data']['user']['edge_follow']['page_info']['end_cursor'],
                }
                yield from self.get_api_follow_request(response, original_user_data, variables)

    def get_follow_item(self, original_user_data, follow_users_data):
        for user in follow_users_data:
            yield InstaFollow(
                user_id=original_user_data['id'],
                user_name=original_user_data['username'],
                following_user_name=user['node']['username']
            )
            yield InstaUser(
                date_parse=dt.datetime.utcnow(),
                user_name=user['node']['username'],
                data=user['node']

            )
    
    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", '')[:-1])
