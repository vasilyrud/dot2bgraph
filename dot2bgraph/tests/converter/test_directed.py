import pytest

from pygraphviz import AGraph

from blockgraph.converter.directed import (
    _sorted_subgraphs, _direct_nodes, 
    _create_regions_nodes, _agraph2regions,
    _iter_sub_grid_offsets, _create_locations_blocks,
    _create_locations_edge_ends, _grids2locations,
    _get_color, dot2locations,
)
from blockgraph.converter.node import Node, Region
from blockgraph.converter.grid import Grid
from blockgraph.locations import Locations, Direction

@pytest.fixture
def grids():
    r1 = Region('r1')
    a1 = Node('a1', r1)
    z1 = Node('z1', r1)
    r2 = Region('r2', r1)
    r3 = Region('r3', r2)
    n3 = Node('n3', r3)

    a1.add_edge(n3)
    a1.add_edge(n3)
    a1.add_edge(z1)
    a1.add_edge(z1)

    grid1 = Grid(r1)
    grid1_a1 = grid1.add_sub_grid(a1, x=1, y=1)
    grid1_z1 = grid1.add_sub_grid(z1, x=0, y=1)

    grid2 = grid1.add_sub_grid(r2, x=0, y=0)

    grid3 = grid2.add_sub_grid(r3, x=0, y=0)
    grid3_n3 = grid3.add_sub_grid(n3, x=0, y=0)

    return grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3

@pytest.fixture
def colors():
    max_depth = 3
    return [
        _get_color(i, max_depth) 
        for i in range(max_depth+1)
    ]

def test_issue():
    ''' Graph illustrating graphviz bug that
    prevents subgraphs from being iterated in 
    order of creation.
    '''
    dot = '''
    digraph X {
        subgraph cluster_B {
            k -> l;
        }
        subgraph cluster_A {
            k -> e;
            e -> f;
        }
    }
    '''
    agraph = AGraph(string=dot)
    subgraph_names = [ag.name for ag in _sorted_subgraphs(agraph)]
    assert subgraph_names[0] == 'cluster_A' # temporary workaround
    # assert subgraph_names[0] == 'cluster_B' # expected behavior

def test_anodes_to_nodes():
    dot = '''
    digraph X {
        subgraph cluster_A {
            a;
            b;
        }
    }
    '''
    agraph = AGraph(string=dot)
    base_region, anodes_to_nodes = _create_regions_nodes(agraph)

    nodes_A = base_region.nodes_map['cluster_A'].nodes_map
    assert len(anodes_to_nodes) == 2
    assert anodes_to_nodes[agraph.get_node('a')] in nodes_A.values()
    assert anodes_to_nodes[agraph.get_node('b')] in nodes_A.values()
    assert nodes_A['a'] != nodes_A['b']

def test_direct_nodes():
    dot = '''
    digraph X {
        subgraph cluster_A {
            a;
        }
        subgraph cluster_C {
            c;
            a;
            subgraph cluster_B {
                b;
            }
        }
    }
    '''
    agraph = AGraph(string=dot)

    cluster_C = list(_sorted_subgraphs(agraph))[1]
    assert cluster_C.name == 'cluster_C'

    direct_nodes = _direct_nodes(cluster_C, set(('a')))
    assert len(direct_nodes) == 1
    assert 'c' in direct_nodes

def test_agraph2regions_empty():
    dot = '''
    digraph X {
    }
    '''
    agraph = AGraph(string=dot)
    base_region = _agraph2regions(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 0

def test_agraph2regions_child():
    dot = '''
    digraph X {
        x;
        x -> a;
        subgraph cluster_A {
            a;
            a -> b;
            subgraph cluster_B {
                b;
            }
        }
    }
    '''
    agraph = AGraph(string=dot)
    base_region = _agraph2regions(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 2
    assert 'x' in base_nodes and 'cluster_A' in base_nodes

    nodes_A = base_nodes['cluster_A'].nodes_map
    assert len(nodes_A) == 2
    assert 'a' in nodes_A and 'cluster_B' in nodes_A

    nodes_B = nodes_A['cluster_B'].nodes_map
    assert len(nodes_B) == 1
    assert 'b' in nodes_B

def test_agraph2regions_sibling():
    dot = '''
    digraph X {
        x;
        x -> a;
        subgraph cluster_A {
            a;
        }
        subgraph cluster_B {
            b;
            a -> b;
        }
    }
    '''
    agraph = AGraph(string=dot)
    base_region = _agraph2regions(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 3
    assert 'x' in base_nodes and 'cluster_A' in base_nodes and 'cluster_B' in base_nodes
    assert 'a' in base_nodes['x'].other_next_map

    nodes_A = base_nodes['cluster_A'].nodes_map
    assert len(nodes_A) == 1
    assert 'a' in nodes_A
    assert 'x' in nodes_A['a'].other_prev_map
    assert 'b' in nodes_A['a'].other_next_map

    nodes_B = base_nodes['cluster_B'].nodes_map
    assert len(nodes_B) == 1
    assert 'b' in nodes_B
    assert 'a' in nodes_B['b'].other_prev_map

def test_agraph2regions_child_2():
    dot = '''
    digraph X {
        subgraph cluster_A {
            subgraph cluster_B {
                e -> f;
            }
            f -> l;
            k -> e;
            k -> l;
        }
    }
    '''
    agraph = AGraph(string=dot)
    base_region = _agraph2regions(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 1
    assert 'cluster_A' in base_nodes

    nodes_A = base_nodes['cluster_A'].nodes_map
    assert len(nodes_A) == 3
    assert 'k' in nodes_A and 'l' in nodes_A and 'cluster_B' in nodes_A
    assert 'l' in nodes_A['k'].local_next_map
    assert 'k' in nodes_A['l'].local_prev_map
    assert 'e' in nodes_A['k'].other_next_map
    assert 'f' in nodes_A['l'].other_prev_map

    nodes_B = nodes_A['cluster_B'].nodes_map
    assert len(nodes_B) == 2
    assert 'e' in nodes_B and 'f' in nodes_B
    assert 'f' in nodes_B['e'].local_next_map
    assert 'e' in nodes_B['f'].local_prev_map
    assert 'k' in nodes_B['e'].other_prev_map
    assert 'l' in nodes_B['f'].other_next_map

def test_agraph2regions_sibling_2():
    dot = '''
    digraph X {
        subgraph cluster_A {
            k -> l;
        }
        subgraph cluster_B {
            k -> e;
            e -> f;
            f -> l;
        }
    }
    '''
    agraph = AGraph(string=dot)
    base_region = _agraph2regions(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 2
    assert 'cluster_A' in base_nodes and 'cluster_B' in base_nodes

    nodes_A = base_nodes['cluster_A'].nodes_map
    assert len(nodes_A) == 2
    assert 'k' in nodes_A and 'l' in nodes_A

    nodes_B = base_nodes['cluster_B'].nodes_map
    assert len(nodes_B) == 2
    assert 'e' in nodes_B and 'f' in nodes_B


def test_agraph2regions_reverse_sibling():
    ''' Due to alphabetical order, the 2 clusters
    are in reverse order. Once time of creation bug
    is fixed, this behavior will change.
    '''
    dot = '''
    digraph X {
        x;
        x -> b;
        subgraph cluster_B {
            b;
        }
        subgraph cluster_A {
            a;
            b -> a;
        }
    }
    '''
    agraph = AGraph(string=dot)
    base_region = _agraph2regions(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 3
    assert 'x' in base_nodes and 'cluster_A' in base_nodes and 'cluster_B' in base_nodes

    nodes_A = base_nodes['cluster_A'].nodes_map
    # assert len(nodes_A) == 1
    # assert 'a' in nodes_A
    assert len(nodes_A) == 2
    assert 'a' in nodes_A and 'b' in nodes_A

    nodes_B = base_nodes['cluster_B'].nodes_map
    # assert len(nodes_B) == 1
    # assert 'b' in nodes_B
    assert len(nodes_B) == 0

def test_agraph2regions_sibling_child():
    dot = '''
    digraph X {
        subgraph cluster_A {
            k -> l;
            subgraph cluster_C {
                l;
            }
        }
        subgraph cluster_B {
            k -> e;
        }
    }
    '''
    agraph = AGraph(string=dot)
    base_region = _agraph2regions(agraph)

    base_nodes = base_region.nodes_map
    nodes_A = base_nodes['cluster_A'].nodes_map
    nodes_B = base_nodes['cluster_B'].nodes_map
    nodes_C = base_nodes['cluster_A'].nodes_map['cluster_C'].nodes_map

    assert len(base_nodes) == 2
    assert len(nodes_A) == 2
    assert len(nodes_B) == 1
    assert len(nodes_C) == 1

    assert 'k' in nodes_A
    assert 'e' in nodes_B
    assert 'l' in nodes_C

def test_agraph2regions_both_sibling_children():
    dot = '''
    digraph X {
        subgraph cluster_A {
            a;
            subgraph cluster_C {
                c;
            }
        }
        subgraph cluster_B {
            a -> b;
            b;
            subgraph cluster_D {
                d;
                c -> d;
            }
        }
    }
    '''
    agraph = AGraph(string=dot)
    base_region = _agraph2regions(agraph)

    base_nodes = base_region.nodes_map
    nodes_A = base_nodes['cluster_A'].nodes_map
    nodes_B = base_nodes['cluster_B'].nodes_map
    nodes_C = base_nodes['cluster_A'].nodes_map['cluster_C'].nodes_map
    nodes_D = base_nodes['cluster_B'].nodes_map['cluster_D'].nodes_map

    assert len(base_nodes) == 2
    assert len(nodes_A) == 2
    assert len(nodes_B) == 2
    assert len(nodes_C) == 1
    assert len(nodes_D) == 1

    assert 'a' in nodes_A
    assert 'b' in nodes_B
    assert 'c' in nodes_C
    assert 'd' in nodes_D

def test_iter_sub_grid_offset_order(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    data = list(_iter_sub_grid_offsets(grid1))

    # Test sub_grid order
    assert data[0][0] == grid1
    assert data[1][0] == grid2
    assert data[2][0] == grid1_z1
    assert data[3][0] == grid1_a1
    assert data[4][0] == grid3
    assert data[5][0] == grid3_n3

def test_iter_sub_grid_offset_xy(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    data = list(_iter_sub_grid_offsets(grid1))

    # Test offset_x
    assert data[0][1] == 0
    assert data[1][1] == 1
    assert data[2][1] == 1
    assert data[3][1] == 4
    assert data[4][1] == 2
    assert data[5][1] == 3
    # Test offset_y
    assert data[0][2] == 0
    assert data[1][2] == 1
    assert data[2][2] == 8
    assert data[3][2] == 8
    assert data[4][2] == 2
    assert data[5][2] == 3

def test_iter_sub_grid_offset_depth(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    data = list(_iter_sub_grid_offsets(grid1))

    # Test depths
    assert data[0][3] == 0
    assert data[1][3] == 1
    assert data[2][3] == 1
    assert data[3][3] == 1
    assert data[4][3] == 2
    assert data[5][3] == 3

def test_create_locations_blocks(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    locs = _grids2locations(grid1)
    assert len(locs._blocks) == 6

    blocks = list(locs.iter_blocks())
    assert blocks[-1].x == 3
    assert blocks[-1].y == 3
    assert blocks[-1].depth == 3

def test_create_locations_edge_ends_coords(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    locs = _grids2locations(grid1)
    assert len(locs._edge_ends) == 8

    edge_ends = list(locs.iter_edge_ends())
    assert edge_ends[0].coords == (1,7)
    assert edge_ends[1].coords == (2,7)
    assert edge_ends[2].coords == (4,10)
    assert edge_ends[3].coords == (5,10)
    assert edge_ends[4].coords == (6,8)
    assert edge_ends[5].coords == (6,9)
    assert edge_ends[6].coords == (2,3)
    assert edge_ends[7].coords == (2,4)

def test_create_locations_edge_ends_direction(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    locs = _grids2locations(grid1)

    edge_ends = list(locs.iter_edge_ends())
    for i in range(0,4):
        assert edge_ends[i].direction == Direction.DOWN
    for i in range(4,8):
        assert edge_ends[i].direction == Direction.RIGHT

def test_create_locations_edges(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    locs = _grids2locations(grid1)
    edge_ends = list(locs.iter_edge_ends())

    assert edge_ends[2].edge_ends[0] == 1
    assert edge_ends[3].edge_ends[0] == 2
    assert edge_ends[4].edge_ends[0] == 7
    assert edge_ends[5].edge_ends[0] == 8

    assert edge_ends[0].edge_ends[0] == 3
    assert edge_ends[1].edge_ends[0] == 4
    assert edge_ends[6].edge_ends[0] == 5
    assert edge_ends[7].edge_ends[0] == 6

def test_get_color_order(colors):
    assert all(
        int(colors[i][1:3], 16) > int(colors[i+1][1:3], 16) 
        for i in range(len(colors)-1)
    )

def test_get_color_gray(colors):
    assert all(
        color[1:3] == color[3:5] and 
        color[3:5] == color[5:7]
        for color in colors
    )

def test_dot2locations():
    dot = '''
    digraph X {
        subgraph cluster_A {
            a;
            subgraph cluster_C {
                c;
            }
        }
        subgraph cluster_B {
            a -> b;
            b;
            subgraph cluster_D {
                d;
                c -> d;
            }
        }
    }
    '''

    locs = dot2locations(dot)
    assert len(locs._blocks) == 9

    blocks = list(locs.iter_blocks())
    assert blocks[0].width  == 33
    assert blocks[0].height == 13
