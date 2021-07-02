import pytest
import pathlib
import json
# import jsonschema

from blockgraph.locations import Locations, _Block, _EdgeEnd, Direction

def _make_blocks(locs: Locations):
    b0 = locs.add_block()
    b1 = locs.add_block(x=5)
    b2 = locs.add_block(y=8)
    return b0, b1, b2

def _make_edge_ends(locs: Locations):
    e0 = locs.add_edge_end(x=5, y=1, direction=Direction.DOWN)
    e1 = locs.add_edge_end(x=1, y=8, direction=Direction.RIGHT)
    return e0, e1

def _make_directions():
    dir1 = Direction.DOWN
    dir2 = Direction.DOWN
    dir3 = Direction.UP
    return dir1, dir2, dir3

def _make_complex_locations():
    locs = Locations()

    b0, b1, b2 = _make_blocks(locs)
    locs.del_block(b0)
    e0, e1 = _make_edge_ends(locs)
    locs.assign_edge_to_block(e0, b1)
    locs.assign_edge_to_block(e1, b2)
    locs.add_edge(e0, e1)

    return locs

def _reload_locs(locs):
    ''' Simulate Locations being loaded in elsewhere.
    '''
    return json.loads(
        json.dumps(locs.to_obj())
    )

@pytest.fixture
def schema():
    return json.loads(
        pathlib.Path(__file__)
            .parent
            .joinpath('../../schema')
            .joinpath('bgraph.json')
            .read_text()
    )

def test_locations_init():
    locs = Locations()
    assert locs._blocks_id_counter == 1
    assert locs._edge_ends_id_counter == 1

def test_add_block_default():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    assert locs.block(b0).coords == (0,0)
    assert locs.block(b0).size == (1,1)
    assert locs.block(b0).depth == 1

def test_add_block():
    locs = Locations()
    b0, b1, b2 = _make_blocks(locs)
    assert locs.block(b0).coords == (0,0)
    assert locs.block(b1).coords == (5,0)
    assert locs.block(b2).coords == (0,8)

def test_add_block_invalid():
    locs = Locations()
    with pytest.raises(AssertionError):
        locs.add_block(x=-1)
    with pytest.raises(AssertionError):
        locs.add_block(width=-1)

def test_block_ids():
    locs = Locations()
    b0, b1, b2 = _make_blocks(locs)
    assert b0 == 1
    assert b1 == 2
    assert b2 == 3

def test_del_block():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    assert len(locs._blocks) == 3
    locs.del_block(b0)
    assert len(locs._blocks) == 2
    b3 = locs.add_block()
    assert b3 == 4
    with pytest.raises(KeyError):
        locs.block(b0)

def test_add_edge_end_default():
    locs = Locations()
    e0 = locs.add_edge_end()
    assert locs.edge_end(e0).coords == (0,0)
    assert locs.edge_end(e0).is_source == False

def test_add_edge_end():
    locs = Locations()
    _, b1, _ = _make_blocks(locs)
    e0, _ = _make_edge_ends(locs)
    locs.assign_edge_to_block(e0, b1)
    assert locs.edge_end(e0).coords == (5,1)
    assert locs.edge_end(e0).direction == Direction.DOWN
    assert e0 in locs.block(b1).edge_ends

def test_edge_end_ids():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    assert e0 == 1
    assert e1 == 2

def test_del_edge_end():
    locs = Locations()
    e0, _ = _make_edge_ends(locs)
    assert len(locs._edge_ends) == 2
    locs.del_edge_end(e0)
    assert len(locs._edge_ends) == 1
    e2 = locs.add_edge_end()
    assert e2 == 3
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

def test_add_edge_end_invalid():
    locs = Locations()
    with pytest.raises(AssertionError):
        locs.add_edge_end(x=-1)

def test_add_edge():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    locs.add_edge(e0, e1)
    assert e1 in locs.edge_end(e0).edge_ends
    assert e0 in locs.edge_end(e1).edge_ends
    assert locs.edge_end(e0).is_source == True
    assert locs.edge_end(e1).is_source == False

def test_add_edge_disallow_both_source_and_dest():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    locs.add_edge(e0, e1)
    locs.add_edge(e0, e1)
    with pytest.raises(AssertionError):
        locs.add_edge(e1, e0)

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
    assert dir1 == Direction.DOWN
    assert Direction.DOWN == dir1
    assert dir1 != Direction.UP
    assert Direction.UP != dir1

def test_direction_hash():
    dir1, dir2, dir3 = _make_directions()
    assert len(set((dir1, dir2, dir3))) == 2

def test_locations_dimension_empty():
    locs = Locations()
    assert locs.width  == 0
    assert locs.height == 0

def test_locations_dimension_block():
    locs = Locations()
    _, _, _ = _make_blocks(locs)
    assert locs.width  == 6
    assert locs.height == 9

def test_locations_dimension_edge_end():
    locs = Locations()
    _, _ = _make_edge_ends(locs)
    assert locs.width  == 6
    assert locs.height == 9

def test_int_color():
    locs = Locations()
    b0 = locs.add_block(x=0, color='#000000')
    b1 = locs.add_block(x=1, color='#ff0000')
    b2 = locs.add_block(x=2, color='#0000ff')
    b3 = locs.add_block(x=3, color='#00ff00')
    b4 = locs.add_block(x=4, color='#ffffff')

    assert locs.block(b0).int_color == 0
    assert locs.block(b1).int_color == 16711680
    assert locs.block(b2).int_color == 255
    assert locs.block(b3).int_color == 65280
    assert locs.block(b4).int_color == 16777215

def test_locations_to_obj():
    locs = _make_complex_locations()

    assert locs.to_obj() == {
        'width': 6,
        'height': 9,
        'blocks': [
            {
                'id': 2,
                'x': 5,'y': 0,
                'width': 1,'height': 1,
                'depth': 1,
                'color': 13421772,
                'edgeEnds': [1],
            },
            {
                'id': 3,
                'x': 0,'y': 8,
                'width': 1,'height': 1,
                'depth': 1,
                'color': 13421772,
                'edgeEnds': [2],
            },
        ],
        'edgeEnds': [
            {
                'id': 1,
                'x': 5,'y': 1,
                'direction': 'down',
                'isSource': True,
                'edgeEnds': [2],
            },
            {
                'id': 2,
                'x': 1,'y': 8,
                'direction': 'right',
                'isSource': False,
                'edgeEnds': [1],
            },
        ],
    }

# def test_locations_empty_schema(schema):
#     locs = Locations()
#     jsonschema.validate(instance=_reload_locs(locs), schema=schema)

# def test_locations_schema(schema):
#     locs = _make_complex_locations()
#     jsonschema.validate(instance=_reload_locs(locs), schema=schema)