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
        #p1 = PageFactory.create(parent=page2, author=users[2], is_public=False, is_removed=True)  # P9
        p1 = PageFactory.create(parent=p1, author=users[2], is_public=False)  # P10

        PageFactory.create(parent=pages1[2], author=users[2])  # P11
        #draw_pages_graph("start_graph")

        RoadFactory.create_batch(3, page=pages2[1], author=u, parent=Road.objects.get(page=pages2[1], parent=None))
        RoadFactory.create_batch(3, page=pages2[0], author=u2, parent=Road.objects.get(page=pages2[0], parent=None), is_public=True)
        draw_roads_graph("start_graph")

    @parameterized.expand([
        (1, 5, 5),
        (9, 2, 2),
        (7, 1, 4)
    ])
    def test_soft_delete_page(self, pk, count, r_count):
        page = Page.objects.get(pk=pk)
        page.cut_page()
        page._change_remove_state()
        assert Page.objects.count() == self.count - count
        assert Page.objects.removed().count() == count
        assert Road.objects.filter(is_removed=False).count() == self.roads_count - r_count
        if pk>5:
            draw_pages_graph('delete_page_'+str(pk))

    @parameterized.expand([
        (1, 5, 5),
        (9, 2, 2),
        (7, 1, 4)
    ])
    def test_delete_page(self, pk, count, r_count):
        page = Page.objects.get(pk=pk)
        page.delete()
        assert Page.objects.count()+Page.objects.removed().count() == self.count - count
        assert Road.objects.count() == self.roads_count - r_count

    @parameterized.expand([
        (1, 1, 4, 4),
        (9, 9, 1, 1),
        (7, 7, 0, 3),
        (5, 10, 3, 9)
    ])
    def test_recovery_page(self, pk_d, pk_r, count, r_count):
        page = Page.objects.get(pk=pk_d)
        page._change_remove_state()
        page = Page.objects.removed().get(pk=pk_r)
        page._change_remove_state(False)
        assert Page.objects.count() == self.count - count
        assert Page.objects.removed().count() == count
        assert Road.objects.filter(is_removed=False).count() == self.roads_count - r_count