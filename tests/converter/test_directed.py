import os
import pytest

from pygraphviz import AGraph

from dot2bgraph.converter.directed import (
    _sorted_subgraphs, _direct_nodes, _direct_edges,
    _create_regions_nodes, _create_edges, _agraph2regions,
    _iter_sub_grid_offsets, _grids2locations,
    _get_color, dot2locations, _populate_subgraph,
    _recursive_agraph, dots2locations,
)
from dot2bgraph.converter.node import Node, Region
from dot2bgraph.converter.grid import GridRows
from dot2bgraph.locations import Direction

# Prevent spinners from printing during tests
import dot2bgraph.utils.spinner
dot2bgraph.utils.spinner._SPINNER_DISABLE = True

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

    grid1 = GridRows(r1, 1, 1)

    grid1_a1 = GridRows(a1, 1, 1)
    grid1.add_sub_grid(grid1_a1, x=1, y=1)

    grid1_z1 = GridRows(z1, 1, 1)
    grid1.add_sub_grid(grid1_z1, x=0, y=1)

    grid2 = GridRows(r2, 1, 1)
    grid1.add_sub_grid(grid2, x=0, y=0)

    grid3 = GridRows(r3, 1, 1)
    grid2.add_sub_grid(grid3, x=0, y=0)

    grid3_n3 = GridRows(n3, 1, 1)
    grid3.add_sub_grid(grid3_n3, x=0, y=0)

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
    base_region, anodes_to_nodes, _ = _create_regions_nodes(agraph)

    nodes_A = base_region.nodes_map['cluster_A'].nodes_map
    assert len(anodes_to_nodes) == 2
    assert anodes_to_nodes[agraph.get_node('a')] in nodes_A.values()
    assert anodes_to_nodes[agraph.get_node('b')] in nodes_A.values()
    assert nodes_A['a'] != nodes_A['b']

def test_labels_none():
    dot = '''
    digraph X {
        subgraph cluster_A {
            a;
        }
    }
    '''
    agraph = AGraph(string=dot)
    _, _, node_labels = _create_regions_nodes(agraph)

    assert len(node_labels) == 0

def test_labels_nodes():
    dot = '''
    digraph X {
        a;
        subgraph cluster_B {
            b [label="label_b"];
        }
        subgraph cluster_C {
            label="label_C";
            c;
        }
    }
    '''
    agraph = AGraph(string=dot)
    _, _, node_labels = _create_regions_nodes(agraph)

    assert len(node_labels) == 2

    labels = sorted(node_labels.values())
    assert labels[0] == 'label_C'
    assert labels[1] == 'label_b'

def test_labels_nodes_inherited():
    ''' This is a strange behavior inherent to
    graphviz.
    '''

    dot = '''
    digraph X {
        label="label_X";
        a;
        subgraph cluster_B {
            b;
        }
        subgraph cluster_C {
            label="label_C";
            c;
        }
    }
    '''
    agraph = AGraph(string=dot)
    _, _, node_labels = _create_regions_nodes(agraph)

    assert len(node_labels) == 3

    labels = sorted(node_labels.values())
    assert labels[0] == 'label_C'
    assert labels[1] == 'label_X'
    assert labels[2] == 'label_X'

def test_labels_edges():
    dot = '''
    digraph X {
        c -> b;
        subgraph cluster_A {
            a -> b [label="label_ab"];
        }
    }
    '''
    agraph = AGraph(string=dot)
    _, anodes_to_nodes, _ = _create_regions_nodes(agraph)
    edge_labels = _create_edges(agraph, anodes_to_nodes)

    assert len(edge_labels) == 1
    assert list(edge_labels.keys())[0][0].name == 'a'
    assert list(edge_labels.keys())[0][1].name == 'b'
    assert list(edge_labels.values())[0] == 'label_ab'

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

def test_direct_edges():
    dot = '''
    digraph X {
        subgraph cluster_A {
            a;
        }
        subgraph cluster_C {
            c;
            a -> c;
            c -> b;
            subgraph cluster_B {
                b -> a;
            }
        }
    }
    '''
    agraph = AGraph(string=dot)

    cluster_A = agraph.get_subgraph('cluster_A')
    assert _direct_edges(cluster_A, set()) == set()

    cluster_C = agraph.get_subgraph('cluster_C')
    assert _direct_edges(cluster_C, set()) == {('a', 'c'), ('c', 'b')}

    cluster_B = cluster_C.get_subgraph('cluster_B')
    assert _direct_edges(cluster_B, set()) == {('b', 'a')}

def test_agraph2regions_empty():
    dot = '''
    digraph X {
    }
    '''
    agraph = AGraph(string=dot)
    base_region, _, _ = _agraph2regions(agraph)

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
    base_region, _, _ = _agraph2regions(agraph)

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
    base_region, _, _ = _agraph2regions(agraph)

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
    base_region, _, _ = _agraph2regions(agraph)

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
    base_region, _, _ = _agraph2regions(agraph)

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
    base_region, _, _ = _agraph2regions(agraph)

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
    base_region, _, _ = _agraph2regions(agraph)

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
    base_region, _, _ = _agraph2regions(agraph)

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

    locs = _grids2locations(grid1, {}, {})
    assert len(locs._blocks) == 6

    blocks = list(locs.iter_blocks())
    assert blocks[-1].x == 3
    assert blocks[-1].y == 3
    assert blocks[-1].depth == 3
    assert blocks[-1].label == None

def test_create_locations_labels(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    locs = _grids2locations(grid1, {
        grid1.node: 'label1',
        grid1_a1.node: 'label1_a1',
    }, {})

    assert locs.block(0).label == 'label1'
    assert locs.block(1).label == None
    assert locs.block(2).label == None
    assert locs.block(3).label == 'label1_a1'
    assert locs.block(4).label == None
    assert locs.block(5).label == None

def test_create_locations_edge_ends_coords(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    locs = _grids2locations(grid1, {}, {})
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

    locs = _grids2locations(grid1, {}, {})

    edge_ends = list(locs.iter_edge_ends())
    for i in range(0,4):
        assert edge_ends[i].direction == Direction.DOWN
    for i in range(4,8):
        assert edge_ends[i].direction == Direction.RIGHT

def test_create_locations_edges(grids):
    grid1, grid1_a1, grid1_z1, grid2, grid3, grid3_n3 = grids

    locs = _grids2locations(grid1, {}, {(grid1_a1.node,grid3_n3.node): 'label_a1n3'})
    edge_ends = list(locs.iter_edge_ends())

    assert edge_ends[2].edge_ends[0] == 0
    assert edge_ends[3].edge_ends[0] == 1
    assert edge_ends[4].edge_ends[0] == 6
    assert edge_ends[5].edge_ends[0] == 7

    assert edge_ends[0].edge_ends[0] == 2
    assert edge_ends[1].edge_ends[0] == 3
    assert edge_ends[6].edge_ends[0] == 4
    assert edge_ends[7].edge_ends[0] == 5

    for i in range(0,4):
        assert locs.edge_end(i).label is None
    for i in range(4,8):
        assert locs.edge_end(i).label == 'label_a1n3'

def test_edge_end_order():
    r0 = Region('r0')
    r1 = Region('r1', r0)
    a1 = Node('a1', r1)
    b1 = Node('b1', r1)
    c1 = Node('c1', r1)
    r2 = Region('r2', r0)
    x2 = Node('x2', r2)
    y2 = Node('y2', r2)

    a1.add_edge(b1)
    a1.add_edge(c1)
    a1.add_edge(x2)
    a1.add_edge(y2)

    i, o = 1, 3
    grid0 = GridRows(r0, i, o)

    grid1 = GridRows(r1, i, o)
    grid0.add_sub_grid(grid1, x=0, y=0)

    grid1_a1 = GridRows(a1, i, o)
    grid1.add_sub_grid(grid1_a1, x=0, y=0)

    grid1_b1 = GridRows(b1, i, o)
    grid1.add_sub_grid(grid1_b1, x=2, y=1)

    grid1_c1 = GridRows(c1, i, o)
    grid1.add_sub_grid(grid1_c1, x=1, y=1)

    grid2 = GridRows(r2, i, o)
    grid0.add_sub_grid(grid2, x=1, y=0)

    grid2_x2 = GridRows(x2, i, o)
    grid2.add_sub_grid(grid2_x2, x=0, y=2)

    grid2_y2 = GridRows(y2, i, o)
    grid2.add_sub_grid(grid2_y2, x=0, y=1)

    locs = _grids2locations(grid0, {}, {})

    edge_ends = list(locs.iter_edge_ends())

    assert edge_ends[0].coords == (3,4)
    assert edge_ends[1].coords == (4,4)
    assert edge_ends[2].coords == (5,2)
    assert edge_ends[3].coords == (5,3)

    assert edge_ends[0].edge_ends[0] == 4
    assert edge_ends[1].edge_ends[0] == 5
    assert edge_ends[2].edge_ends[0] == 6
    assert edge_ends[3].edge_ends[0] == 7

def test_get_color_order(colors):
    assert all(
        colors[i][0] > colors[i+1][0] and 
        colors[i][1] > colors[i+1][1] and 
        colors[i][2] > colors[i+1][2]
        for i in range(len(colors)-1)
    )

def test_get_color_gray(colors):
    assert all(
        color[0] == color[1] and 
        color[1] == color[2]
        for color in colors
    )

def test_dot2locations_dir_input(tmp_path):
    dir = tmp_path/'dir'
    os.mkdir(dir)

    with pytest.raises(AssertionError):
        dot2locations(dir)

def test_dot2locations(tmp_path):
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

    dotfile = tmp_path/'test.dot'
    dotfile.write_text(dot)

    locs = dot2locations(dotfile)
    assert len(locs._blocks) == 9

    blocks = list(locs.iter_blocks())
    assert blocks[0].width  == 17
    assert blocks[0].height == 25

def test_dot2locations_empty(tmp_path):
    dot = '''
    digraph X {
    }
    '''

    dotfile = tmp_path/'test.dot'
    dotfile.write_text(dot)

    locs = dot2locations(dotfile)
    assert len(locs._blocks) == 1

    blocks = list(locs.iter_blocks())
    assert blocks[0].width  == 1
    assert blocks[0].height == 1

def test_populate_subgraph_labels():
    dot = '''
    digraph X {
        label="label_X";
        subgraph cluster_A {
            label="label_A";
            a [label="label_a"];
        }
        b;
        a -> b [label="label_ab"];
        b -> a;
    }
    '''
    original_subgraph = AGraph(string=dot)
    new_subgraph = AGraph(strict=False, directed=True, name='test', label='test_label')

    _populate_subgraph(new_subgraph, original_subgraph, 'test')

    assert new_subgraph.graph_attr['label'] == 'test_label'
    sub_A = new_subgraph.get_subgraph('test:cluster_A')
    assert sub_A.graph_attr['label'] == 'label_A'

    node_a = sub_A.get_node('test:a')
    assert node_a.attr['label'] == 'label_a'
    node_b = new_subgraph.get_node('test:b')
    assert node_b.attr['label'] == '\\N'

    edge_ab = new_subgraph.get_edge('test:a', 'test:b')
    assert edge_ab.attr['label'] == 'label_ab'
    edge_ba = new_subgraph.get_edge('test:b', 'test:a')
    assert edge_ba.attr['label'] == ''

def test_recursive_agraph_file_input(tmp_path):
    ex = tmp_path/'ex.dot'
    ex.write_text('digraph G { A; }')

    with pytest.raises(AssertionError):
        _recursive_agraph(ex)

def test_recursive_agraph_dir_single_file(tmp_path):
    dir = tmp_path/'dir'
    os.mkdir(dir)

    ex = dir/'ex.dot'
    ex.write_text('digraph G { A; }')

    agraph = _recursive_agraph(dir.resolve())
    assert agraph.name == 'dir'
    assert agraph.get_subgraph('dir/ex.dot') is not None
    assert agraph.has_node('dir/ex.dot:A')

def test_recursive_agraph_dir_parallel(tmp_path):
    dir = tmp_path/'dir'
    os.mkdir(dir)

    dot = '''
    digraph G {
        subgraph subA {
            A;
            A -> B;
            subgraph subB {
                B;
            }
        }
    }
    '''
    ex1 = dir/'ex1.dot'
    ex1.write_text(dot)
    ex2 = dir/'ex2.dot'
    ex2.write_text(dot)

    agraph = _recursive_agraph(dir)
    assert agraph.name == 'dir'

    exsub1 = agraph.get_subgraph('dir/ex1.dot')
    assert exsub1 is not None
    exsub1A = exsub1.get_subgraph('dir/ex1.dot:subA')
    assert exsub1A is not None
    exsub1B = exsub1A.get_subgraph('dir/ex1.dot:subB')
    assert exsub1B is not None

    exsub2 = agraph.get_subgraph('dir/ex2.dot')
    assert exsub2 is not None
    exsub2A = exsub2.get_subgraph('dir/ex2.dot:subA')
    assert exsub2A is not None
    exsub2B = exsub2A.get_subgraph('dir/ex2.dot:subB')
    assert exsub2B is not None

    assert agraph.has_node('dir/ex1.dot:A')
    assert agraph.has_node('dir/ex1.dot:B')
    assert agraph.has_edge('dir/ex1.dot:A', 'dir/ex1.dot:B')
    assert _direct_nodes(exsub1A, set()) == {'dir/ex1.dot:A'}
    assert _direct_nodes(exsub1B, set()) == {'dir/ex1.dot:B'}

    assert agraph.has_node('dir/ex2.dot:A')
    assert agraph.has_node('dir/ex2.dot:B')
    assert agraph.has_edge('dir/ex2.dot:A', 'dir/ex2.dot:B')
    assert _direct_nodes(exsub2A, set()) == {'dir/ex2.dot:A'}
    assert _direct_nodes(exsub2B, set()) == {'dir/ex2.dot:B'}

    assert not agraph.has_edge('dir/ex1.dot:A', 'dir/ex2.dot:B')
    assert not agraph.has_edge('dir/ex2.dot:A', 'dir/ex1.dot:B')

def test_recursive_agraph_same_in_subdir(tmp_path):
    dir = tmp_path/'dir'
    os.mkdir(dir)
    subdir = dir/'dir'
    os.mkdir(subdir)

    ex1 = dir/'ex.dot'
    ex1.write_text('digraph G { A; }')
    ex2 = subdir/'ex.dot'
    ex2.write_text('digraph G { A; }')

    agraph = _recursive_agraph(dir)
    assert agraph.name == 'dir'

    exsub1 = agraph.get_subgraph('dir/ex.dot')
    assert exsub1 is not None
    exsubdir = agraph.get_subgraph('dir/dir')
    assert exsubdir is not None
    exsub3 = exsubdir.get_subgraph('dir/dir/ex.dot')
    assert exsub3 is not None

    assert agraph.has_node('dir/ex.dot:A')
    assert agraph.has_node('dir/dir/ex.dot:A')

def test_recursive_agraph_same_in_subdirs(tmp_path):
    dir = tmp_path/'dir'
    os.mkdir(dir)
    sub1 = dir/'sub1'
    os.mkdir(sub1)
    subdir1 = sub1/'dir'
    os.mkdir(subdir1)
    sub2 = dir/'sub2'
    os.mkdir(sub2)
    subdir2 = sub2/'dir'
    os.mkdir(subdir2)

    ex1 = subdir1/'ex.dot'
    ex1.write_text('digraph G { A; }')
    ex2 = subdir2/'ex.dot'
    ex2.write_text('digraph G { A; }')

    agraph = _recursive_agraph(dir)
    assert agraph.name == 'dir'

    exsub1 = agraph.get_subgraph('dir/sub1')
    assert exsub1 is not None
    exsubdir1 = exsub1.get_subgraph('dir/sub1/dir')
    assert exsubdir1 is not None
    ex1 = exsubdir1.get_subgraph('dir/sub1/dir/ex.dot')
    assert ex1 is not None

    exsub2 = agraph.get_subgraph('dir/sub2')
    assert exsub2 is not None
    exsubdir2 = exsub2.get_subgraph('dir/sub2/dir')
    assert exsubdir2 is not None
    ex2 = exsubdir2.get_subgraph('dir/sub2/dir/ex.dot')
    assert ex2 is not None

    assert agraph.has_node('dir/sub1/dir/ex.dot:A')
    assert agraph.has_node('dir/sub2/dir/ex.dot:A')

def test_dots2locations(tmp_path):
    dir = tmp_path/'dir'
    os.mkdir(dir)

    ex = dir/'ex.dot'
    ex.write_text('digraph G { A; }')

    locs = dots2locations(dir)
    assert len(locs._blocks) == 3

    blocks = list(locs.iter_blocks())
    assert blocks[0].width  == 9
    assert blocks[0].height == 9
