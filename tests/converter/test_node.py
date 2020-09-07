import pytest

from pygraphviz import AGraph

from bgraph.blockgraph.converter.node import Node, Region

def _make_nodes():
    n1 = Node('node1')
    n2 = Node('node2')
    return n1, n2

def _make_agraphs():
    a1 = AGraph(name='ag', strict=False, directed=True)
    a2 = a1.add_subgraph(name='subg')
    return a1, a2

def _make_regions():
    a1, a2 = _make_agraphs()
    r1 = Region(a1)
    r2 = Region(a2, r1)
    return r1, r2

def test_create_node():
    n1 = Node('node1')
    assert n1.name == 'node1'
    assert len(n1.nodes) == 0

def test_create_region():
    a1, _ = _make_agraphs()
    r1 = Region(a1)
    assert r1.agraph == a1
    assert r1.name == 'ag'

def test_in_region():
    r1, r2 = _make_regions()
    assert r1.in_region is None
    assert r2.in_region == r1

def test_create_region_with_node():
    r1, _ = _make_regions()
    n1 = Node('node1', in_region=r1)
    assert n1.in_region == r1

def test_add_node_to_region():
    r1, r2 = _make_regions()
    n1, n2 = _make_nodes()
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

def test_nodes_iter():
    r1, r2 = _make_regions()
    n2 = Node('node2', in_region=r1)
    n1 = Node('node1', in_region=r1)
    r1_nodes = list(r1.nodes_iter())
    assert r1_nodes[0] == n1
    assert r1_nodes[1] == n2
    assert r1_nodes[2] == r2
