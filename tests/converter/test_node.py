import pytest

from bgraph.blockgraph.converter.node import Node, Region

def test_create_node():
    n = Node('abc')
    assert n.name == 'abc'
    assert len(n.nodes) == 0

def test_create_region():
    assert True

def test_create_node_in_region():
    assert True

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
