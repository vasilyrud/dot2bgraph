import pytest

from pygraphviz import AGraph

from blockgraph.converter.directed import _sorted_subgraphs, _direct_nodes, _agraph2regions

@pytest.fixture
def agraph_child():
    X = AGraph(name='X', strict=False, directed=True)
    A = X.add_subgraph(name='cluster_A')
    A.add_node('k')
    A.add_node('l')
    A.add_edge('k', 'l')
    A.add_edge('f', 'l')
    A.add_edge('k', 'e')
    B = A.add_subgraph(name='cluster_B')
    B.add_node('e')
    B.add_node('f')
    B.add_edge('e', 'f')
    return X

@pytest.fixture
def agraph_sibling():
    X = AGraph(name='X', strict=False, directed=True)
    A = X.add_subgraph(name='cluster_A')
    A.add_node('k')
    A.add_node('l')
    A.add_edge('k', 'l')
    B = X.add_subgraph(name='cluster_B')
    B.add_node('e')
    B.add_node('f')
    B.add_edge('e', 'f')
    B.add_edge('f', 'l')
    B.add_edge('k', 'e')
    return X

@pytest.fixture
def agraph_nested():
    X = AGraph(name='X', strict=False, directed=True)
    X.add_node('a')
    X.add_node('b')
    X.add_edge('a', 'b')
    X.add_edge('b', 'k')
    X.add_edge('b', 'r')
    A = X.add_subgraph(name='cluster_A')
    A.add_node('e')
    A.add_node('f')
    A.add_edge('e', 'f')
    A.add_edge('k', 'e')
    C = A.add_subgraph(name='cluster_C')
    C.add_node('r')
    C.add_node('s')
    C.add_edge('r', 's')
    B = X.add_subgraph(name='cluster_B')
    B.add_node('k')
    B.add_node('l')
    B.add_edge('k', 'l')
    return X

def test_direct_nodes_child(agraph_child):
    seen_sibling_nodes = set()
    nodes_A = _direct_nodes(agraph_child.get_subgraph('cluster_A'), seen_sibling_nodes)
    assert len(nodes_A) == 2
    assert 'k' in nodes_A and 'l' in nodes_A

    sub_seen_sibling_nodes = set()
    nodes_B = _direct_nodes(agraph_child.get_subgraph('cluster_A').get_subgraph('cluster_B'), sub_seen_sibling_nodes)
    assert len(nodes_B) == 2
    assert 'e' in nodes_B and 'f' in nodes_B

def test_direct_nodes_sibling(agraph_sibling):
    seen_sibling_nodes = set()
    nodes_A = _direct_nodes(agraph_sibling.get_subgraph('cluster_A'), seen_sibling_nodes)
    assert len(nodes_A) == 2
    assert 'k' in nodes_A and 'l' in nodes_A

    nodes_B = _direct_nodes(agraph_sibling.get_subgraph('cluster_B'), seen_sibling_nodes)
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
