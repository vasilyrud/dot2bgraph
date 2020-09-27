import pytest

from blockgraph.converter.grid import (
    Grid, _EdgeType,
    _sources, _get_edge_info
)
from blockgraph.converter.node import Node, Region

@pytest.fixture
def region():
    return Region('ag')

@pytest.fixture
def loose_nodes():
    r1 = Region('r1')
    n1 = Node('n1', r1)
    n2 = Node('n2', r1)
    n3 = Node('n3', r1)
    n4 = Node('n4', r1)
    return r1, n1, n2, n3, n4

def test_grid_add_node(loose_nodes):
    r1, n1, _, _, _ = loose_nodes
    grid = Grid(r1)

    grid.add_node(n1, x=10, y=10)
    assert grid.has_node(n1)
    assert grid.get_x(n1) == 10 and grid.get_y(n1) == 10

def test_grid_add_node_defaults(loose_nodes):
    r1, n1, n2, n3, n4 = loose_nodes
    grid = Grid(r1)

    grid.add_node(n1)
    assert grid.get_x(n1) == 0 and grid.get_y(n1) == 0

    grid.add_node(n2)
    assert grid.get_x(n2) == 1 and grid.get_y(n2) == 0

    grid.add_node(n3, y=1)
    assert grid.get_x(n3) == 0 and grid.get_y(n3) == 1

    grid.add_node(n4, x=5)
    assert grid.get_x(n4) == 5 and grid.get_y(n4) == 1

def test_grid_add_node_errors(loose_nodes):
    r1, n1, n2, _, _ = loose_nodes
    grid = Grid(r1)

    grid.add_node(n1)
    assert grid.get_x(n1) == 0 and grid.get_y(n1) == 0

    with pytest.raises(AssertionError):
        grid.add_node(n1)

    with pytest.raises(AssertionError):
        grid.add_node(n2, x=0, y=0)

def test_grid_del_node(loose_nodes):
    r1, n1, n2, _, _ = loose_nodes
    grid = Grid(r1)

    assert not grid.has_node(n1)
    grid.add_node(n1, x=10, y=10)
    assert grid.has_node(n1)
    assert grid.get_x(n1) == 10 and grid.get_y(n1) == 10

    grid.del_node(n1)
    assert not grid.has_node(n1)
    assert len(grid._coord2node) == 0
    assert len(grid._node2coord) == 0

    grid.add_node(n2, x=10, y=10)
    grid.add_node(n1)

def test_sources_sinks_empty_region(region):
    with pytest.raises(AssertionError):
        _sources(region)

def test_sources_sinks_pure(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    c.add_edge(d)

    srcs = _sources(region)
    assert len(srcs) == 2
    assert srcs[0] == a

def test_sources_sinks_that_are_both(region):
    a = Node('a', region)
    b = Node('b', region)

    srcs = _sources(region)
    assert len(srcs) == 2
    assert srcs[0] == a

def test_sources_sinks_not_pure(region):
    a = Node('a', region)
    b = Node('b', region)
    a.add_edge(b)
    b.add_edge(a)

    srcs = _sources(region)
    assert len(srcs) == 1
    assert srcs[0] == a

def test_sources_sinks_max_out_in(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    a.add_edge(c)
    b.add_edge(a)
    d.add_edge(c)
    c.add_edge(d)

    srcs = _sources(region)
    assert len(srcs) == 1
    assert srcs[0] == a

def test_get_edge_info_loose(region):
    a = Node('a', region)
    b = Node('b', region)

    edge_types, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 0

def test_get_edge_info_loop(region):
    a = Node('a', region)
    b = Node('b', region)
    a.add_edge(b)
    b.add_edge(a)

    edge_types, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 1
    assert edge_types[(a,b)] == _EdgeType.NORMAL
    assert edge_types[(b,a)] == _EdgeType.BACK

def test_get_edge_info_max_out_in(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    a.add_edge(c)
    b.add_edge(a)
    d.add_edge(c)
    c.add_edge(d)

    edge_types, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 1
    assert node_depths[c] == 1
    assert node_depths[d] == 2
    assert edge_types[(b,a)] == _EdgeType.BACK
    assert edge_types[(d,c)] == _EdgeType.BACK

def test_get_edge_info_forward_edge(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    a.add_edge(b)
    b.add_edge(c)
    a.add_edge(c)

    edge_types, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 1
    assert node_depths[c] == 2
    assert edge_types[(a,b)] == _EdgeType.NORMAL
    assert edge_types[(b,c)] == _EdgeType.NORMAL
    assert edge_types[(a,c)] == _EdgeType.FWD

def test_get_edge_info_cross_edge(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    a.add_edge(c)
    a.add_edge(b)
    b.add_edge(c)

    edge_types, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 1
    assert node_depths[c] == 2
    assert edge_types[(a,b)] == _EdgeType.NORMAL
    assert edge_types[(b,c)] == _EdgeType.CROSS
    assert edge_types[(a,c)] == _EdgeType.NORMAL

def test_get_edge_info_source_cross_right(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    b.add_edge(c)
    d.add_edge(c)

    edge_types, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 1
    assert node_depths[c] == 2
    assert node_depths[d] == 0
    assert edge_types[(b,c)] == _EdgeType.NORMAL
    assert edge_types[(d,c)] == _EdgeType.CROSS

def test_get_edge_info_source_cross_left(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(c)
    d.add_edge(b)
    b.add_edge(c)

    edge_types, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 1
    assert node_depths[c] == 2
    assert node_depths[d] == 0
    assert edge_types[(b,c)] == _EdgeType.CROSS
    assert edge_types[(a,c)] == _EdgeType.NORMAL
