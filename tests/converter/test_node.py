import pytest

from pygraphviz import AGraph

from blockgraph.converter.node import Node, Region

def _make_agraphs():
    a1 = AGraph(name='ag', strict=False, directed=True)
    a2 = a1.add_subgraph(name='subg')
    return a1, a2

@pytest.fixture
def regions():
    a1, a2 = _make_agraphs()
    r1 = Region(a1)
    r2 = Region(a2, r1)
    return r1, r2

def test_create_node():
    n1 = Node('node1')
    assert n1.name == 'node1'

def test_create_region():
    a1, _ = _make_agraphs()
    r1 = Region(a1)
    assert r1.agraph == a1
    assert r1.name == 'ag'
    assert len(r1.nodes) == 0

def test_in_region(regions):
    r1, r2 = regions
    assert r1.in_region is None
    assert r2.in_region == r1

def test_create_region_with_node(regions):
    r1, _ = regions
    n1 = Node('node1', in_region=r1)
    assert n1.in_region == r1

def test_add_node_to_region(regions):
    r1, r2 = regions
    n1 = Node('node1')
    n2 = Node('node2')
    n1.in_region = r1
    n2.in_region = r1
    assert n1 in r1.nodes and n2 in r1.nodes and r2 in r1.nodes
    assert n1.in_region == r1 and n2.in_region == r1 and r2.in_region == r1
    assert len(r1.nodes) == 3

def test_add_edge():
    a = Node('a')
    b = Node('b')
    c = Node('c')
    a.add_edge(b)
    a.add_edge(c)
    assert len(a.prev) == 0 and len(a.next) == 2
    assert b in a.next and c in a.next
    assert len(b.prev) == 1 and len(b.next) == 0
    assert a in b.prev
    assert len(c.prev) == 1 and len(c.next) == 0
    assert a in c.prev

def test_nodes(regions):
    r1, r2 = regions
    n2 = Node('node2', in_region=r1)
    n1 = Node('node1', in_region=r1)
    r1_nodes = r1.nodes
    assert n1 in r1_nodes
    assert n2 in r1_nodes
    assert r2 in r1_nodes

def test_nodes_map(regions):
    r1, r2 = regions
    n2 = Node('node2', in_region=r1)
    n1 = Node('node1', in_region=r1)
    r1_nodes = r1.nodes_map
    assert len(r1_nodes) == 3
    assert r1_nodes['subg'] == r2
    assert r1_nodes['node1'] == n1
    assert r1_nodes['node2'] == n2

def test_nodes_iter(regions):
    r1, r2 = regions
    n2 = Node('z_node2', in_region=r1)
    n1 = Node('z_node1', in_region=r1)
    r1_nodes = list(r1.nodes_iter)
    assert len(r1_nodes) == 3
    assert r1_nodes[0] == n1
    assert r1_nodes[1] == n2
    assert r1_nodes[2] == r2

def test_nodes_sorted(regions):
    r1, r2 = regions
    n2 = Node('z_node2', in_region=r1)
    n1 = Node('z_node1', in_region=r1)
    r1_nodes = list(r1.nodes_sorted)
    assert len(r1_nodes) == 3
    assert r1_nodes[0] == r2
    assert r1_nodes[1] == n1
    assert r1_nodes[2] == n2

def test_is_local_node(regions):
    r1, r2 = regions
    n1 = Node('node1', in_region=r1)
    n2 = Node('node2', in_region=r2)
    assert not n1._is_local_node(n2)
    assert n1._is_local_node(r2)

def test_local_nodes(regions):
    r1, r2 = regions
    a = Node('a', r1)
    b = Node('b', r1)
    c = Node('c', r1)
    x = Node('x', r2)
    y = Node('y', r2)
    a.add_edge(b)
    a.add_edge(x)
    c.add_edge(a)
    y.add_edge(a)
    assert b in a.local_next and b not in a.other_next
    assert x in a.other_next and x not in a.local_next
    assert c in a.local_prev and c not in a.other_prev
    assert y in a.other_prev and y not in a.local_prev

def test_node_dimensions_default():
    a = Node('a')
    assert a.width == 1
    assert a.height == 1

def test_node_dimensions_local(regions):
    r1, r2 = regions
    a = Node('a', r1)
    b = Node('b', r1)
    c = Node('c', r1)
    a.add_edge(b)
    assert a.width == 1
    a.add_edge(c)
    assert a.width == 2
    b.add_edge(c)
    assert c.width == 2
    assert a.height == 1
    assert c.height == 1

def test_node_dimensions_other(regions):
    r1, r2 = regions
    a = Node('a', r1)
    x = Node('x', r2)
    y = Node('y', r2)
    a.add_edge(x)
    assert a.height == 1
    a.add_edge(y)
    assert a.height == 2
    a.add_edge(y)
    assert y.height == 2
    assert a.width == 1
    assert y.width == 1

def test_is_region(regions):
    r1, _ = regions
    n1 = Node('n1')
    assert r1.is_region
    assert not n1.is_region

def test_is_empty(regions):
    _, r2 = regions
    assert r2.is_empty
    n1 = Node('n1', r2)
    assert not r2.is_empty
