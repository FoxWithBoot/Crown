from parameterized import parameterized
from rest_framework.test import APITestCase

from .factories import PageFactory
from ..models import Page
from user.tests import factories
from road.models import Road


class TestPage(APITestCase):
    url = '/page/'
    count = 10

    @classmethod
    def setUpTestData(cls):
        users = factories.UserFactory.create_batch(3)
        u = users[0]
        u2 = users[1]
        u3 = users[2]

        page1 = PageFactory.create(author=users[0])  # 1
        pages1 = PageFactory.create_batch(3, parent=page1, author=users[0])  # 2 3 4

        page2 = PageFactory.create(author=users[1], is_public=True)  # 5
        pages2 = PageFactory.create_batch(2, parent=page2, author=users[1], is_public=True)  # 6 7
        p1 = PageFactory.create(parent=page2, author=users[0], is_public=True)  # 8
        p1 = PageFactory.create(parent=page2, author=users[2], is_public=False)  # 9
        p1 = PageFactory.create(parent=p1, author=users[2], is_public=False)  # 10

    def login(self, username):
        response = self.client.post('/user/token/', {'username': username, 'password': '123'}, format='json')
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    @parameterized.expand([
        (None, {}, 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User0', {}, 201, '{"id":11,"author":{"id":1,"username":"User0"},"is_public":false,'
                           '"title":"Страница","parent":null}'),
        ('User0', {'title': 'Page'}, 201, '{"id":11,"author":{"id":1,"username":"User0"},"is_public":false,'
                                          '"title":"Page","parent":null}'),
        ('User0', {'title': 'Page' * 100}, 400,
         '{"title":["Убедитесь, что это значение содержит не более 150 символов."]}'),
        # --------------------------------------------------------------------------------------------------------------
        ('User0', {'parent': None}, 201, '{"id":11,"author":{"id":1,"username":"User0"},"is_public":false,'
                                         '"title":"Страница","parent":null}'),
        ('User0', {'parent': 1}, 201, '{"id":11,"author":{"id":1,"username":"User0"},"is_public":false,'
                                      '"title":"Страница","parent":1}'),
        ('User0', {'parent': 5}, 201, '{"id":11,"author":{"id":1,"username":"User0"},"is_public":false,'
                                      '"title":"Страница","parent":5}'),
        ('User1', {'parent': 1}, 400, '{"parent":["Попытка доступа к чужой приватной странице"]}'),
        ('User1', {'parent': 19}, 400, '{"parent":["Недопустимый первичный ключ \\"19\\" - объект не существует."]}'),
        ('User1', {'parent': -19}, 400, '{"parent":["Недопустимый первичный ключ \\"-19\\" - объект не существует."]}'),
        ('User1', {'parent': 'rt'}, 400,
         '{"parent":["Некорректный тип. Ожидалось значение первичного ключа, получен str."]}'),
    ])
    def test_create_page(self, username, data, status, resp):
        if username:
            self.login(username)
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp
        if status == 201:
            assert Page.objects.count() == self.count + 1
            assert Road.objects.count() == self.count + 1
        else:
            assert Page.objects.count() == self.count
            assert Road.objects.count() == self.count

    @parameterized.expand([
        (None, 5, 200, '{"id":5,"author":{"id":2,"username":"User1"},"is_public":true,"title":"Page_4","parent":null}'),
        (None, 1, 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User2', 1, 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', 1, 200, '{"id":1,"author":{"id":1,"username":"User0"},"is_public":false,"title":"Page_0","parent":null}'),
        ('User0', 101, 404, '{"detail":"Страница не найдена."}'),
    ])
    def test_get_page_info(self, username, page_id, status, resp):
        if username:
            self.login(username)
        response = self.client.get(self.url+str(page_id)+'/', format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '1', 401, '{"detail":"Учетные данные не были предоставлены."}'),
        (None, '5', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
             '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]},'
             '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
             '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]}]}'),
        (None, '7', 200, '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]}'),
        ('User0', '1', 200,
         '{"id":1,"author":{"id":1,"username":"User0"},"title":"Page_0","is_public":false,"subpages":['
             '{"id":2,"author":{"id":1,"username":"User0"},"title":"Page_1","is_public":false,"subpages":[]},'
             '{"id":3,"author":{"id":1,"username":"User0"},"title":"Page_2","is_public":false,"subpages":[]},'
             '{"id":4,"author":{"id":1,"username":"User0"},"title":"Page_3","is_public":false,"subpages":[]}]}'),
        ('User0', '5', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
             '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]},'
             '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
             '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]}]}'),
        ('User0', '7', 200,
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]}'),
        ('User1', '1', 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User1', '5', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
             '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]},'
             '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
             '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]}]}'),
        ('User2', '5', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
             '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]},'
             '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
             '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},'
             '{"id":9,"author":{"id":3,"username":"User2"},"title":"Page_8","is_public":false,"subpages":['
                '{"id":10,"author":{"id":3,"username":"User2"},"title":"Page_9","is_public":false,"subpages":[]}]}]}'),
        ('User1', '7', 200,
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]}'),
        ('User1', '77', 404, '{"detail":"Страница не найдена."}'),
    ])
    def test_get_subpages_tree(self, username, address, status, resp):
        if username:
            self.login(username)
        response = self.client.get(self.url + address + '/subpages_tree/', format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    # @parameterized.expand([
    #     (None, '/page-writer-list/', 401, '{"detail":"Учетные данные не были предоставлены."}'),
    #     ('User1', '/page-writer-list/', 200, '[{"id":5,"title":"Page_4"},{"id":6,"title":"Page_5"},{"id":7,"title":"Page_6"}]'),
    #     ('User1', '/page-writer-list/?parent=', 200, '[{"id":5,"title":"Page_4"},{"id":6,"title":"Page_5"}]'),
    # ])
    # def test_pages_list_writer(self, username, url, status, resp):
    #     if username:
    #         self.login(username)
    #     response = self.client.get(url, format='json')
    #     assert response.status_code == status
    #     assert response.content.decode('utf-8') == resp
