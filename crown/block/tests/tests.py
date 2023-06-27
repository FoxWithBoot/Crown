import networkx as nx
from parameterized import parameterized
from pyvis.network import Network
from rest_framework.test import APITestCase

from block.models import Block
from user.models import User
from page.models import Page
from road.models import Road


def draw_blocks_graph(filename):
    blocks = list(Block.objects.all().order_by('road_id'))
    blocks = Block.objects.all().order_by('road_id')
    sv = list(Block.objects.all().values('id', 'next_blocks'))
    nx_graph = nx.DiGraph()
    for i in blocks:
        nx_graph.add_node(i.id, group=i.road_id, shape='circle' if i.road.is_public else 'box', label=str(i.id),
                          title=f'content:{i.content}\n'
                                f'road:{i.road}')

    for i in sv:
        if i.get('next_blocks', None):
            nx_graph.add_edge(i.get('id'), i.get('next_blocks'))

    nt = Network(height='1000px', width='1000px', notebook=True, directed=True, layout=True)
    nt.from_nx(nx_graph)
    nt.toggle_physics(False)
    nt.show_buttons(filter_=['layout', 'physics'])
    nt.show(f'block/tests/graphics/{filename}.html')


class TestBlock(APITestCase):
    #url = '/api/v2.2.1/block/'
    count = 21

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
        r5 = Road.objects.create(page=p1, parent=r1, title="Alt4", author=u2, is_public=True)
        r6 = Road.objects.create(page=p1, parent=r5, title="Alt5", author=u2, is_public=True)
        r7 = Road.objects.create(page=p1, parent=r6, title="Alt5", author=u3, is_public=True)

        b1_1 = Block.objects.get(road=r1, is_start=True)
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
        b6_2 = Block.objects.create(road=r6, content="Блок 6_2")  # 18
        b6_3 = Block.objects.create(road=r6, content="Блок 6_3")  # 19
        b6_1.next_blocks.add(b6_2)  # 17 -> 18
        b6_2.next_blocks.add(b5_1)  # 18 -> 15
        b5_2.next_blocks.add(b6_3)  # 16 -> 19

        b7_1 = Block.objects.create(road=r7, content="Блок 7_1")  # 20
        b1_4.next_blocks.add(b7_1)  # 4 -> 20
        b7_1.next_blocks.add(b1_6)  # 20 -> 6

        Page.objects.create(author=u3)
        draw_blocks_graph('block_graph')

    def login(self, username):
        response = self.client.post('/user/token/', {'username': username, 'password': '123'}, format='json')
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    @parameterized.expand([
        ('User1', '/road/2/blocks/', 403, '{"detail":"Доступ разрешен только автору."}'),
        ('User0', '/road/4/blocks/', 403, '{"detail":"Доступ разрешен только автору."}'),
        (None, '/road/5/blocks/', 200, '[{"id":15,"content":"Блок 5_1"},{"id":4,"content":"Блок 4"},{"id":5,"content":"Блок 5"},{"id":6,"content":"Блок 6"},{"id":16,"content":"Блок 5_2"}]'),
        (None, '/road/8/blocks/', 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User2', '/road/8/blocks/', 200, '[{"id":21,"content":"<p>Давай начнем писать;)</p>"}]'),
        ('User2', '/road/101/blocks/', 404, '{"detail":"Страница не найдена."}'),
    ])
    def test_get_blocks_of_road(self, username, address, status, resp):
        if username:
            self.login(username)
        response = self.client.get(address, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

    @parameterized.expand([
        (None, '/road/1/blocks/', {}, 401, '{"detail":"Учетные данные не были предоставлены."}'),
        ('User0', '/road/1/blocks/', {'where': {'before_after': 'before', 'block': 1}}, 201, '{"id":22,"content":""}'),
        ('User0', '/road/1/blocks/', {'content': 'Заголовок', 'where': {'before_after': 'before', 'block': 1}}, 201,
         '{"id":22,"content":"Заголовок"}'),
        ('User0', '/road/1/blocks/', {'content': 'Заголовок', 'where': {'before_after': 'before', 'block': 101}}, 400,
         '{"where":{"block":["Такого блока не существует."]}}'),
        ('User0', '/road/1/blocks/', {'content': 'Заголовок', 'where': {'before_after': 'beforeRR', 'block': 1}}, 400,
         '{"where":{"before_after":["Значения beforeRR нет среди допустимых вариантов."]}}'),
        ('User0', '/road/1/blocks/', {'content': 'Заголовок'}, 400, '{"where":["Обязательное поле."]}'),
        ('User0', '/road/4/blocks/', {'content': 'Заголовок', 'where': {'before_after': 'before', 'block': 4}}, 403,
         '{"detail":"Доступ разрешен только автору."}'),
        ('User0', '/road/4/blocks/', {'content': 'Заголовок', 'where': {'before_after': 'before', 'block': 1}}, 403,
         '{"detail":"Доступ разрешен только автору."}'),
    ])
    def test_create_block(self, username, address, data, status, resp):
        if username:
            self.login(username)
        response = self.client.post(address, data, format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp

