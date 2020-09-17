import pytest

from pygraphviz import AGraph

from blockgraph.converter.directed import _sorted_subgraphs, _direct_nodes, _agraph2regions, _create_regions_nodes
from blockgraph.converter.node import Node, Region

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

def test_create_regions_nodes_child():
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
    base_region, _ = _create_regions_nodes(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 2
    assert 'x' in base_nodes and 'cluster_A' in base_nodes

    nodes_A = base_nodes['cluster_A'].nodes_map
    assert len(nodes_A) == 2
    assert 'a' in nodes_A and 'cluster_B' in nodes_A

    nodes_B = nodes_A['cluster_B'].nodes_map
    assert len(nodes_B) == 1
    assert 'b' in nodes_B

def test_create_regions_nodes_sibling():
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
    base_region, _ = _create_regions_nodes(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 3
    assert 'x' in base_nodes and 'cluster_A' in base_nodes and 'cluster_B' in base_nodes

    nodes_A = base_nodes['cluster_A'].nodes_map
    assert len(nodes_A) == 1
    assert 'a' in nodes_A

    nodes_B = base_nodes['cluster_B'].nodes_map
    assert len(nodes_B) == 1
    assert 'b' in nodes_B

def test_create_regions_nodes_child_2():
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
    base_region, _ = _create_regions_nodes(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 1
    assert 'cluster_A' in base_nodes

    nodes_A = base_nodes['cluster_A'].nodes_map
    assert len(nodes_A) == 3
    assert 'k' in nodes_A and 'l' in nodes_A and 'cluster_B' in nodes_A

    nodes_B = nodes_A['cluster_B'].nodes_map
    assert len(nodes_B) == 2
    assert 'e' in nodes_B and 'f' in nodes_B

def test_create_regions_nodes_sibling_2():
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
    base_region, _ = _create_regions_nodes(agraph)

    base_nodes = base_region.nodes_map
    assert len(base_nodes) == 2
    assert 'cluster_A' in base_nodes and 'cluster_B' in base_nodes

    nodes_A = base_nodes['cluster_A'].nodes_map
    assert len(nodes_A) == 2
    assert 'k' in nodes_A and 'l' in nodes_A

    nodes_B = base_nodes['cluster_B'].nodes_map
    assert len(nodes_B) == 2
    assert 'e' in nodes_B and 'f' in nodes_B


def test_create_regions_nodes_reverse_sibling():
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
    base_region, _ = _create_regions_nodes(agraph)

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

def test_create_regions_nodes_sibling_child():
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
    base_region, _ = _create_regions_nodes(agraph)

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

def test_create_regions_nodes_both_sibling_children():
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
    base_region, _ = _create_regions_nodes(agraph)

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
