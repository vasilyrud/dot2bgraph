import pytest

from bgraph.blockgraph.locations import Locations, _Block, _EdgeEnd

def test_locations_init():
    locs = Locations()
    assert locs._blocks_id_counter == 0
    assert locs._edge_ends_id_counter == 0

def test_block_default():
    locs = Locations()
    b0 = locs.add_block()
    assert locs.block(b0).coords == (0,0)
    assert locs.block(b0).size == (1,1)

def test_edge_end_default():
    locs = Locations()
    b0 = locs.add_edge_end()
    assert locs.edge_end(b0).coords == (0,0)

def test_direction():
    dir1 = _EdgeEnd.Direction('down')
    dir2 = _EdgeEnd.Direction('down')
    dir3 = _EdgeEnd.Direction('up')

    assert dir1 == dir2
    assert dir1 != dir3
    assert dir1 == 'down'
    assert 'down' == dir1
    assert dir1 != 'up'
    assert 'up' != dir1
    assert len(set((dir1, dir2, dir3))) == 2

def test_simple_locations_graph():
    locs = Locations()

    b0 = locs.add_block(x=5)
    assert locs.block(b0).coords == (5,0)
    b1 = locs.add_block(y=8)
    assert locs.block(b1).coords == (0,8)

    e0 = locs.add_edge_end(x=5, y=1, block_id=b0, direction='down')
    assert locs.edge_end(e0).coords == (5,1)
    assert locs.edge_end(e0).direction == _EdgeEnd.Direction('down')
    assert locs.edge_end(e0) in locs.block(b0).edge_ends
    e1 = locs.add_edge_end(x=1, y=8, block_id=b1, direction='right')
    assert locs.edge_end(e1).coords == (1,8)
    assert locs.edge_end(e1) in locs.block(b1).edge_ends
    assert locs.edge_end(e1).direction == _EdgeEnd.Direction('right')

    locs.add_edge(e0, e1)
    assert locs.edge_end(e1) in locs.edge_end(e0).edge_ends
    assert locs.edge_end(e0) not in locs.edge_end(e1).edge_ends

    # print()
    # locs.print_locations()
