import networkx as nx
from parameterized import parameterized
from pyvis.network import Network
from rest_framework.test import APITestCase

from block.models import Block
from user.models import User
from page.models import Page
from road.models import Road

from block.controller import read_road, create_block, update_block, delete_block, merge_roads

from block.models import BlocksOnRoad


# def draw_blocks_graph(filename):
#     blocks = list(Block.objects.all().order_by('road_id'))
#     blocks = Block.objects.all().order_by('road_id')
#     sv = list(Block.objects.all().values('id', 'next_blocks'))
#     nx_graph = nx.DiGraph()
#     for i in blocks:
#         nx_graph.add_node(i.id, group=i.road_id, shape='circle' if i.road.is_public else 'box', label=str(i.id),
#                           title=f'content:{i.content}\n'
#                                 f'road:{i.road}')
#
#     for i in sv:
#         if i.get('next_blocks', None):
#             nx_graph.add_edge(i.get('id'), i.get('next_blocks'))
#
#     nt = Network(height='1000px', width='1000px', notebook=True, directed=True, layout=True)
#     nt.from_nx(nx_graph)
#     nt.toggle_physics(False)
#     nt.show_buttons(filter_=['layout', 'physics'])
#     nt.show(f'block/tests/graphics/{filename}.html')


def draw_blocks_graph(filename):
    roads = list(Road.objects.all().order_by('id'))
    nx_graph = nx.DiGraph()

    for r in roads:
        connects = list(BlocksOnRoad.objects.filter(road=r).order_by('index'))
        for b in connects:
            nx_graph.add_node(b.block.id, group=b.road.id, label=str(b.block.id))
    for r in roads:
        connects = list(BlocksOnRoad.objects.filter(road=r).order_by('index'))
        for c in range(len(connects)-1):
            nx_graph.add_edge(connects[c].block.id, connects[c+1].block.id)

    nt = Network(height='1000px', width='1000px', notebook=True, directed=True, layout=True)
    nt.from_nx(nx_graph)
    nt.toggle_physics(False)
    nt.show_buttons(filter_=['layout', 'physics'])
    nt.show(f'block/tests/graphics/{filename}.html')


def write_lines(filename):
    with open(f'block/tests/graphics/{filename}.txt', 'w') as f:
        roads = Road.objects.all()
        for r in roads:
            line = read_road(r)
            print(r.id, end=' ')
            f.write(f'{r.id}: ')
            for b in line:
                t = BlocksOnRoad.objects.filter(road=r, block=b).values_list('block__id', 'index')
                print(t, end=' ')
                f.write(f'{t}, ')
            print()
            f.write('\n')
    f.close()

class TestBlock(APITestCase):
    count = 21
    cc = 7+7+7+7+5+8+8+1

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

        b1_1 = BlocksOnRoad.objects.get(road=r1).block
        #b1_1 = Block.objects.get(road=r1, is_start=True)
        b1_1.content = "Начало"
        b1_1.save()  # 1

        b1_2 = Block.objects.create(content="Блок 2")  # 2
        BlocksOnRoad.objects.create(road=r1, block=b1_2, index=1, original_road=True)
        b1_3 = Block.objects.create(content="Блок 3")  # 3
        BlocksOnRoad.objects.create(road=r1, block=b1_3, index=2, original_road=True)
        b1_4 = Block.objects.create(content="Блок 4")  # 4
        BlocksOnRoad.objects.create(road=r1, block=b1_4, index=3, original_road=True)
        b1_5 = Block.objects.create(content="Блок 5")  # 5
        BlocksOnRoad.objects.create(road=r1, block=b1_5, index=4, original_road=True)
        b1_6 = Block.objects.create(content="Блок 6")  # 6
        BlocksOnRoad.objects.create(road=r1, block=b1_6, index=5, original_road=True)
        b1_7 = Block.objects.create(content="Блок 7")  # 7
        BlocksOnRoad.objects.create(road=r1, block=b1_7, index=6, original_road=True)
        line_1 = [b1_1, b1_2, b1_3, b1_4, b1_5, b1_6, b1_7]
        # b1_1.next_blocks.add(b1_2)  # 1 -> 2
        # b1_2.next_blocks.add(b1_3)  # 2 -> 3
        # b1_3.next_blocks.add(b1_4)  # 3 -> 4
        # b1_4.next_blocks.add(b1_5)  # 4 -> 5
        # b1_5.next_blocks.add(b1_6)  # 5 -> 6
        # b1_6.next_blocks.add(b1_7)  # 6 -> 7

        b2_1 = Block.objects.create(content="Блок 2_1")  # 8
        for b1 in line_1:
            BlocksOnRoad.objects.create(road=r2, block=b1, index=line_1.index(b1))
        BlocksOnRoad.objects.filter(road=r2, block__id=5).delete()
        BlocksOnRoad.objects.create(road=r2, block=b2_1, original_road=True, index=line_1.index(b1_5))
        # b1_4.next_blocks.add(b2_1)  # 4 -> 8
        # b2_1.next_blocks.add(b1_6)  # 8 -> 5
        for b1 in line_1[:3]:
            BlocksOnRoad.objects.create(road=r3, block=b1, index=line_1.index(b1))
        b3_1 = Block.objects.create(content="Блок 3_1")  # 9
        BlocksOnRoad.objects.create(road=r3, block=b3_1, original_road=True, index=3)
        b3_2 = Block.objects.create(content="Блок 3_2")  # 10
        BlocksOnRoad.objects.create(road=r3, block=b3_2, original_road=True, index=4)
        b3_3 = Block.objects.create(content="Блок 3_3")  # 11
        BlocksOnRoad.objects.create(road=r3, block=b3_3, original_road=True, index=5)
        b3_4 = Block.objects.create(content="Блок 3_4")  # 12
        BlocksOnRoad.objects.create(road=r3, block=b3_4, original_road=True, index=6)
        # b1_3.next_blocks.add(b3_1)  # 3 -> 9
        # b3_1.next_blocks.add(b3_2)  # 9 -> 10
        # b3_2.next_blocks.add(b3_3)  # 10 -> 11
        # b3_3.next_blocks.add(b3_4)  # 11 -> 12

        b4_1 = Block.objects.create(content="Блок 4_1")  # 13
        BlocksOnRoad.objects.create(road=r4, block=b4_1, original_road=True, index=0)
        b4_2 = Block.objects.create(content="Блок 4_2")  # 14
        BlocksOnRoad.objects.create(road=r4, block=b4_2, original_road=True, index=1)
        i = 1
        for b1 in line_1[2:]:
            i += 1
            BlocksOnRoad.objects.create(road=r4, block=b1, index=i)
        # b4_1.next_blocks.add(b4_2)  # 13 -> 14
        # b4_2.next_blocks.add(b1_3)  # 14 -> 3

        b5_1 = Block.objects.create(content="Блок 5_1")  # 15
        BlocksOnRoad.objects.create(road=r5, block=b5_1, original_road=True, index=0)
        b5_2 = Block.objects.create(content="Блок 5_2")  # 16
        BlocksOnRoad.objects.create(road=r5, block=b1_4, index=1)
        BlocksOnRoad.objects.create(road=r5, block=b1_5, index=2)
        BlocksOnRoad.objects.create(road=r5, block=b1_6, index=3)
        BlocksOnRoad.objects.create(road=r5, block=b5_2, original_road=True, index=4)
        # b5_1.next_blocks.add(b1_4)  # 15 -> 4
        # b1_6.next_blocks.add(b5_2)  # 6 -> 16

        b6_1 = Block.objects.create(content="Блок 6_1")  # 17
        BlocksOnRoad.objects.create(road=r6, block=b6_1, original_road=True, index=0)
        b6_2 = Block.objects.create(content="Блок 6_2")  # 18
        BlocksOnRoad.objects.create(road=r6, block=b6_2, original_road=True, index=1)
        b6_3 = Block.objects.create(content="Блок 6_3")  # 19
        BlocksOnRoad.objects.create(road=r6, block=b5_1, index=2)
        BlocksOnRoad.objects.create(road=r6, block=b1_4, index=3)
        BlocksOnRoad.objects.create(road=r6, block=b1_5, index=4)
        BlocksOnRoad.objects.create(road=r6, block=b1_6, index=5)
        BlocksOnRoad.objects.create(road=r6, block=b5_2, index=6)
        BlocksOnRoad.objects.create(road=r6, block=b6_3, original_road=True, index=7)
        line_6 = [b6_1, b6_2, b5_1, b1_4, b1_5, b1_6, b5_2, b6_3]
        # b6_1.next_blocks.add(b6_2)  # 17 -> 18
        # b6_2.next_blocks.add(b5_1)  # 18 -> 15
        # b5_2.next_blocks.add(b6_3)  # 16 -> 19

        b7_1 = Block.objects.create(content="Блок 7_1")  # 20
        line_7_ = [b6_1, b6_2, b5_1, b1_4, b7_1, b1_6, b5_2, b6_3]
        i = -1
        for b7 in line_7_:
            i += 1
            BlocksOnRoad.objects.create(road=r7, block=b7, index=i)
        BlocksOnRoad.objects.filter(road=r7, block=b7_1).update(original_road=True)
        # b1_4.next_blocks.add(b7_1)  # 4 -> 20
        # b7_1.next_blocks.add(b1_6)  # 20 -> 6

        Page.objects.create(author=u3)
        draw_blocks_graph('block_graph_2')

    @parameterized.expand([
        (1, [1, 2, 3, 4, 5, 6, 7], 0),
        (2, [1, 2, 3, 4, 8, 6, 7], 0),
        (3, [1, 2, 3, 9, 10, 11, 12], 0),
        (4, [13, 14, 3, 4, 5, 6, 7], 0),
        (5, [15, 4, 5, 6, 16], 0),
        (6, [17, 18, 15, 4, 5, 6, 16, 19], 0),
        (7, [17, 18, 15, 4, 20, 6, 16, 19], 0),
        (8, [21], 0),
    ])
    def test_read_road(self, rd, bls, cc):
        road = Road.objects.get(pk=rd)
        blocks = read_road(road)
        assert len(blocks) == len(bls)
        assert [i.id for i in blocks] == bls
        assert BlocksOnRoad.objects.count() == self.cc + cc

    @parameterized.expand([
        (1, {'block': 1, 'before_after': 'before'}, [22, 1, 2, 3, 4, 5, 6, 7], 3),
        (1, {'block': 7, 'before_after': 'after'}, [1, 2, 3, 4, 5, 6, 7, 22], 3),
        (1, {'block': 3, 'before_after': 'after'}, [1, 2, 3, 22, 4, 5, 6, 7], 3),
        (1, {'block': 4, 'before_after': 'before'}, [1, 2, 3, 22, 4, 5, 6, 7], 3),
        (2, {'block': 3, 'before_after': 'after'}, [1, 2, 3, 22, 4, 8, 6, 7], 1),
        (2, {'block': 4, 'before_after': 'before'}, [1, 2, 3, 22, 4, 8, 6, 7], 1),
        (4, {'block': 3, 'before_after': 'after'}, [13, 14, 3, 22, 4, 5, 6, 7], 1),
        (4, {'block': 4, 'before_after': 'before'}, [13, 14, 3, 22, 4, 5, 6, 7], 1),
        (7, {'block': 15, 'before_after': 'before'}, [17, 18, 22, 15, 4, 20, 6, 16, 19], 1),
        (7, {'block': 18, 'before_after': 'after'}, [17, 18, 22, 15, 4, 20, 6, 16, 19], 1),
    ])
    def test_create_block(self, road, where, fin_line, cc):
        road = Road.objects.get(pk=road)
        where['block'] = Block.objects.get(pk=where['block'])
        create_block(road=road, content='', where=where)
        new_line = read_road(road)
        assert len(new_line) == len(fin_line)
        assert [i.id for i in new_line] == fin_line
        assert BlocksOnRoad.objects.count() == self.cc + cc
        write_lines(f'create_new_block2_{road}_{where["before_after"]}_{where["block"].id}')
        for r in Road.objects.all():
            i = 0
            for c in BlocksOnRoad.objects.filter(road=r).order_by('index'):
                assert c.index == i
                i += 1

    @parameterized.expand([
        (4, 4, [13, 14, 3, 22, 5, 6, 7], 0),
        (4, 6, [13, 14, 3, 4, 5, 22, 7], 0),
        (5, 4, [15, 22, 5, 6, 16], 0),
        (5, 6, [15, 4, 5, 22, 16], 0),
        (6, 4, [17, 18, 15, 22, 5, 6, 16, 19], 0),
        (6, 6, [17, 18, 15, 4, 5, 22, 16, 19], 0),
        (6, 15, [17, 18, 22, 4, 5, 6, 16, 19], 0),
        (1, 1, [1, 2, 3, 4, 5, 6, 7], 0)
    ])
    def test_update_block(self, road, block, fin_line, cc):
        block = Block.objects.get(pk=block)
        road = Road.objects.get(pk=road)
        update_block(block, road, 'content')
        new_line = read_road(road)
        assert len(new_line) == len(fin_line)
        assert [i.id for i in new_line] == fin_line
        assert BlocksOnRoad.objects.count() == self.cc + cc
        for r in Road.objects.all():
            i = 0
            for c in BlocksOnRoad.objects.filter(road=r).order_by('index'):
                assert c.index == i
                i += 1

    @parameterized.expand([
        (1, 1, -1, [2, 3, 4, 5, 6, 7], -3),
        (1, 2, -1, [1, 3, 4, 5, 6, 7], -3),
        (1, 3, -1, [1, 2, 4, 5, 6, 7], -4),
        (4, 3, 0, [13, 14, 4, 5, 6, 7], -1),
        (4, 14, -1, [13, 3, 4, 5, 6, 7], -1),
        (2, 8, -1, [1, 2, 3, 4, 6, 7], -1),
        (5, 15, -1, [4, 5, 6, 16], -3),
        (7, 20, -1, [17, 18, 15, 4, 6, 16, 19], -1),
        #  --------------------------------------
        (7, 4, 0, [17, 18, 15, 20, 6, 16, 19], -1),
        (6, 4, 0, [17, 18, 15, 5, 6, 16, 19], -2),
        (5, 4, 0, [15, 5, 6, 16], -3),
        (2, 4, 0, [1, 2, 3, 8, 6, 7], -1),
        (1, 4, -1, [1, 2, 3, 5, 6, 7], -6),
        #  --------------------------------------
        (7, 6, 0, [17, 18, 15, 4, 20, 16, 19], -1),
        (6, 6, 0, [17, 18, 15, 4, 5, 16, 19], -2),
        (5, 6, 0, [15, 4, 5, 16], -3),
        (2, 6, 0, [1, 2, 3, 4, 8, 7], -1),
        (1, 6, -1, [1, 2, 3, 4, 5, 7], -6),
    ])
    def test_delete_block(self, rd, bl, c, fin_line, cc):
        block = Block.objects.get(pk=bl)
        road = Road.objects.get(pk=rd)
        delete_block(road, block)
        new_line = read_road(road)
        assert Block.objects.count() == self.count + c
        assert len(new_line) == len(fin_line)
        assert [i.id for i in new_line] == fin_line
        assert BlocksOnRoad.objects.count() == self.cc + cc
        for r in Road.objects.all():
            i = 0
            for c in BlocksOnRoad.objects.filter(road=r).order_by('index'):
                assert c.index == i
                i += 1

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
        print('blocks', blocks)
        assert len(blocks) == len(bls)
        assert [i.id for i in blocks] == bls
        write_lines(f'merge2_road_{r1}_with_{r2}')
        assert Road.objects.count() == 8 - cr
        assert Block.objects.count() == self.count - cb
        for r in Road.objects.all():
            i = 0
            for c in BlocksOnRoad.objects.filter(road=r).order_by('index'):
                assert c.index == i
                i += 1
        #draw_blocks_graph(f'merge2_road_{r1}_with_{r2}')

