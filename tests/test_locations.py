import pytest

from bgraph.blockgraph.locations import Locations, _Block, _EdgeEnd, _Direction

def _make_blocks(locs: Locations):
    b0 = locs.add_block()
    b1 = locs.add_block(x=5)
    b2 = locs.add_block(y=8)
    return b0, b1, b2

def _make_edge_ends(locs: Locations):
    e0 = locs.add_edge_end(x=5, y=1, direction='down')
    e1 = locs.add_edge_end(x=1, y=8, direction='right')
    return e0, e1

def _make_directions():
    dir1 = _Direction('down')
    dir2 = _Direction('down')
    dir3 = _Direction('up')
    return dir1, dir2, dir3

def test_locations_init():
    locs = Locations()
    assert locs._blocks_id_counter == 0
    assert locs._edge_ends_id_counter == 0

def test_add_block_default():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    assert locs.block(b0).coords == (0,0)
    assert locs.block(b0).size == (1,1)

def test_add_block():
    locs = Locations()
    b0, b1, b2 = _make_blocks(locs)
    assert locs.block(b0).coords == (0,0)
    assert locs.block(b1).coords == (5,0)
    assert locs.block(b2).coords == (0,8)

def test_block_ids():
    locs = Locations()
    b0, b1, b2 = _make_blocks(locs)
    assert b0 == 0
    assert b1 == 1
    assert b2 == 2

def test_del_block():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    assert len(locs._blocks) == 3
    locs.del_block(b0)
    assert len(locs._blocks) == 2
    b3 = locs.add_block()
    assert b3 == 3
    with pytest.raises(KeyError):
        locs.block(b0)

def test_add_edge_end_default():
    locs = Locations()
    b0 = locs.add_edge_end()
    assert locs.edge_end(b0).coords == (0,0)

def test_add_edge_end():
    locs = Locations()
    _, b1, _ = _make_blocks(locs)
    e0, _ = _make_edge_ends(locs)
    locs.assign_edge_to_block(e0, b1)
    assert locs.edge_end(e0).coords == (5,1)
    assert locs.edge_end(e0).direction == 'down'
    assert e0 in locs.block(b1).edge_ends

def test_edge_end_ids():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    assert e0 == 0
    assert e1 == 1

def test_del_edge_end():
    locs = Locations()
    e0, _ = _make_edge_ends(locs)
    assert len(locs._edge_ends) == 2
    locs.del_edge_end(e0)
    assert len(locs._edge_ends) == 1
    e2 = locs.add_edge_end()
    assert e2 == 2
    with pytest.raises(KeyError):
        locs.edge_end(e0)

def test_add_edge_end_with_block():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    e0 = locs.add_edge_end(block_id=b0)
    assert e0 in locs.block(b0).edge_ends

def test_del_edge_end_from_block():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    e0 = locs.add_edge_end(block_id=b0)
    locs.del_edge_end_from_block(e0, b0)
    assert e0 not in locs.block(b0).edge_ends
    with pytest.raises(KeyError):
        locs.block(b0)._del_edge_end(locs.edge_end(e0))

def test_add_edge():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    locs.add_edge(e0, e1)
    assert e1 in locs.edge_end(e0).edge_ends
    assert e0 not in locs.edge_end(e1).edge_ends

def test_add_many_edges():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    locs.add_edge(e0, e1)
    locs.add_edge(e0, e1)
    assert e1 in locs.edge_end(e0).edge_ends
    assert len(locs.edge_end(e0).edge_ends) == 2
    assert locs.edge_end(e0).edge_ends[0] == e1
    assert locs.edge_end(e0).edge_ends[1] == e1

def test_del_edges():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    e2 = locs.add_edge_end()
    locs.add_edge(e0, e1)
    locs.add_edge(e0, e1)
    locs.add_edge(e0, e2)
    num_deleted = locs.del_edges(e0, e1)
    assert num_deleted == 2
    assert e1 not in locs.edge_end(e0).edge_ends
    assert len(locs.edge_end(e0).edge_ends) == 1
    assert locs.edge_end(e0).edge_ends[0] == e2
    with pytest.raises(KeyError):
        locs.edge_end(e0)._del_edge_ends(locs.edge_end(e1))

def test_direction_eq():
    dir1, dir2, dir3 = _make_directions()
    assert dir1 == dir2
    assert dir1 != dir3
    assert dir1 == 'down'
    assert 'down' == dir1
    assert dir1 != 'up'
    assert 'up' != dir1

def test_direction_hash():
    dir1, dir2, dir3 = _make_directions()
    assert len(set((dir1, dir2, dir3))) == 2

def test_locations_to_obj():
    locs = Locations()

    b0, b1, b2 = _make_blocks(locs)
    locs.del_block(b0)
    e0, e1 = _make_edge_ends(locs)
    locs.assign_edge_to_block(e0, b1)
    locs.assign_edge_to_block(e1, b2)
    locs.add_edge(e0, e1)

    # print()
    # locs.print_locations()

    assert locs.to_obj() == {
        'blocks': {
            1: {
                'x': 5,'y': 0,
                'width': 1,'height': 1,
                'depth': 0,
                'color': '#cccccc',
                'shape': 'box',
                'edge_ends': [0],
            },
            2: {
                'x': 0,'y': 8,
                'width': 1,'height': 1,
                'depth': 0,
                'color': '#cccccc',
                'shape': 'box',
                'edge_ends': [1],
            },
        },
        'edge_ends': {
            0: {
                'x': 5,'y': 1,
                'direction': 'down',
                'edge_ends': [1],
            },
            1: {
                'x': 1,'y': 8,
                'direction': 'right',
                'edge_ends': [],
            },
        },
    }
