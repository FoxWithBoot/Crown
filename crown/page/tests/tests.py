from parameterized import parameterized
from rest_framework.test import APITestCase
import networkx as nx
from pyvis.network import Network

from .factories import PageFactory
from ..models import Page
from user.tests import factories
from road.models import Road
from road.tests.factories import RoadFactory
from road.tests.tests import draw_roads_graph


def draw_pages_graph(filename):
    pages = list(Page.objects.all())
    nx_graph = nx.DiGraph()
    for i in pages:
        nx_graph.add_node(i.id, group=i.author.id, shape='circle' if i.is_public else 'box', label=str(i.id),
                          title=f'title: {i.title}\n'
                                f'public: {i.is_public}\n'
                                f'author: {i.author}\n'
                                f'floor: {i.floor}', )
    for i in pages:
        if i.parent:
            nx_graph.add_edge(i.parent.id, i.id)

    nt = Network(height='1000px', width='1000px', notebook=True, directed=True, layout=True)
    nt.from_nx(nx_graph)
    nt.toggle_physics(False)
    nt.show_buttons(filter_=['layout', 'physics'])
    nt.show(f'page/tests/graphics/{filename}.html')


class TestPage(APITestCase):
    url = '/page/'
    count = 11
    roads_count = 17

    @classmethod
    def setUpTestData(cls):
        users = factories.UserFactory.create_batch(3)
        u = users[0]
        u2 = users[1]
        u3 = users[2]

        page1 = PageFactory.create(author=users[0])  # P1
        pages1 = PageFactory.create_batch(3, parent=page1, author=users[0])  # P2 P3 P4

        page2 = PageFactory.create(author=users[1], is_public=True)  # P5
        pages2 = PageFactory.create_batch(2, parent=page2, author=users[1], is_public=True)  # P6 P7
        p1 = PageFactory.create(parent=page2, author=users[0], is_public=True)  # P8
        p1 = PageFactory.create(parent=page2, author=users[2], is_public=False)  # P9
        p1 = PageFactory.create(parent=p1, author=users[2], is_public=False)  # P10

        PageFactory.create(parent=pages1[2], author=users[2])
        draw_pages_graph("start_graph")

        RoadFactory.create_batch(3, page=pages2[1], author=u, parent=Road.objects.get(page=pages2[1], parent=None))
        RoadFactory.create_batch(3, page=pages2[0], author=u2, parent=Road.objects.get(page=pages2[0], parent=None), is_public=True)
        draw_roads_graph("start_graph")

    def login(self, username):
        response = self.client.post('/user/token/', {'username': username, 'password': '123'}, format='json')
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    @parameterized.expand([
        (None, {}, 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User0', {}, 201, '{"id":12,"author":{"id":1,"username":"User0"},'
                           '"ancestry":[{"id":12,"title":"Страница"}],"is_public":false,'
                           '"title":"Страница","parent":null}'),
        ('User0', {'title': 'Page'}, 201, '{"id":12,"author":{"id":1,"username":"User0"},'
                                          '"ancestry":[{"id":12,"title":"Page"}],"is_public":false,'
                                          '"title":"Page","parent":null}'),
        ('User0', {'title': 'Page' * 100}, 400,
         '{"title":["Убедитесь, что это значение содержит не более 150 символов."]}'),
        # --------------------------------------------------------------------------------------------------------------
        ('User0', {'parent': None}, 201, '{"id":12,"author":{"id":1,"username":"User0"},'
                                         '"ancestry":[{"id":12,"title":"Страница"}],"is_public":false,'
                                         '"title":"Страница","parent":null}'),
        ('User0', {'parent': 1}, 201, '{"id":12,"author":{"id":1,"username":"User0"},'
                                      '"ancestry":[{"id":1,"title":"Page_0"},{"id":12,"title":"Страница"}],'
                                      '"is_public":false,"title":"Страница","parent":1}'),
        ('User0', {'parent': 5}, 201, '{"id":12,"author":{"id":1,"username":"User0"},'
                                      '"ancestry":[{"id":5,"title":"Page_4"},{"id":12,"title":"Страница"}],'
                                      '"is_public":false,"title":"Страница","parent":5}'),
        ('User1', {'parent': 1}, 400, '{"parent":["Попытка доступа к чужой приватной странице"]}'),
        ('User1', {'parent': 19}, 400, '{"parent":["Недопустимый первичный ключ \\"19\\" - объект не существует."]}'),
        ('User1', {'parent': -19}, 400, '{"parent":["Недопустимый первичный ключ \\"-19\\" - объект не существует."]}'),
        ('User1', {'parent': 'rt'}, 400,
         '{"parent":["Некорректный тип. Ожидалось значение первичного ключа, получен str."]}'),
        ('User2', {'parent': 10}, 201,
         '{"id":12,"author":{"id":3,"username":"User2"},'
         '"ancestry":[{"id":5,"title":"Page_4"},{"id":9,"title":"Page_8"},{"id":10,"title":"Page_9"},{"id":12,"title":"Страница"}],'
         '"is_public":false,"title":"Страница","parent":10}'),
        # --------------------------------------------------------------------------------------------------------------
        ('User1', {'parent': 1, 'where': {}}, 400, '{"parent":["Попытка доступа к чужой приватной странице"],"where":{"before_after":["Обязательное поле."],"page":["Обязательное поле."]}}'),
        ('User0', {'parent': 1, 'where': {}}, 400, '{"where":{"before_after":["Обязательное поле."],"page":["Обязательное поле."]}}'),
        ('User0', {'parent': 1, 'where': {'before_after': 'aas', 'page': 2}}, 400, '{"where":{"before_after":["Значения aas нет среди допустимых вариантов."]}}'),
        ('User0', {'parent': 1, 'where': {'before_after': 'after', 'page': 1}}, 400, '{"where":{"page":["Указанная страница не является дочерней к parent"]}}'),
        ('User0', {'parent': 1, 'where': {'before_after': 'after', 'page': 101}}, 400, '{"where":{"page":["Такой страницы не существует"]}}'),
        ('User0', {'parent': 1, 'where': {'before_after': 'after', 'page': 'sd'}}, 400, '{"where":{"page":["Значение “sd” должно быть целым числом."]}}'),
        ('User0', {'parent': 1, 'where': {'before_after': 'after', 'page': 2}}, 201,
         '{"id":12,"author":{"id":1,"username":"User0"},'
         '"ancestry":[{"id":1,"title":"Page_0"},{"id":12,"title":"Страница"}],'
         '"is_public":false,"title":"Страница","parent":1}'),
        ('User0', {'parent': 1, 'where': {'before_after': 'before', 'page': 2}}, 201,
         '{"id":12,"author":{"id":1,"username":"User0"},'
         '"ancestry":[{"id":1,"title":"Page_0"},{"id":12,"title":"Страница"}],'
         '"is_public":false,"title":"Страница","parent":1}'),
        ('User1', {'parent': 5, 'where': {'before_after': 'before', 'page': 9}}, 400,
         '{"where":{"page":["Попытка доступа к чужой приватной странице"]}}'),
        ('User1', {'parent': 5, 'where': {'before_after': 'before', 'page': 8}}, 201,
         '{"id":12,"author":{"id":2,"username":"User1"},'
         '"ancestry":[{"id":5,"title":"Page_4"},{"id":12,"title":"Страница"}],'
         '"is_public":false,"title":"Страница","parent":5}'),
                ])
    def test_create_page(self, username, data, status, resp):
        if username:
            self.login(username)
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp
        if status == 201:
            assert Page.objects.count() == self.count + 1
            assert Road.objects.count() == self.roads_count + 1
            if data.get('where', None):
                draw_pages_graph("create_page_" + data['where']['before_after'] + "_" + str(data['where']['page']))
        else:
            assert Page.objects.count() == self.count
            assert Road.objects.count() == self.roads_count

    @parameterized.expand([
        (None, 5, 200, '{"id":5,"author":{"id":2,"username":"User1"},'
                       '"ancestry":[{"id":5,"title":"Page_4"}],'
                       '"is_public":true,"title":"Page_4","parent":null}'),
        (None, 1, 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User2', 1, 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', 1, 200, '{"id":1,"author":{"id":1,"username":"User0"},'
                          '"ancestry":[{"id":1,"title":"Page_0"}],'
                          '"is_public":false,"title":"Page_0","parent":null}'),
        ('User2', 10, 200, '{"id":10,"author":{"id":3,"username":"User2"},'
                           '"ancestry":['
                               '{"id":5,"title":"Page_4"},'
                               '{"id":9,"title":"Page_8"},'
                               '{"id":10,"title":"Page_9"}],'
                           '"is_public":false,"title":"Page_9","parent":9}'),
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
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'
         ),
        (None, '7', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        ('User0', '1', 200,
         '{"id":1,"author":{"id":1,"username":"User0"},"title":"Page_0","is_public":false,"subpages":['
         '{"id":4,"author":{"id":1,"username":"User0"},"title":"Page_3","is_public":false,"subpages":[]},'
         '{"id":3,"author":{"id":1,"username":"User0"},"title":"Page_2","is_public":false,"subpages":[]},'
         '{"id":2,"author":{"id":1,"username":"User0"},"title":"Page_1","is_public":false,"subpages":[]}]}'),
        ('User0', '5', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},'
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        ('User0', '7', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},'
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        ('User1', '1', 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User1', '5', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        ('User2', '10', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":9,"author":{"id":3,"username":"User2"},"title":"Page_8","is_public":false,"subpages":['
            '{"id":10,"author":{"id":3,"username":"User2"},"title":"Page_9","is_public":false,"subpages":[]}]},'
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        ('User1', '7', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        ('User1', '77', 404, '{"detail":"Страница не найдена."}'),
        ('User2', '11', 403, '{"detail":"Доступ разрешен только автору."}'),
    ])
    def test_get_subpages_tree(self, username, address, status, resp):
        if username:
            self.login(username)
        response = self.client.get(self.url + address + '/subpages_tree/', format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '5', '1', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},'
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        (None, '5', 'User0', 400, '{"parent":["Некорректный id автора"]}'),
        ('User1', '5', '1', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},'
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        ('User1', '5', '2', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        ('User2', '5', '1', 200,
         '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":['
         '{"id":9,"author":{"id":3,"username":"User2"},"title":"Page_8","is_public":false,"subpages":['
         '{"id":10,"author":{"id":3,"username":"User2"},"title":"Page_9","is_public":false,"subpages":[]}]},'
         '{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},'
         '{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},'
         '{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
    ])
    def test_get_subpages_tree_with_author_filter(self, username, address, author, status, resp):
        if username:
            self.login(username)
        url = "{0}{1}/subpages_tree/?other_author={2}".format(self.url, address, author)
        response = self.client.get(url, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '5/subpages_tree/?other_author=1&other_author=2', 200, '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":[{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        (None, '5/subpages_tree/?other_author=1&other_author=22', 200, '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":[{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
        (None, '5/subpages_tree/?other_author=1&other_author=2r2', 400, '{"parent":["Некорректный id автора"]}'),
        (None, '5/subpages_tree/?other_author=1&other_author=3', 200, '{"id":5,"author":{"id":2,"username":"User1"},"title":"Page_4","is_public":true,"subpages":[{"id":8,"author":{"id":1,"username":"User0"},"title":"Page_7","is_public":true,"subpages":[]},{"id":7,"author":{"id":2,"username":"User1"},"title":"Page_6","is_public":true,"subpages":[]},{"id":6,"author":{"id":2,"username":"User1"},"title":"Page_5","is_public":true,"subpages":[]}]}'),
    ])
    def test_get_subpages_tree_with_authors_list_filter(self, username, address, status, resp):
        if username:
            self.login(username)
        response = self.client.get(self.url+address, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '5', 200, '[{"id":2,"username":"User1"},{"id":1,"username":"User0"}]'),
        (None, '7', 200, '[{"id":2,"username":"User1"},{"id":1,"username":"User0"}]'),
        (None, '3', 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User0', '9', 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', '1', 200, '[{"id":1,"username":"User0"}]'),
        ('User0', '8', 200, '[{"id":2,"username":"User1"},{"id":1,"username":"User0"}]'),
        ('User1', '5', 200, '[{"id":2,"username":"User1"},{"id":1,"username":"User0"}]'),
        ('User2', '5', 200, '[{"id":2,"username":"User1"},{"id":1,"username":"User0"},{"id":3,"username":"User2"}]'),
        ('User2', '55', 404, '{"detail":"Страница не найдена."}'),
    ])
    def test_get_list_authors_in_space(self, username, address, status, resp):
        if username:
            self.login(username)
        url = "{0}{1}/other_authors_list/".format(self.url, address)
        response = self.client.get(url, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '1', {}, 401, '{"detail":"Учетные данные не были предоставлены."}', 7, 7),
        ('User1', '1', {}, 403, '{"detail":"Доступ разрешен только автору."}', 7, 7),
        ('User1', '101', {}, 404, '{"detail":"Страница не найдена."}', 7, 7),
        ('User1', '5', {'title': 'YES'}, 200, '{"id":5,"author":{"id":2,"username":"User1"},'
                                              '"ancestry":[{"id":5,"title":"YES"}],'
                                              '"is_public":true,"title":"YES","parent":null}', 7, 7),
        ('User1', '5', {'title': 'YES'*51}, 400,
         '{"title":["Убедитесь, что это значение содержит не более 150 символов."]}', 7, 7),
        ('User1', '5', {'is_public': True}, 200, '{"id":5,"author":{"id":2,"username":"User1"},'
                                                 '"ancestry":[{"id":5,"title":"Page_4"}],'
                                                 '"is_public":true,"title":"Page_4","parent":null}', 7, 4),
        ('User1', '5', {'is_public': False}, 200, '{"id":5,"author":{"id":2,"username":"User1"},'
                                                 '"ancestry":[{"id":5,"title":"Page_4"}],'
                                                 '"is_public":false,"title":"Page_4","parent":null}', 17, 11),
        ('User0', '8', {'is_public': False}, 200, '{"id":8,"author":{"id":1,"username":"User0"},'
                                                  '"ancestry":[{"id":5,"title":"Page_4"},{"id":8,"title":"Page_7"}],'
                                                  '"is_public":false,"title":"Page_7","parent":5}', 10, 8),
        ('User0', '6', {'is_public': False}, 403, '{"detail":"Доступ разрешен только автору."}', 7, 7),
        ('User1', '6', {'is_public': False}, 200, '{"id":6,"author":{"id":2,"username":"User1"},'
                                                  '"ancestry":[{"id":5,"title":"Page_4"},{"id":6,"title":"Page_5"}],'
                                                  '"is_public":false,"title":"Page_5","parent":5}', 13, 8),
        ('User2', '10', {'is_public': True}, 200, '{"id":10,"author":{"id":3,"username":"User2"},'
                                                  '"ancestry":[{"id":5,"title":"Page_4"},{"id":9,"title":"Page_8"},{"id":10,"title":"Page_9"}],'
                                                  '"is_public":true,"title":"Page_9","parent":9}', 9, 6),
        ('User2', '9', {'is_public': True}, 200, '{"id":9,"author":{"id":3,"username":"User2"},'
                                                  '"ancestry":[{"id":5,"title":"Page_4"},{"id":9,"title":"Page_8"}],'
                                                  '"is_public":true,"title":"Page_8","parent":5}', 8, 5),
        ('User2', '11', {'is_public': True}, 400,
         '{"is_public":["Автор одной из родительских страниц отменил публикацию."]}', 7, 4),
    ])
    def test_update_page(self, username, address, data, status, resp, count_r, count_p):
        if username:
            self.login(username)
        response = self.client.patch(self.url+address+"/", data, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp
        if data.get('is_public', None):
            assert Road.objects.filter(is_public=data.get('is_public')).count() == count_r
            assert Page.objects.filter(is_public=data.get('is_public')).count() == count_p

    @parameterized.expand([
        (None, '1', {}, 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User2', '1', {}, 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', '1', {'before_after': 'ee'}, 400, '{"before_after":["Значения ee нет среди допустимых вариантов."],"page":["Обязательное поле."]}'),
        ('User0', '1', {'page': 9}, 400, '{"page":["Попытка доступа к чужой приватной странице"]}'),
        ('User1', '6', {'page': 7}, 200, '{"id":6,"author":{"id":2,"username":"User1"},'
                                         '"ancestry":[{"id":5,"title":"Page_4"},'
                                         '{"id":7,"title":"Page_6"},'
                                         '{"id":6,"title":"Page_5"}],"is_public":true,"title":"Page_5","parent":7}'),
        ('User1', '7', {'page': 8}, 200, '{"id":7,"author":{"id":2,"username":"User1"},'
                                         '"ancestry":[{"id":5,"title":"Page_4"},'
                                         '{"id":8,"title":"Page_7"},{"id":7,"title":"Page_6"}],'
                                         '"is_public":true,"title":"Page_6","parent":8}'),
        ('User2', '11', {'page': 5}, 200, '{"id":11,"author":{"id":3,"username":"User2"},'
                                          '"ancestry":[{"id":5,"title":"Page_4"},{"id":11,"title":"Page_10"}],'
                                          '"is_public":false,"title":"Page_10","parent":5}'),
        ('User2', '11', {'page': 7}, 200, '{"id":11,"author":{"id":3,"username":"User2"},'
                                          '"ancestry":[{"id":5,"title":"Page_4"},{"id":7,"title":"Page_6"},'
                                          '{"id":11,"title":"Page_10"}],"is_public":false,"title":"Page_10","parent":7}'),
        ('User2', '11', {'page': None}, 200, '{"id":11,"author":{"id":3,"username":"User2"},'
                                             '"ancestry":[{"id":11,"title":"Page_10"}],'
                                             '"is_public":false,"title":"Page_10","parent":null}'),
        ('User0', '1', {'page': 1}, 400, '{"page":["Нельзя ссылаться на себя или своего потомка"]}'),
        ('User0', '1', {'page': 4}, 400, '{"page":["Нельзя ссылаться на себя или своего потомка"]}'),
        ('User0', '1', {'page': 4, 'before_after': 'before'}, 400, '{"page":["Нельзя ссылаться на себя или своего потомка"]}'),
        ('User2', '11', {'page': 4, 'before_after': 'before'}, 400, '{"page":["Попытка доступа к чужой приватной странице"]}'),
        ('User2', '10', {'page': 8, 'before_after': 'after'}, 200, '{"id":10,"author":{"id":3,"username":"User2"},'
                                                                 '"ancestry":[{"id":5,"title":"Page_4"},'
                                                                 '{"id":10,"title":"Page_9"}],'
                                                                 '"is_public":false,"title":"Page_9","parent":5}'),
        ('User2', '10', {'page': 8, 'before_after': 'before'}, 200, '{"id":10,"author":{"id":3,"username":"User2"},'
                                                                 '"ancestry":[{"id":5,"title":"Page_4"},'
                                                                 '{"id":10,"title":"Page_9"}],'
                                                                 '"is_public":false,"title":"Page_9","parent":5}'),
        ('User0', '8', {'page': 2, 'before_after': 'before'}, 200, '{"id":8,"author":{"id":1,"username":"User0"},'
                                                                   '"ancestry":[{"id":1,"title":"Page_0"},'
                                                                   '{"id":8,"title":"Page_7"}],'
                                                                   '"is_public":false,"title":"Page_7","parent":1}'),
        ('User0', '6', {'page': 9, 'before_after': 'after'}, 403, '{"detail":"Доступ разрешен только автору."}'),
    ])
    def test_move_page(self, username, address, data, status, resp):
        if username:
            self.login(username)
        response = self.client.patch(self.url + address + "/move_page/", data, format='json')
        assert response.status_code == status
        if status == 200 and data.get('before_after', None):
            draw_pages_graph("move_page_"+address+"_to_"+data['before_after']+"_page_"+str(data['page']))
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '123', 401, '{"detail":"Учетные данные не были предоставлены."}', 0),
        ('User0', '6', 403, '{"detail":"Доступ разрешен только автору."}', 0),
        ('User0', '9', 403, '{"detail":"Доступ разрешен только автору."}', 0),
        ('User0', '666', 404, '{"detail":"Страница не найдена."}', 0),
        ('User0', '2', 200, '', 1),
        ('User0', '1', 200, '', 5),
    ])
    def test_soft_delete_page(self, username, address, status, resp, count):
        if username:
            self.login(username)
        response = self.client.delete(self.url + address+'/', format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp
        assert Page.objects.count() == self.count - count
        assert Page.objects.removed().count() == count

    @parameterized.expand([
        ('User0', '2', '2', 204, '', 1),
        ('User0', '4', '4', 204, '', 2),
        ('User0', '1', '3', 204, '', 1),
        ('User0', '1', '1', 204, '', 5),
        ('User0', '1', '4', 204, '', 2),
    ])
    def test_delete_page(self, username, address1, address2, status, resp, count):
        self.login(username)
        self.client.delete(self.url + address1 + '/', format='json')
        response = self.client.delete(self.url + address2 + '/', format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp
        assert Page.objects.all_pages().count() == self.count - count

    @parameterized.expand([
        (1, None, '1', 401, '{"detail":"Учетные данные не были предоставлены."}', 5),
        (1, 'User2', '1', 403, '{"detail":"Доступ разрешен только автору."}', 5),
        (1, 'User0', '1', 200, '{"id":1,"author":{"id":1,"username":"User0"},"'
                               'ancestry":[{"id":1,"title":"Page_0"}],'
                               '"is_public":false,"title":"Page_0","parent":null}', 4),
        (1, 'User0', '4', 200, '{"id":4,"author":{"id":1,"username":"User0"},'
                               '"ancestry":[{"id":1,"title":"Page_0"},{"id":4,"title":"Page_3"}],'
                               '"is_public":false,"title":"Page_3","parent":1}', 3),
        (1, 'User0', '11', 403, '{"detail":"Доступ разрешен только автору."}', 5),
        (1, 'User2', '11', 400, '{"detail":"Одна из родительских страниц удалена автором."}', 5),
        (1, 'User2', '121', 404, '{"detail":"Страница не найдена."}', 5),
        (11, 'User2', '11', 200, '{"id":11,"author":{"id":3,"username":"User2"},'
                                 '"ancestry":'
                                 '[{"id":1,"title":"Page_0"},{"id":4,"title":"Page_3"},{"id":11,"title":"Page_10"}],'
                                 '"is_public":false,"title":"Page_10","parent":4}', 0),
    ])
    def test_recovery_page(self, pk, username, address, status, resp, count):
        Page.objects.get(pk=pk).soft_delete()
        if username:
            self.login(username)
        response = self.client.put(self.url + address+'/', format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp
        assert Page.objects.count() == self.count - count
        assert Page.objects.removed().count() == count

    @parameterized.expand([
        (None, '/page-writer-list/', 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User1', '/page-writer-list/', 200, '[{"id":5,"title":"Page_4"},{"id":6,"title":"Page_5"},{"id":7,"title":"Page_6"}]'),
        ('User1', '/page-writer-list/?without_parent=True', 200, '[{"id":5,"title":"Page_4"}]'),
        ('User0', '/page-writer-list/?without_parent=True', 200, '[{"id":1,"title":"Page_0"}]'),
        ('User0', '/page-writer-list/?is_public=True', 200, '[{"id":8,"title":"Page_7"}]'),
        ('User2', '/page-writer-list/?is_public=True', 200, '[]'),
        ('User2', '/page-writer-list/?parent__author=User2', 400, '{"parent__author":["Выберите корректный вариант. Вашего варианта нет среди допустимых значений."]}'),
        ('User2', '/page-writer-list/?parent__author=5', 400, '{"parent__author":["Выберите корректный вариант. Вашего варианта нет среди допустимых значений."]}'),
        ('User2', '/page-writer-list/?parent__author=1', 200, '[{"id":11,"title":"Page_10"}]'),
        ('User2', '/page-writer-list/?in_other_space=True', 200, '[{"id":9,"title":"Page_8"},{"id":11,"title":"Page_10"}]'),
    ])
    def test_pages_list_writer(self, username, url, status, resp):
        if username:
            self.login(username)
        response = self.client.get(url, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (1, 'User0', '/page-writer-list/', 200, '[{"id":8,"title":"Page_7"}]'),
        (1, 'User0', '/page-writer-list/?is_removed=False', 200, '[{"id":8,"title":"Page_7"}]'),
        (1, 'User0', '/page-writer-list/?is_removed=True', 200, '[{"id":1,"title":"Page_0"},{"id":2,"title":"Page_1"},{"id":3,"title":"Page_2"},{"id":4,"title":"Page_3"}]'),
        (1, 'User0', '/page-writer-list/?is_removed=True&without_parent=True', 200, '[{"id":1,"title":"Page_0"}]'),
        (8, 'User0', '/page-writer-list/?is_removed=True&without_parent=True', 200, '[]'),
        (8, 'User0', '/page-writer-list/?is_removed=True&in_other_space=True', 200, '[{"id":8,"title":"Page_7"}]'),
        (5, 'User0', '/page-writer-list/?is_removed=True', 200, '[{"id":8,"title":"Page_7"}]'),
        (5, 'User0', '/page-writer-list/?is_public=False', 200, '[{"id":1,"title":"Page_0"},{"id":2,"title":"Page_1"},{"id":3,"title":"Page_2"},{"id":4,"title":"Page_3"}]'),
    ])
    def test_rubber_box_list(self, pk_del, username, url, status, resp):
        Page.objects.get(pk=pk_del).soft_delete()
        if username:
            self.login(username)
        response = self.client.get(url, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp