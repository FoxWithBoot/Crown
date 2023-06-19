from rest_framework.test import APITestCase
from parameterized import parameterized
import networkx as nx
from pyvis.network import Network

from ..models import Road
from user.models import User
from page.models import Page
from block.models import Block


def draw_roads_graph(filename):
    roads = list(Road.objects.all())
    nx_graph = nx.DiGraph()
    for i in roads:
        nx_graph.add_node(i.id, group=i.author.id, shape='circle' if i.is_public else 'box', label=str(i.id),
                          title=f'title: {i.title}\n'
                                f'public: {i.is_public}\n'
                                f'author: {i.author}')
    for i in roads:
        if i.parent:
            nx_graph.add_edge(i.parent.id, i.id)

    nt = Network(height='1000px', width='1000px', notebook=True, directed=True, layout=True)
    nt.from_nx(nx_graph)
    nt.toggle_physics(False)
    nt.show_buttons(filter_=['layout', 'physics'])
    nt.show(f'road/tests/graphics/{filename}.html')


class TestRoad(APITestCase):
    url = '/road/'
    count = 8

    @classmethod
    def setUpTestData(cls):
        u = User.objects.create_user(username="User0", password="123")
        u2 = User.objects.create_user(username="User1", password="123")
        u3 = User.objects.create_user(username="User2", password="123")

        p1 = Page.objects.create(title="Test Page 1", author=u, is_public=True)
        r1 = Road.objects.get(page=p1, parent=None)
        r2 = Road.objects.create(page=p1, parent=r1, title="Alt", author=u)
        r3 = Road.objects.create(page=p1, parent=r1, title="Alt2", author=u, is_public=True)
        r4 = Road.objects.create(page=p1, parent=r1, title="Alt3", author=u2)
        # r4.co_authors.add(u3)
        # r4.save()
        r5 = Road.objects.create(page=p1, parent=r1, title="Alt4", author=u2, is_public=True)
        r6 = Road.objects.create(page=p1, parent=r5, title="Alt5", author=u2, is_public=True)
        r7 = Road.objects.create(page=p1, parent=r6, title="Alt5", author=u3, is_public=True)

        b1_1 = Block.objects.get(road=r1, is_start=True)
        b1_1.type = "{'header':1}"
        b1_1.content = "Начало"
        b1_1.save()  # 1

        b1_2 = Block.objects.create(road=r1, content="Блок 2")  # 2
        b1_3 = Block.objects.create(road=r1, content="Блок 3")  # 3
        b1_4 = Block.objects.create(road=r1, content="Блок 4")  # 4
        b1_5 = Block.objects.create(road=r1, content="Блок 5")  # 5
        b1_6 = Block.objects.create(road=r1, content="Блок 6")  # 6
        b1_7 = Block.objects.create(road=r1, content="Блок 7")  # 7
        b1_1.next_blocks.add(b1_2)  # 1 -> 2
        b1_2.next_blocks.add(b1_3)  # 2 -> 3
        b1_3.next_blocks.add(b1_4)  # 3 -> 4
        b1_4.next_blocks.add(b1_5)  # 4 -> 5
        b1_5.next_blocks.add(b1_6)  # 5 -> 6
        b1_6.next_blocks.add(b1_7)  # 6 -> 7

        b2_1 = Block.objects.create(road=r2, content="Блок 2_1")  # 8
        b1_4.next_blocks.add(b2_1)  # 4 -> 8
        b2_1.next_blocks.add(b1_6)  # 8 -> 5

        b3_1 = Block.objects.create(road=r3, content="Блок 3_1")  # 9
        b3_2 = Block.objects.create(road=r3, content="Блок 3_2")  # 10
        b3_3 = Block.objects.create(road=r3, content="Блок 3_3")  # 11
        b3_4 = Block.objects.create(road=r3, content="Блок 3_4")  # 12
        b1_3.next_blocks.add(b3_1)  # 3 -> 9
        b3_1.next_blocks.add(b3_2)  # 9 -> 10
        b3_2.next_blocks.add(b3_3)  # 10 -> 11
        b3_3.next_blocks.add(b3_4)  # 11 -> 12

        b4_1 = Block.objects.create(road=r4, content="Блок 4_1", is_start=True)  # 13
        b4_2 = Block.objects.create(road=r4, content="Блок 4_2")  # 14
        b4_1.next_blocks.add(b4_2)  # 13 -> 14
        b4_2.next_blocks.add(b1_3)  # 14 -> 3

        b5_1 = Block.objects.create(road=r5, content="Блок 5_1", is_start=True)  # 15
        b5_2 = Block.objects.create(road=r5, content="Блок 5_2")  # 16
        b5_1.next_blocks.add(b1_4)  # 15 -> 4
        b1_6.next_blocks.add(b5_2)  # 6 -> 16

        b6_1 = Block.objects.create(road=r6, content="Блок 6_1", is_start=True)  # 17
        b6_2 = Block.objects.create(road=r6, content="Блок 6_2",)  # 18
        b6_3 = Block.objects.create(road=r6, content="Блок 6_3",)  # 19
        b6_1.next_blocks.add(b6_2)  # 17 -> 18
        b6_2.next_blocks.add(b5_1)  # 18 -> 15
        b5_2.next_blocks.add(b6_3)  # 16 -> 19

        b7_1 = Block.objects.create(road=r7, content="Блок 7_1",)  # 20
        b1_4.next_blocks.add(b7_1)  # 4 -> 20
        b7_1.next_blocks.add(b1_6)  # 20 -> 6

        Page.objects.create(author=u3)
        draw_roads_graph('roads_graph')

    def login(self, username):
        response = self.client.post('/user/token/', {'username': username, 'password': '123'}, format='json')
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    @parameterized.expand([
        (None, {}, 401, '{"detail":"Учетные данные не были предоставлены."}', 0),
        ('User0', {}, 400, '{"parent":["Обязательное поле."]}', 0),
        ('User0', {'parent': 1}, 201,
         '{"id":9,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":9,"title":"Дорога"}],"is_public":false,"title":"Дорога","parent":1}', 1),
        ('User0', {'parent': 2}, 201,
         '{"id":9,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":2,"title":"Alt"},{"id":9,"title":"Дорога"}],"is_public":false,"title":"Дорога","parent":2}', 1),
        ('User0', {'parent': 5}, 201,
         '{"id":9,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":5,"title":"Alt4"},{"id":9,"title":"Дорога"}],"is_public":false,"title":"Дорога","parent":5}', 1),
        ('User0', {'parent': 4}, 400, '{"parent":["Попытка доступа к чужой приватной ветке"]}', 0),
        ('User0', {'parent': 8}, 400, '{"parent":["Попытка доступа к чужой приватной ветке"]}', 0),
        ('User0', {'parent': 18}, 400, '{"parent":["Такой ветки не существует"]}', 0),
        ('User0', {'parent': -18}, 400, '{"parent":["Такой ветки не существует"]}', 0),
        ('User0', {'parent': 0}, 400, '{"parent":["Такой ветки не существует"]}', 0),
        ('User0', {'parent': 'rt'}, 400, '{"parent":["Значение “rt” должно быть целым числом."]}', 0),
        # --------------------------------------------------------------------------------------------------------------
        ('User0', {'parent': 1, 'title': 'Альтернатива'}, 201,
         '{"id":9,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":9,"title":"Альтернатива"}],"is_public":false,"title":"Альтернатива","parent":1}', 1),
        ('User0', {'parent': 1, 'title': 'Альтернатива'*100}, 400,
         '{"title":["Убедитесь, что это значение содержит не более 150 символов."]}', 0),
    ])
    def test_create_road(self, username, data, status, resp, c):
        if username:
            self.login(username)
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp
        assert Road.objects.count() == self.count + c

    @parameterized.expand([
        (None, '1', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"}],"is_public":true,"title":"Дорога","parent":null}'),
        (None, '3', 200, '{"id":3,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":3,"title":"Alt2"}],"is_public":true,"title":"Alt2","parent":1}'),
        (None, '2', 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User0', '1', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"}],"is_public":true,"title":"Дорога","parent":null}'),
        ('User0', '3', 200, '{"id":3,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":3,"title":"Alt2"}],"is_public":true,"title":"Alt2","parent":1}'),
        ('User0', '2', 200, '{"id":2,"author":{"id":1,"username":"User0"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":2,"title":"Alt"}],"is_public":false,"title":"Alt","parent":1}'),
        ('User0', '5', 200, '{"id":5,"author":{"id":2,"username":"User1"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":5,"title":"Alt4"}],"is_public":true,"title":"Alt4","parent":1}'),
        ('User0', '4', 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', '40', 404, '{"detail":"Страница не найдена."}'),
        ('User0', '7', 200, '{"id":7,"author":{"id":3,"username":"User2"},"page":{"id":1,"title":"Test Page 1"},"ancestry":[{"id":1,"title":"Дорога"},{"id":5,"title":"Alt4"},{"id":6,"title":"Alt5"},{"id":7,"title":"Alt5"}],"is_public":true,"title":"Alt5","parent":6}'),
    ])
    def test_get_road_info(self, username, road_id, status, resp):
        if username:
            self.login(username)
        response = self.client.get(self.url+road_id+'/', format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '8/roads_tree/', 401, '{"detail":"Учетные данные не были предоставлены."}'),
        (None, '2/roads_tree/', 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User0', '8/roads_tree/', 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', '4/roads_tree/', 403, '{"detail":"Доступ разрешен только автору."}'),
        (None, '3/roads_tree/', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]}]}'),
        (None, '3/roads_tree/?other_author=2', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]},{"id":5,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt4","is_public":true,"subroads":[{"id":6,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt5","is_public":true,"subroads":[]}]}]}'),
        (None, '3/roads_tree/?other_author=3', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]}]}'),
        (None, '3/roads_tree/?other_author=2&other_author=3', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]},{"id":5,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt4","is_public":true,"subroads":[{"id":6,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt5","is_public":true,"subroads":[{"id":7,"author":{"id":3,"username":"User2"},"page":1,"title":"Alt5","is_public":true,"subroads":[]}]}]}]}'),
        ('User1', '4/roads_tree/', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]},{"id":4,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt3","is_public":false,"subroads":[]},{"id":5,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt4","is_public":true,"subroads":[{"id":6,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt5","is_public":true,"subroads":[]}]}]}'),
        ('User0', '4/roads_tree/', 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', '3/roads_tree/', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":2,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt","is_public":false,"subroads":[]},{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]}]}'),
        ('User2', '1/roads_tree/', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]}]}'),
        ('User2', '1/roads_tree/?other_author=2', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]},{"id":5,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt4","is_public":true,"subroads":[{"id":6,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt5","is_public":true,"subroads":[{"id":7,"author":{"id":3,"username":"User2"},"page":1,"title":"Alt5","is_public":true,"subroads":[]}]}]}]}'),
        ('User2', '1/roads_tree/?other_author=2rt', 400, '{"parent":["Некорректный id автора"]}'),
        ('User2', '1/roads_tree/?other_author=22', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]}]}'),
        ('User2', '8/roads_tree/', 200, '{"id":8,"author":{"id":3,"username":"User2"},"page":2,"title":"Дорога","is_public":false,"subroads":[]}'),
    ])
    def test_get_roads_tree(self, username, address, status, resp):
        if username:
            self.login(username)
        response = self.client.get(self.url + address, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '/page/1/roads_tree/', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]},{"id":5,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt4","is_public":true,"subroads":[{"id":6,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt5","is_public":true,"subroads":[{"id":7,"author":{"id":3,"username":"User2"},"page":1,"title":"Alt5","is_public":true,"subroads":[]}]}]}]}'),
        (None, '/page/2/roads_tree/', 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User0', '/page/2/roads_tree/', 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', '/page/1/roads_tree/', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":2,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt","is_public":false,"subroads":[]},{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]},{"id":5,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt4","is_public":true,"subroads":[{"id":6,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt5","is_public":true,"subroads":[{"id":7,"author":{"id":3,"username":"User2"},"page":1,"title":"Alt5","is_public":true,"subroads":[]}]}]}]}'),
        ('User2', '/page/1/roads_tree/', 200, '{"id":1,"author":{"id":1,"username":"User0"},"page":1,"title":"Дорога","is_public":true,"subroads":[{"id":3,"author":{"id":1,"username":"User0"},"page":1,"title":"Alt2","is_public":true,"subroads":[]},{"id":5,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt4","is_public":true,"subroads":[{"id":6,"author":{"id":2,"username":"User1"},"page":1,"title":"Alt5","is_public":true,"subroads":[{"id":7,"author":{"id":3,"username":"User2"},"page":1,"title":"Alt5","is_public":true,"subroads":[]}]}]}]}'),
    ])
    def test_get_full_roads_tree(self, username, address, status, resp):
        if username:
            self.login(username)
        response = self.client.get(address, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp