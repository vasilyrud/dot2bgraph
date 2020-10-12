import pytest

from blockgraph.converter.grid import (
    Grid, EdgeType,
    _sources, _get_edge_info,
    place_on_grid
)
from blockgraph.converter.node import Node, Region

def _region():
    return Region('r1')

def _loose_nodes():
    n1 = Node('n1')
    n2 = Node('n2')
    n3 = Node('n3')
    n4 = Node('n4')
    return n1, n2, n3, n4

@pytest.fixture
def region():
    return _region()

@pytest.fixture
def regions():
    r1 = Region('r1')
    r2 = Region('r2')
    r3 = Region('r3')
    return r1, r2, r3

@pytest.fixture
def loose_nodes():
    return _loose_nodes()

@pytest.fixture
def region_nodes():
    r1 = _region()
    n1, n2, n3, n4 = _loose_nodes()
    n1.in_region = r1
    n2.in_region = r1
    n3.in_region = r1
    n4.in_region = r1
    return r1, n1, n2, n3, n4

def test_grid_add_sub_grid(region_nodes):
    r1, n1, _, _, _ = region_nodes
    grid = Grid(r1)

    grid.add_sub_grid(n1, x=10, y=10)
    assert grid.has_node(n1)
    assert grid.get_x(n1) == 10 and grid.get_y(n1) == 10

def test_grid_add_sub_grid_defaults(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes
    grid = Grid(r1)

    grid.add_sub_grid(n1)
    assert grid.get_x(n1) == 0 and grid.get_y(n1) == 0

    grid.add_sub_grid(n2)
    assert grid.get_x(n2) == 1 and grid.get_y(n2) == 0

    grid.add_sub_grid(n3, y=1)
    assert grid.get_x(n3) == 0 and grid.get_y(n3) == 1

    grid.add_sub_grid(n4, x=5)
    assert grid.get_x(n4) == 5 and grid.get_y(n4) == 1

def test_grid_add_sub_grid_errors(region_nodes):
    r1, n1, n2, _, _ = region_nodes
    grid = Grid(r1)

    grid.add_sub_grid(n1)
    assert grid.get_x(n1) == 0 and grid.get_y(n1) == 0

    with pytest.raises(AssertionError):
        grid.add_sub_grid(n1)

    with pytest.raises(AssertionError):
        grid.add_sub_grid(n2, x=0, y=0)

def test_grid_del_sub_grid(region_nodes):
    r1, n1, n2, _, _ = region_nodes
    grid = Grid(r1)

    assert not grid.has_node(n1)
    grid.add_sub_grid(n1, x=10, y=10)
    assert grid.has_node(n1)
    assert grid.get_x(n1) == 10 and grid.get_y(n1) == 10

    grid.del_sub_grid(n1)
    assert not grid.has_node(n1)
    assert len(grid._coord2node) == 0
    assert len(grid._node2coord) == 0

    grid.add_sub_grid(n2, x=10, y=10)
    grid.add_sub_grid(n1)
    assert grid.get_x(n2) == 10 and grid.get_y(n2) == 10
    assert grid.get_x(n1) == 11 and grid.get_y(n1) == 10

def test_grid_dimension_empty(region_nodes):
    r1, _, _, _, _ = region_nodes
    grid = Grid(r1)

    assert grid.width  == 1
    assert grid.height == 1

def test_grid_dimension_single(region_nodes):
    r1, n1, _, _, _ = region_nodes
    grid = Grid(r1)
    grid.add_sub_grid(n1)

    assert grid.get_sub_grid(n1).width  == 1
    assert grid.get_sub_grid(n1).height == 1
    assert grid.width  == 3
    assert grid.height == 3

def test_grid_dimension_edges_other_single(regions, loose_nodes):
    r1, r2, _ = regions
    n1, n2, _, _ = loose_nodes

    n1.in_region = r1
    n2.in_region = r2

    n1.add_edge(n2)
    n2.add_edge(n1)

    grid = Grid(r1)
    grid.add_sub_grid(n1)

    assert grid.get_sub_grid(n1).width  == 1
    assert grid.get_sub_grid(n1).height == 1
    assert grid.width  == 3
    assert grid.height == 3

def test_grid_dimension_edges_other_multiple_next(regions, loose_nodes):
    r1, r2, _ = regions
    n1, n2, n3, n4 = loose_nodes

    n1.in_region = r1
    n2.in_region = r2
    n3.in_region = r2
    n4.in_region = r2

    n1.add_edge(n2)
    n1.add_edge(n3)
    n1.add_edge(n4)

    grid = Grid(r1)
    grid.add_sub_grid(n1)

    assert grid.get_sub_grid(n1).width  == 1
    assert grid.get_sub_grid(n1).height == 3
    assert grid.width  == 3
    assert grid.height == 5

def test_grid_dimension_edges_other_multiple_prev(regions, loose_nodes):
    r1, r2, _ = regions
    n1, n2, n3, n4 = loose_nodes

    n1.in_region = r1
    n2.in_region = r2
    n3.in_region = r2
    n4.in_region = r2

    n2.add_edge(n1)
    n3.add_edge(n1)
    n4.add_edge(n1)

    grid = Grid(r1)
    grid.add_sub_grid(n1)

    assert grid.get_sub_grid(n1).width  == 1
    assert grid.get_sub_grid(n1).height == 3
    assert grid.width  == 3
    assert grid.height == 5

def test_grid_dimension_edges_local_single(regions, loose_nodes):
    r1, _, _ = regions
    n1, n2, _, _ = loose_nodes

    n1.in_region = r1
    n2.in_region = r1

    n1.add_edge(n2)
    n2.add_edge(n1)

    grid = Grid(r1)
    grid.add_sub_grid(n1)
    # Intentionally don't add n2 to grid

    assert grid.get_sub_grid(n1).width  == 1
    assert grid.get_sub_grid(n1).height == 1
    assert grid.width  == 3
    assert grid.height == 3

def test_grid_dimension_edges_local_multiple_next(regions, loose_nodes):
    r1, _, _ = regions
    n1, n2, n3, n4 = loose_nodes

    n1.in_region = r1
    n2.in_region = r1
    n3.in_region = r1
    n4.in_region = r1

    n1.add_edge(n2)
    n1.add_edge(n3)
    n1.add_edge(n4)

    grid = Grid(r1)
    grid.add_sub_grid(n1)
    # Intentionally don't add n2, n3, n4 to grid

    assert grid.get_sub_grid(n1).width  == 3
    assert grid.get_sub_grid(n1).height == 1
    assert grid.width  == 5
    assert grid.height == 3

def test_grid_dimension_edges_local_multiple_prev(regions, loose_nodes):
    r1, _, _ = regions
    n1, n2, n3, n4 = loose_nodes

    n1.in_region = r1
    n2.in_region = r1
    n3.in_region = r1
    n4.in_region = r1

    n2.add_edge(n1)
    n3.add_edge(n1)
    n4.add_edge(n1)

    grid = Grid(r1)
    grid.add_sub_grid(n1)
    # Intentionally don't add n2, n3, n4 to grid

    assert grid.get_sub_grid(n1).width  == 3
    assert grid.get_sub_grid(n1).height == 1
    assert grid.width  == 5
    assert grid.height == 3

def test_grid_dimension_more_edges_than_sub_grids(regions, loose_nodes):
    r1, r2, r3 = regions
    n1, n2, n3, _ = loose_nodes

    r2.in_region = r1
    n1.in_region = r1
    n2.in_region = r2
    n3.in_region = r3

    r2.add_edge(n3)
    r2.add_edge(n3)
    r2.add_edge(n3)
    r2.add_edge(n3)

    r2.add_edge(n1)
    r2.add_edge(n1)
    r2.add_edge(n1)
    r2.add_edge(n1)

    grid = Grid(r1)
    grid2 = grid.add_sub_grid(r2)
    grid2.add_sub_grid(n2)
    # Don't bother adding other nodes/regions to grids

    assert grid2.get_sub_grid(n2).width  == 1
    assert grid2.get_sub_grid(n2).height == 1
    assert grid2.width  == 4
    assert grid2.height == 4

def test_grid_dimension_multiple_nodes(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes

    grid = Grid(r1)
    grid.add_sub_grid(n1, x=0, y=0)
    grid.add_sub_grid(n2, x=0, y=1)
    grid.add_sub_grid(n3, x=1, y=0)
    grid.add_sub_grid(n4, x=1, y=1)

    assert grid.width  == 5
    assert grid.height == 5

def test_grid_dimension_gaps(region_nodes):
    r1, n1, _, _, _ = region_nodes

    grid = Grid(r1)
    grid.add_sub_grid(n1, x=1, y=1)

    assert grid.width  == 3
    assert grid.height == 3

def test_grid_dimension_gaps_diagonal(region_nodes):
    r1, n1, n2, _, _ = region_nodes

    grid = Grid(r1)
    grid.add_sub_grid(n1, x=0, y=0)
    grid.add_sub_grid(n2, x=1, y=1)

    assert grid.width  == 3
    assert grid.height == 5

def test_grid_dimension_non_default(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes

    l, r, t, b, col, row = (2, 3, 4, 5, 6, 7)

    grid = Grid(r1,
        padding_l=l,
        padding_r=r,
        padding_t=t,
        padding_b=b,
        space_col=col,
        space_row=row
    )
    grid.add_sub_grid(n1, x=0, y=0)
    grid.add_sub_grid(n2, x=0, y=1)
    grid.add_sub_grid(n3, x=1, y=0)
    grid.add_sub_grid(n4, x=1, y=1)

    assert grid.width  == l + 1 + col + 1 + r
    assert grid.height == t + 1 + row + 1 + b

def test_grid_dimension_non_default_children(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes
    r2 = Region('r2', r1)

    l, r, t, b, col, row = (2, 3, 4, 5, 6, 7)

    grid = Grid(r1,
        padding_l=l,
        padding_r=r,
        padding_t=t,
        padding_b=b,
        space_col=col,
        space_row=row
    )
    grid2 = grid.add_sub_grid(r2)

    grid2.add_sub_grid(n1, x=0, y=0)
    grid2.add_sub_grid(n2, x=0, y=1)
    grid2.add_sub_grid(n3, x=1, y=0)
    grid2.add_sub_grid(n4, x=1, y=1)

    assert grid2.width  == l + 1 + col + 1 + r
    assert grid2.height == t + 1 + row + 1 + b

def test_grid_dimension_complex():
    r1 = Region('r1')
    r2 = Region('r2')
    n1 = Node('n1', r1)
    n2 = Node('n2', r1)
    n3 = Node('n3', r1)
    n4 = Node('n4', r1)
    n5 = Node('n5', r1)
    n6 = Node('n6', r1)
    n7 = Node('n7', r1)

    l = Node('l', r1) # local
    o = Node('o', r2) # other

    for _ in range(8):
        n1.add_edge(l)
    for _ in range(2):
        n2.add_edge(l)
    for _ in range(4):
        n3.add_edge(l)
    for _ in range(8):
        n4.add_edge(l)
    for _ in range(2):
        n5.add_edge(l)
    for _ in range(3):
        n6.add_edge(l)
    for _ in range(3):
        n7.add_edge(l)

    for _ in range(3):
        n4.add_edge(o)

    grid = Grid(r1)

    grid.add_sub_grid(n1, x=0, y=0)
    grid.add_sub_grid(n2, x=1, y=0)
    grid.add_sub_grid(n3, x=0, y=1)
    grid.add_sub_grid(n4, x=1, y=1)
    grid.add_sub_grid(n5, x=0, y=2)
    grid.add_sub_grid(n6, x=0, y=4)
    grid.add_sub_grid(n7, x=2, y=4)

    assert grid.width  == 15
    assert grid.height == 11

def test_sources_empty_region(region):
    srcs = _sources(region)
    assert len(srcs) == 0

def test_sources_pure(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    c.add_edge(d)

    srcs = _sources(region)
    assert len(srcs) == 2
    assert srcs[0] == a

def test_sources_that_are_both(region):
    a = Node('a', region)
    b = Node('b', region)

    srcs = _sources(region)
    assert len(srcs) == 2
    assert srcs[0] == a

def test_sources_not_pure(region):
    a = Node('a', region)
    b = Node('b', region)
    a.add_edge(b)
    b.add_edge(a)

    srcs = _sources(region)
    assert len(srcs) == 1
    assert srcs[0] == a

def test_sources_max_out_in(region):
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

def test_sources_islands(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    b.add_edge(a)
    c.add_edge(d)
    d.add_edge(c)

    srcs = _sources(region)
    assert len(srcs) == 2
    assert a in srcs
    assert c in srcs

def test_sources_islands_diff(region):
    a = Node('a', region)
    c = Node('c', region)
    d = Node('d', region)
    c.add_edge(d)
    d.add_edge(c)

    srcs = _sources(region)
    assert len(srcs) == 2
    assert a in srcs
    assert c in srcs

def test_sources_multiple_pure_per_conn_comp(region):
    z = Node('z', region)
    y = Node('y', region)
    x = Node('x', region)
    z.add_edge(x)
    y.add_edge(x)

    srcs = _sources(region)
    assert len(srcs) == 2
    assert z in srcs
    assert y in srcs

def test_sources_reverse_order(region):
    c = Node('c', region)
    b = Node('b', region)
    a = Node('a', region)
    c.add_edge(b)
    b.add_edge(a)

    srcs = _sources(region)
    assert len(srcs) == 1
    assert c in srcs

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
    assert edge_types[(a,b)] == EdgeType.NORMAL
    assert edge_types[(b,a)] == EdgeType.BACK

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
    assert edge_types[(b,a)] == EdgeType.BACK
    assert edge_types[(d,c)] == EdgeType.BACK

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
    assert edge_types[(a,b)] == EdgeType.NORMAL
    assert edge_types[(b,c)] == EdgeType.NORMAL
    assert edge_types[(a,c)] == EdgeType.FWD

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
    assert edge_types[(a,b)] == EdgeType.NORMAL
    assert edge_types[(b,c)] == EdgeType.CROSS
    assert edge_types[(a,c)] == EdgeType.NORMAL

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
    assert edge_types[(b,c)] == EdgeType.NORMAL
    assert edge_types[(d,c)] == EdgeType.CROSS

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
    assert edge_types[(b,c)] == EdgeType.CROSS
    assert edge_types[(a,c)] == EdgeType.NORMAL

def test_get_edge_info_inner_loop(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    a.add_edge(b)
    a.add_edge(c)
    b.add_edge(c)
    c.add_edge(b)

    edge_types, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 1
    assert node_depths[c] == 2
    assert edge_types[(b,c)] == EdgeType.NORMAL
    assert edge_types[(c,b)] == EdgeType.BACK

def test_get_sub_grid(region):
    a = Node('a', region)
    r2 = Region('r2', region)

    grid = place_on_grid(region)
    assert grid.get_sub_grid(a) == grid._node2grid[a]
    assert grid.get_sub_grid(r2) == grid._node2grid[r2]

def test_sub_grid_iter(region):
    z = Node('z', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    z.add_edge(b)
    c.add_edge(d)
    z.add_edge(d)

    grid = place_on_grid(region)
    sub_grids = grid.sub_grids
    assert sub_grids[0].node == c
    assert sub_grids[1].node == z
    assert sub_grids[2].node == d
    assert sub_grids[3].node == b

def test_place_on_grid_empty(region):
    grid = place_on_grid(region)
    assert grid.node == region
    assert grid.is_empty

def test_place_on_grid_one_level(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    c.add_edge(d)
    a.add_edge(d)

    grid = place_on_grid(region)
    sub_grids = grid.sub_grids
    assert not grid.is_empty
    assert len(sub_grids) == 4
    assert all(g.is_empty for g in sub_grids)

def test_place_on_grid_multi_level(region):
    a = Node('a', region)
    r2 = Region('r2', region)
    b = Node('b', r2)
    r3 = Region('r3', r2)
    c = Node('c', r3)
    d = Node('d', r3)
    a.add_edge(r2)
    b.add_edge(c)
    c.add_edge(d)
    r3.add_edge(r2)
    d.add_edge(b)

    grid1 = place_on_grid(region)
    assert len(grid1.sub_grids) == 2
    assert a in grid1.sub_nodes and r2 in grid1.sub_nodes

    grid2 = grid1.get_sub_grid(r2)
    assert len(grid2.sub_grids) == 2
    assert b in grid2.sub_nodes and r3 in grid2.sub_nodes

    grid3 = grid2.get_sub_grid(r3)
    assert len(grid3.sub_grids) == 2
    assert c in grid3.sub_nodes and d in grid3.sub_nodes
