import pytest

from blockgraph.converter.grid import (
    GridRows, GridPack, EdgeType,
    _sources, _sinks, _get_edge_info,
    _independent_sub_grids,
    _make_pack_grid, _make_rows_grid,
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

def offset_based_width(grid):
    ''' Test offset numbers by re-computing width
    based on offset iterator.
    '''
    offsets = list(grid.iter_offsets())
    if not offsets:
        return grid.node.width
    return max(
        max(x + g.width + g.padding_outer for x, _, g in offsets),
        grid.node.width,
    )

def offset_based_height(grid):
    ''' Test offset numbers by re-computing height
    based on offset iterator.
    '''
    offsets = list(grid.iter_offsets())
    if not offsets:
        return grid.node.height
    return max(
        max(y + g.height + g.padding_outer for _, y, g in offsets),
        grid.node.height,
    )

def _add_sub_grid(grid, node, x = None, y = None):
    sub_grid = GridRows(node, grid.padding_outer, grid.padding_inner)

    if x is None and y is None:
        grid.add_sub_grid(sub_grid          )
    elif x is None and y is not None:
        grid.add_sub_grid(sub_grid,      y=y)
    elif x is not None and y is None:
        grid.add_sub_grid(sub_grid, x=x     )
    else:
        grid.add_sub_grid(sub_grid, x=x, y=y)

    return sub_grid

def test_grid_add_sub_grid(region_nodes):
    r1, n1, _, _, _ = region_nodes
    grid = GridRows(r1, 1, 1)

    _add_sub_grid(grid, n1, x=10, y=10)
    assert grid._has_node(n1)
    assert grid._get_x(n1) == 10 and grid._get_y(n1) == 10

def test_grid_add_sub_grid_defaults(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes
    grid = GridRows(r1, 1, 1)

    _add_sub_grid(grid, n1)
    assert grid._get_x(n1) == 0 and grid._get_y(n1) == 0

    _add_sub_grid(grid, n2)
    assert grid._get_x(n2) == 1 and grid._get_y(n2) == 0

    _add_sub_grid(grid, n3, y=1)
    assert grid._get_x(n3) == 0 and grid._get_y(n3) == 1

    _add_sub_grid(grid, n4, x=5)
    assert grid._get_x(n4) == 5 and grid._get_y(n4) == 1

def test_grid_add_sub_grid_errors(region_nodes):
    r1, n1, n2, _, _ = region_nodes
    grid = GridRows(r1, 1, 1)

    _add_sub_grid(grid, n1)
    assert grid._get_x(n1) == 0 and grid._get_y(n1) == 0

    with pytest.raises(AssertionError):
        _add_sub_grid(grid, n1)

    with pytest.raises(AssertionError):
        _add_sub_grid(grid, n2, x=0, y=0)

def _test_dimension_empty(grid_type, region_nodes):
    r1, _, _, _, _ = region_nodes
    grid = globals()[grid_type](r1, 1, 1)

    assert grid.width  == 1
    assert grid.height == 1

def test_grid_dimension_empty(region_nodes):
    _test_dimension_empty('GridRows', region_nodes)
    _test_dimension_empty('GridPack', region_nodes)

def _test_grid_dimension_gets_cached(grid_type, region_nodes):
    r1, _, _, _, _ = region_nodes
    grid = globals()[grid_type](r1, 1, 1)

    assert grid._width  == None
    assert grid.width  == 1
    assert grid._width  == 1
    assert grid.width  == 1

    assert grid._height == None
    assert grid.height == 1
    assert grid._height == 1
    assert grid.height == 1

def test_grid_dimension_gets_cached(region_nodes):
    _test_grid_dimension_gets_cached('GridRows', region_nodes)
    _test_grid_dimension_gets_cached('GridPack', region_nodes)

def _test_grid_dimension_invalidated_by_add(grid_type, region_nodes):
    r1, n1, _, _, _ = region_nodes
    grid = globals()[grid_type](r1, 1, 1)

    assert grid.width  == 1
    assert grid.height == 1

    _add_sub_grid(grid, n1, 0, 0)

    assert grid._width  == None
    assert grid.width  == 3
    assert grid._width  == 3

    assert grid._height == None
    assert grid.height == 3
    assert grid._height == 3

def test_grid_dimension_invalidated_by_add(region_nodes):
    _test_grid_dimension_invalidated_by_add('GridRows', region_nodes)
    _test_grid_dimension_invalidated_by_add('GridPack', region_nodes)

def _test_grid_dimension_single(grid_type, region_nodes):
    r1, n1, _, _, _ = region_nodes
    grid = globals()[grid_type](r1, 1, 1)
    _add_sub_grid(grid, n1, 0, 0)

    grid_n1 = grid._sub_grid_from_node(n1)

    assert grid_n1.width  == 1
    assert grid_n1.height == 1
    assert grid.width  == 3
    assert grid.height == 3

    assert grid_n1.width  == offset_based_width(grid_n1)
    assert grid_n1.height == offset_based_height(grid_n1)
    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def test_grid_dimension_single(region_nodes):
    _test_grid_dimension_single('GridRows', region_nodes)
    _test_grid_dimension_single('GridPack', region_nodes)

def test_grid_dimension_edges_other_single(regions, loose_nodes):
    r1, r2, _ = regions
    n1, n2, _, _ = loose_nodes

    n1.in_region = r1
    n2.in_region = r2

    n1.add_edge(n2)
    n2.add_edge(n1)

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1)

    grid_n1 = grid._sub_grid_from_node(n1)

    assert grid_n1.width  == 1
    assert grid_n1.height == 1
    assert grid.width  == 3
    assert grid.height == 3

    assert grid_n1.width  == offset_based_width(grid_n1)
    assert grid_n1.height == offset_based_height(grid_n1)
    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

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

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1)

    grid_n1 = grid._sub_grid_from_node(n1)

    assert grid_n1.width  == 1
    assert grid_n1.height == 3
    assert grid.width  == 3
    assert grid.height == 5

    assert grid_n1.width  == offset_based_width(grid_n1)
    assert grid_n1.height == offset_based_height(grid_n1)
    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

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

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1)

    grid_n1 = grid._sub_grid_from_node(n1)

    assert grid_n1.width  == 1
    assert grid_n1.height == 3
    assert grid.width  == 3
    assert grid.height == 5

    assert grid_n1.width  == offset_based_width(grid_n1)
    assert grid_n1.height == offset_based_height(grid_n1)
    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def test_grid_dimension_edges_local_single(regions, loose_nodes):
    r1, _, _ = regions
    n1, n2, _, _ = loose_nodes

    n1.in_region = r1
    n2.in_region = r1

    n1.add_edge(n2)
    n2.add_edge(n1)

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1)
    # Intentionally don't add n2 to grid

    grid_n1 = grid._sub_grid_from_node(n1)

    assert grid_n1.width  == 1
    assert grid_n1.height == 1
    assert grid.width  == 3
    assert grid.height == 3

    assert grid_n1.width  == offset_based_width(grid_n1)
    assert grid_n1.height == offset_based_height(grid_n1)
    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

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

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1)
    # Intentionally don't add n2, n3, n4 to grid

    grid_n1 = grid._sub_grid_from_node(n1)

    assert grid_n1.width  == 3
    assert grid_n1.height == 1
    assert grid.width  == 5
    assert grid.height == 3

    assert grid_n1.width  == offset_based_width(grid_n1)
    assert grid_n1.height == offset_based_height(grid_n1)
    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

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

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1)
    # Intentionally don't add n2, n3, n4 to grid

    grid_n1 = grid._sub_grid_from_node(n1)

    assert grid_n1.width  == 3
    assert grid_n1.height == 1
    assert grid.width  == 5
    assert grid.height == 3

    assert grid_n1.width  == offset_based_width(grid_n1)
    assert grid_n1.height == offset_based_height(grid_n1)
    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def _test_grid_dimension_more_edges_than_sub_grids(grid_type, regions, loose_nodes):
    r1, r2, _ = regions
    _, n2, _, _ = loose_nodes

    grid = globals()[grid_type](r1, 1, 1)

    grid2 = globals()[grid_type](r2, 1, 1)
    grid.add_sub_grid(grid2, 0, 0)

    _add_sub_grid(grid2, n2, 0, 0)
    # Don't bother adding other nodes/regions to grids

    grid_n2 = grid2._sub_grid_from_node(n2)

    assert grid_n2.width  == 1
    assert grid_n2.height == 1
    assert grid2.width  == 4
    assert grid2.height == 4

    assert grid_n2.width  == offset_based_width(grid_n2)
    assert grid_n2.height == offset_based_height(grid_n2)
    assert grid2.width  == offset_based_width(grid2)
    assert grid2.height == offset_based_height(grid2)

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

    _test_grid_dimension_more_edges_than_sub_grids('GridRows', regions, loose_nodes)
    _test_grid_dimension_more_edges_than_sub_grids('GridPack', regions, loose_nodes)

def test_grid_dimension_multiple_nodes(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1, x=0, y=0)
    _add_sub_grid(grid, n2, x=0, y=1)
    _add_sub_grid(grid, n3, x=1, y=0)
    _add_sub_grid(grid, n4, x=1, y=1)

    assert grid.width  == 5
    assert grid.height == 5

    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def test_grid_pack_dimension_multiple_nodes(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes

    grid = GridPack(r1, 1, 0)
    _add_sub_grid(grid, n1, x=0, y=0)
    _add_sub_grid(grid, n2, x=0, y=1)
    _add_sub_grid(grid, n3, x=1, y=0)
    _add_sub_grid(grid, n4, x=1, y=1)

    assert grid.width  == 4
    assert grid.height == 4

    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def test_grid_dimension_gaps(region_nodes):
    r1, n1, _, _, _ = region_nodes

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1, x=1, y=1)

    assert grid.width  == 3
    assert grid.height == 3

    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def test_grid_dimension_gaps_diagonal(region_nodes):
    r1, n1, n2, _, _ = region_nodes

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1, x=0, y=0)
    _add_sub_grid(grid, n2, x=1, y=1)

    assert grid.width  == 3
    assert grid.height == 5

    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def test_grid_dimension_non_default(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes

    o, i = (2, 6)

    grid = GridRows(r1,
        padding_outer=o,
        padding_inner=i,
    )
    _add_sub_grid(grid, n1, x=0, y=0)
    _add_sub_grid(grid, n2, x=0, y=1)
    _add_sub_grid(grid, n3, x=1, y=0)
    _add_sub_grid(grid, n4, x=1, y=1)

    assert grid.width  == o + 1 + i + 1 + o
    assert grid.height == o + 1 + i + 1 + o

    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def test_grid_dimension_non_default_children(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes
    r2 = Region('r2', r1)
    n1.in_region = r2
    n2.in_region = r2
    n3.in_region = r2
    n4.in_region = r2

    o, i = (2, 6)

    grid = GridRows(r1, o, i)
    grid2 = _add_sub_grid(grid, r2)

    _add_sub_grid(grid2, n1, x=0, y=0)
    _add_sub_grid(grid2, n2, x=0, y=1)
    _add_sub_grid(grid2, n3, x=1, y=0)
    _add_sub_grid(grid2, n4, x=1, y=1)

    assert grid2.width  == o + 1 + i + 1 + o
    assert grid2.height == o + 1 + i + 1 + o

    assert grid2.width  == offset_based_width(grid2)
    assert grid2.height == offset_based_height(grid2)

def test_grid_dimension_nested():
    r1 = Region('r1')
    r2 = Region('r2', r1)
    r3 = Region('r3', r2)
    n3 = Node('n3', r3)

    grid1 = GridRows(r1, 1, 1)
    grid2 = _add_sub_grid(grid1, r2)
    grid3 = _add_sub_grid(grid2, r3)
    grid4 = _add_sub_grid(grid3, n3)

    assert grid4.width == 1 and grid4.height == 1
    assert grid3.width == 3 and grid3.height == 3
    assert grid2.width == 5 and grid2.height == 5
    assert grid1.width == 7 and grid1.height == 7

def test_grid_pack_dimension_nested():
    r1 = Region('r1')
    r2 = Region('r2', r1)
    r3 = Region('r3', r2)
    n3 = Node('n3', r3)

    grid1 = GridPack(r1, 1, 1)

    grid2 = GridPack(r2, 1, 1)
    grid1.add_sub_grid(grid2, 0, 0)

    grid3 = GridPack(r3, 1, 1)
    grid2.add_sub_grid(grid3, 0, 0)

    grid4 = GridPack(n3, 1, 1)
    grid3.add_sub_grid(grid4, 0, 0)

    assert grid4.width == 1 and grid4.height == 1
    assert grid3.width == 3 and grid3.height == 3
    assert grid2.width == 5 and grid2.height == 5
    assert grid1.width == 7 and grid1.height == 7

def test_grid_dimension_complex():
    ''' Same graph as on the description of Grid.
    '''

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

    grid = GridRows(r1, 1, 1)

    _add_sub_grid(grid, n1, x=0, y=0)
    _add_sub_grid(grid, n2, x=1, y=0)
    _add_sub_grid(grid, n3, x=0, y=1)
    _add_sub_grid(grid, n4, x=1, y=1)
    _add_sub_grid(grid, n5, x=0, y=2)
    _add_sub_grid(grid, n6, x=0, y=4)
    _add_sub_grid(grid, n7, x=2, y=4)

    assert grid.width  == 15
    assert grid.height == 11

    assert grid.width  == offset_based_width(grid)
    assert grid.height == offset_based_height(grid)

def test_row_width(region_nodes):
    r1, n1, n2, _, _ = region_nodes

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1, x=0, y=0)
    _add_sub_grid(grid, n2, x=1, y=0)

    assert grid._row_width_total(0) == 5
    with pytest.raises(KeyError):
        assert grid._row_width_total(1)

def test_row_offset(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1, x=1, y=0)
    _add_sub_grid(grid, n2, x=0, y=1)
    _add_sub_grid(grid, n3, x=1, y=1)
    _add_sub_grid(grid, n4, x=2, y=1)

    assert grid.width == 7

    assert grid._row_offset(0) == 2
    assert grid._row_offset_end(0) == 2
    assert grid._row_offset(1) == 0
    assert grid._row_offset_end(1) == 0

def test_row_offset_odd(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes

    n2.add_edge(n3)
    n2.add_edge(n4)

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1, x=1, y=0)
    _add_sub_grid(grid, n2, x=0, y=1)
    _add_sub_grid(grid, n3, x=1, y=1)
    _add_sub_grid(grid, n4, x=2, y=1)

    assert grid.width == 8

    assert grid._row_offset(0) == 2
    assert grid._row_offset_end(0) == 3
    assert grid._row_offset(1) == 0
    assert grid._row_offset_end(1) == 0

def test_sub_grid_from_coord(region_nodes):
    r1, n1, _, _, _ = region_nodes

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1, x=1, y=0)

    assert grid._sub_grid_from_coord(1, 0) == grid._sub_grid_from_node(n1)

def test_iter_offset(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes

    grid = GridRows(r1, 1, 1)
    _add_sub_grid(grid, n1, x=10, y=10)
    _add_sub_grid(grid, n2, x=10, y=15)
    _add_sub_grid(grid, n3, x=20, y=15)
    _add_sub_grid(grid, n4, x=30, y=30)

    assert grid.width  == 5
    assert grid.height == 7

    offsets_y    = list(oy[0] for oy in grid._iter_offset_y())
    offsets_10_x = list(ox[0] for ox in grid._iter_offset_x(10))
    offsets_15_x = list(ox[0] for ox in grid._iter_offset_x(15))
    offsets_30_x = list(ox[0] for ox in grid._iter_offset_x(30))

    assert offsets_y[0] == 1
    assert offsets_y[1] == 3
    assert offsets_y[2] == 5

    assert offsets_10_x[0] == 2
    assert offsets_15_x[0] == 1
    assert offsets_15_x[1] == 3
    assert offsets_30_x[0] == 2

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

def test_sinks_empty_region(region):
    snks = _sinks(region)
    assert len(snks) == 0

def test_sinks_pure(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    c.add_edge(d)

    snks = _sinks(region)
    assert len(snks) == 2
    assert snks[0] == b

def test_sinks_not_pure(region):
    a = Node('a', region)
    b = Node('b', region)
    a.add_edge(b)
    b.add_edge(a)

    snks = _sinks(region)
    assert len(snks) == 0

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

def test_get_edge_info_update_depth(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    e = Node('e', region)
    a.add_edge(b)
    a.add_edge(c)
    a.add_edge(d)
    c.add_edge(e)
    d.add_edge(b)
    b.add_edge(e)

    _, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 2
    assert node_depths[c] == 1
    assert node_depths[d] == 1
    assert node_depths[e] == 3

def test_get_edge_info_sinks_depth(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    e = Node('e', region)
    f = Node('f', region)
    g = Node('g', region)
    a.add_edge(b)
    c.add_edge(d)
    d.add_edge(e)
    f.add_edge(g)

    _, node_depths = _get_edge_info(region)
    assert node_depths[b] == 2
    assert node_depths[e] == 2
    assert node_depths[g] == 2

def test_get_edge_info_update_depth_with_loop(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    e = Node('e', region)
    f = Node('f', region)
    g = Node('g', region)
    h = Node('h', region)
    i = Node('i', region)
    j = Node('j', region)
    a.add_edge(b)
    a.add_edge(c)
    a.add_edge(d)
    c.add_edge(e)
    d.add_edge(b)
    b.add_edge(f)
    f.add_edge(g)
    f.add_edge(h)
    g.add_edge(h)
    h.add_edge(i)
    h.add_edge(j)
    i.add_edge(f)

    _, node_depths = _get_edge_info(region)
    assert node_depths[a] == 0
    assert node_depths[b] == 2
    assert node_depths[c] == 1
    assert node_depths[d] == 1
    assert node_depths[e] == 6
    assert node_depths[f] == 3
    assert node_depths[g] == 4
    assert node_depths[h] == 5
    assert node_depths[i] == 6
    assert node_depths[j] == 6

def test_sub_grid_from_node(region):
    a = Node('a', region)
    r2 = Region('r2', region)

    grid = place_on_grid(region, 1, 1)
    assert grid._sub_grid_from_node(a) == grid._node2grid[a]
    assert grid._sub_grid_from_node(r2) == grid._node2grid[r2]

def test_sub_grid_iter(region):
    z = Node('z', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    z.add_edge(b)
    c.add_edge(d)
    z.add_edge(d)

    grid = place_on_grid(region, 1, 1)
    assert isinstance(grid, GridRows)

    sub_grids = grid.sub_grids
    assert sub_grids[0].node == c
    assert sub_grids[1].node == z
    assert sub_grids[2].node == d
    assert sub_grids[3].node == b

def test_independent_sub_grids_no_nodes():
    assert _independent_sub_grids({}) == False

def test_independent_sub_grids_few_nodes():
    assert _independent_sub_grids({
        Node('a'): 0, 
        Node('b'): 1,
    }) == False

def test_independent_sub_grids_diff_depths():
    assert _independent_sub_grids({
        Node('a'): 0,
        Node('b'): 1,
        Node('c'): 2,
    }) == False

def test_independent_sub_grids_same_depths():
    assert _independent_sub_grids({
        Node('a'): 0,
        Node('b'): 0,
        Node('c'): 0,
    }) == True

def test_make_pack_grid_empty(region_nodes):
    r1, _, _, _, _ = region_nodes
    grid = _make_pack_grid(r1, 2, 3, [])
    assert grid.width  == 1
    assert grid.height == 1
    assert len(list(grid.iter_offsets())) == 0

def test_make_rows_grid_empty(region_nodes):
    r1, _, _, _, _ = region_nodes
    grid = _make_rows_grid(r1, 2, 3, [])
    assert grid.width  == 1
    assert grid.height == 1
    assert len(list(grid.iter_offsets())) == 0

def test_make_pack_grid_single_grid(region_nodes):
    r1, n1, _, _, _ = region_nodes
    grid = _make_pack_grid(r1, 2, 3, [
        (GridPack(n1, 1, 1), None),
    ])
    assert grid.width  == 5
    assert grid.height == 5
    assert len(list(grid.iter_offsets())) == 1

def test_make_rows_grid_single_grid(region_nodes):
    r1, n1, _, _, _ = region_nodes
    grid = _make_rows_grid(r1, 2, 3, [
        (GridRows(n1, 1, 1), 0),
    ])
    assert grid.width  == 5
    assert grid.height == 5
    assert len(list(grid.iter_offsets())) == 1

def test_make_pack_grid_multiple_grids(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes
    grid = _make_pack_grid(r1, 2, 3, [
        (GridPack(n1, 1, 1), None),
        (GridRows(n2, 1, 1), None),
        (GridPack(n3, 1, 1), None),
        (GridRows(n4, 1, 1), None),
    ])
    assert grid.width  == 9
    assert grid.height == 9
    assert len(list(grid.iter_offsets())) == 4

def test_make_rows_grid_multiple_grids(region_nodes):
    r1, n1, n2, n3, n4 = region_nodes
    grid = _make_rows_grid(r1, 2, 3, [
        (GridPack(n1, 1, 1), 0),
        (GridRows(n2, 1, 1), 1),
        (GridPack(n3, 1, 1), 1),
        (GridRows(n4, 1, 1), 2),
    ])
    assert grid.width  == 9
    assert grid.height == 13
    assert len(list(grid.iter_offsets())) == 4

def test_place_on_grid_empty(region):
    grid = place_on_grid(region, 1, 1)
    assert isinstance(grid, GridRows)

    assert grid.node == region
    assert grid._is_empty()

def test_place_on_grid_one_level(region):
    a = Node('a', region)
    b = Node('b', region)
    c = Node('c', region)
    d = Node('d', region)
    a.add_edge(b)
    c.add_edge(d)
    a.add_edge(d)

    grid = place_on_grid(region, 1, 1)
    assert isinstance(grid, GridRows)

    sub_grids = grid.sub_grids
    assert not grid._is_empty()
    assert len(sub_grids) == 4
    assert all(g._is_empty() for g in sub_grids)

def test_place_on_grid_multi_level(region):
    a = Node('a', region)
    r2 = Region('r2', region)
    b = Node('b', r2)
    r3 = Region('r3', r2)
    c = Node('c', r3)
    d = Node('d', r3)
    a.add_edge(r2)
    b.add_edge(c)
    b.add_edge(r3)
    c.add_edge(d)
    r3.add_edge(r2)
    d.add_edge(b)

    grid1 = place_on_grid(region, 1, 1)
    assert isinstance(grid1, GridRows)
    assert len(grid1.sub_grids) == 2
    assert a in grid1.sub_nodes and r2 in grid1.sub_nodes

    grid2 = grid1._sub_grid_from_node(r2)
    assert isinstance(grid2, GridRows)
    assert len(grid2.sub_grids) == 2
    assert b in grid2.sub_nodes and r3 in grid2.sub_nodes

    grid3 = grid2._sub_grid_from_node(r3)
    assert isinstance(grid3, GridRows)
    assert len(grid3.sub_grids) == 2
    assert c in grid3.sub_nodes and d in grid3.sub_nodes

def test_place_on_grid_alternating_grids_top_pack():
    r1 = Region('r1')

    a1 = Node('a1', r1)
    b1 = Node('b1', r1)
    c1 = Node('c1', r1)
    r2 = Region('r2', r1)

    r3 = Region('r3', r2)

    a3 = Node('a3', r3)
    b3 = Node('b3', r3)
    c3 = Node('c3', r3)
    d3 = Node('d3', r3)

    grid1 = place_on_grid(r1, 1, 1)
    assert isinstance(grid1, GridPack)
    assert len(grid1.sub_grids) == 4

    grid2 = grid1._sub_grid_from_node(r2)
    assert isinstance(grid2, GridRows)
    assert len(grid2.sub_grids) == 1

    grid3 = grid2._sub_grid_from_node(r3)
    assert isinstance(grid3, GridPack)
    assert len(grid3.sub_grids) == 4

def test_place_on_grid_alternating_grids_top_rows():
    r1 = Region('r1')

    r2 = Region('r2', r1)

    a2 = Node('a2', r2)
    b2 = Node('b2', r2)
    c2 = Node('c2', r2)
    r3 = Region('r3', r2)

    a3 = Node('a3', r3)

    grid1 = place_on_grid(r1, 1, 1)
    assert isinstance(grid1, GridRows)
    assert len(grid1.sub_grids) == 1

    grid2 = grid1._sub_grid_from_node(r2)
    assert isinstance(grid2, GridPack)
    assert len(grid2.sub_grids) == 4

    grid3 = grid2._sub_grid_from_node(r3)
    assert isinstance(grid3, GridRows)
    assert len(grid3.sub_grids) == 1
