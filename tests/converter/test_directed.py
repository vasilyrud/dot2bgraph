import pytest

from pygraphviz import AGraph

from blockgraph.converter.directed import _sorted_subgraphs, _direct_nodes, _agraph2regions, _create_regions_nodes
from blockgraph.converter.node import Node, Region

def test_direct_nodes_child():
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
    seen_sibling_nodes = set()

    nodes_A = _direct_nodes(agraph.get_subgraph('cluster_A'), seen_sibling_nodes)
    assert len(nodes_A) == 2
    assert 'k' in nodes_A and 'l' in nodes_A

    sub_seen_sibling_nodes = set()

    nodes_B = _direct_nodes(agraph.get_subgraph('cluster_A').get_subgraph('cluster_B'), sub_seen_sibling_nodes)
    assert len(nodes_B) == 2
    assert 'e' in nodes_B and 'f' in nodes_B

def test_direct_nodes_sibling():
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
    seen_sibling_nodes = set()

    nodes_A = _direct_nodes(agraph.get_subgraph('cluster_A'), seen_sibling_nodes)
    assert len(nodes_A) == 2
    assert 'k' in nodes_A and 'l' in nodes_A

    nodes_B = _direct_nodes(agraph.get_subgraph('cluster_B'), seen_sibling_nodes)
    assert len(nodes_B) == 2
    assert 'e' in nodes_B and 'f' in nodes_B

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

    nodes_A = list(list(base_region.nodes)[0].nodes)
    assert len(anodes_to_nodes) == 2
    assert anodes_to_nodes[agraph.get_node('a')] in nodes_A
    assert anodes_to_nodes[agraph.get_node('b')] in nodes_A
    assert nodes_A[0] != nodes_A[1]

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

    base_nodes = list(base_region.nodes_iter())
    assert len(base_nodes) == 2
    assert base_nodes[0].name == 'x'
    assert base_nodes[1].name == 'cluster_A'

    nodes_A = list(base_nodes[1].nodes_iter())
    assert len(nodes_A) == 2
    assert nodes_A[0].name == 'a'
    assert nodes_A[1].name == 'cluster_B'

    nodes_B = list(nodes_A[1].nodes_iter())
    assert len(nodes_B) == 1
    assert nodes_B[0].name == 'b'

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

    base_nodes = list(base_region.nodes_iter())
    assert len(base_nodes) == 3
    assert base_nodes[0].name == 'x'
    assert base_nodes[1].name == 'cluster_A'
    assert base_nodes[2].name == 'cluster_B'

    nodes_A = list(base_nodes[1].nodes_iter())
    assert len(nodes_A) == 1
    assert nodes_A[0].name == 'a'

    nodes_B = list(base_nodes[2].nodes_iter())
    assert len(nodes_B) == 1
    assert nodes_B[0].name == 'b'
