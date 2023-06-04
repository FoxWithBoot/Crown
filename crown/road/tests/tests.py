from rest_framework.test import APITestCase
from parameterized import parameterized
import networkx as nx
from pyvis.network import Network

from road.models import Road


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