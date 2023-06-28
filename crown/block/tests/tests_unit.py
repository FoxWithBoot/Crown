import networkx as nx
from parameterized import parameterized
from pyvis.network import Network
from rest_framework.test import APITestCase

from block.models import Block
from user.models import User
from page.models import Page
from road.models import Road

from block.controller import read_road, create_block, update_block_content, delete_block, merge_roads


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
        #r4.co_authors.add(u3)
        #r4.save()
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

    @parameterized.expand([
        (1, [1, 2, 3, 4, 5, 6, 7]),
        (2, [1, 2, 3, 4, 8, 6, 7]),
        (3, [1, 2, 3, 9, 10, 11, 12]),
        (4, [13, 14, 3, 4, 5, 6, 7]),
        (5, [15, 4, 5, 6, 16]),
        (6, [17, 18, 15, 4, 5, 6, 16, 19]),
        (7, [17, 18, 15, 4, 20, 6, 16, 19]),
        (8, [21]),
    ])
    def test_read_road(self, rd, bls):
        road = Road.objects.get(pk=rd)
        blocks = read_road(road)
        assert len(blocks) == len(bls)
        assert [i.id for i in blocks] == bls

    @parameterized.expand([
        (1, {'block': 1, 'before_after': 'before'}, [22, 1, 2, 3, 4, 5, 6, 7]),
        (1, {'block': 7, 'before_after': 'after'}, [1, 2, 3, 4, 5, 6, 7, 22]),
        (1, {'block': 3, 'before_after': 'after'}, [1, 2, 3, 22, 4, 5, 6, 7]),
        (1, {'block': 4, 'before_after': 'before'}, [1, 2, 3, 22, 4, 5, 6, 7]),
        (2, {'block': 3, 'before_after': 'after'}, [1, 2, 3, 22, 4, 8, 6, 7]),
        (2, {'block': 4, 'before_after': 'before'}, [1, 2, 3, 22, 4, 8, 6, 7]),
        (4, {'block': 3, 'before_after': 'after'}, [13, 14, 3, 22, 4, 5, 6, 7]),
        (4, {'block': 4, 'before_after': 'before'}, [13, 14, 3, 22, 4, 5, 6, 7]),
        (7, {'block': 15, 'before_after': 'before'}, [17, 18, 22, 15, 4, 20, 6, 16, 19]),
        (7, {'block': 18, 'before_after': 'after'}, [17, 18, 22, 15, 4, 20, 6, 16, 19]),
    ])
    def test_create_block(self, road, where, fin_line):
        road = Road.objects.get(pk=road)
        line = read_road(road)
        where['block'] = Block.objects.get(pk=where['block'])
        create_block(road=road, content='', where=where, line=line)
        new_line = read_road(road)
        assert len(new_line) == len(fin_line)
        assert [i.id for i in new_line] == fin_line
        draw_blocks_graph(f'create_new_block_{road}_{where["before_after"]}_{where["block"].id}')

    @parameterized.expand([
        (4, 4, [13, 14, 3, 22, 5, 6, 7]),
        (4, 6, [13, 14, 3, 4, 5, 22, 7]),
        (5, 4, [15, 22, 5, 6, 16]),
        (5, 6, [15, 4, 5, 22, 16]),
        (6, 4, [17, 18, 15, 22, 5, 6, 16, 19]),
        (6, 6, [17, 18, 15, 4, 5, 22, 16, 19]),
        (6, 15, [17, 18, 22, 4, 5, 6, 16, 19]),
    ])
    def test_update_block(self, road, block, fin_line):
        block = Block.objects.get(pk=block)
        road = Road.objects.get(pk=road)
        line = read_road(road)
        update_block_content(block, road, line, 'content')
        new_line = read_road(road)
        assert len(new_line) == len(fin_line)
        assert [i.id for i in new_line] == fin_line
        draw_blocks_graph(f'update_block_{block.id}_on_road_{road.id}')

    @parameterized.expand([
        (1, 1, -1, [2, 3, 4, 5, 6, 7]),
        (1, 2, -1, [1, 3, 4, 5, 6, 7]),
        (1, 3, 1, [1, 2, 4, 5, 6, 7]),
        (4, 3, 0, [13, 14, 4, 5, 6, 7]),
        (4, 14, -1, [13, 3, 4, 5, 6, 7]),
        (2, 8, 1, [1, 2, 3, 22, 23, 7]),
        (5, 15, 1, [23, 5, 6, 16]),
        (7, 20, 1, [17, 18, 15, 22, 23, 16, 19]),
        #  --------------------------------------
        (7, 4, 0, [17, 18, 15, 20, 6, 16, 19]),
        (6, 4, 3, [17, 18, 23, 24, 6, 16, 19]),
        (5, 4, 1, [15, 5, 6, 16]),
        (2, 4, 0, [1, 2, 3, 8, 6, 7]),
        (1, 4, 1, [1, 2, 3, 5, 6, 7]),
        #  --------------------------------------
        (7, 6, 0, [17, 18, 15, 4, 20, 16, 19]),
        (6, 6, 3, [17, 18, 15, 4, 23, 24, 19]),
        (5, 6, 1, [15, 4, 5, 16]),
        (2, 6, 0, [1, 2, 3, 4, 8, 7]),
        (1, 6, 1, [1, 2, 3, 4, 5, 7]),
    ])
    def test_delete_block(self, rd, bl, c, fin_line):
        block = Block.objects.get(pk=bl)
        road = Road.objects.get(pk=rd)
        line = read_road(road)
        delete_block(road, line, block)
        new_line = read_road(road)
        assert Block.objects.count() == self.count + c
        assert len(new_line) == len(fin_line)
        assert [i.id for i in new_line] == fin_line
        draw_blocks_graph(f'delete_block_{bl}_on_road_{rd}')

    @parameterized.expand([
        (1, 2, [1, 2, 3, 4, 8, 6, 7], 1, 1),
        (1, 3, [1, 2, 3, 9, 10, 11, 12], 5, 11),
        (1, 5, [15, 4, 5, 6, 16], 3, 10),
        (1, 6, [17, 18, 15, 4, 5, 6, 16, 19], 4, 10),
        (1, 7, [17, 18, 15, 4, 20, 6, 16, 19], 5, 11),
        (5, 6, [17, 18, 15, 4, 5, 6, 16, 19], 1, 0),
        (5, 7, [17, 18, 15, 4, 20, 6, 16, 19], 2, 0),
        (6, 7, [17, 18, 15, 4, 20, 6, 16, 19], 1, 0),
    ])
    def test_merge_roads(self, r1, r2, bls, cr, cb):
        road1 = Road.objects.get(pk=r1)
        road2 = Road.objects.get(pk=r2)
        merge_roads(road1, road2)
        blocks = read_road(Road.objects.get(pk=r1))
        assert len(blocks) == len(bls)
        assert [i.id for i in blocks] == bls
        assert Road.objects.count() == 8 - cr
        assert Block.objects.count() == self.count - cb
        draw_blocks_graph(f'merge_road_{r1}_with_{r2}')

