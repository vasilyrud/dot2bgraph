import pytest
import pathlib
import json
# import jsonschema

from dot2bgraph.locations import Locations, _Block, _EdgeEnd, Direction

def _make_blocks(locs: Locations):
    b0 = locs.add_block()
    b1 = locs.add_block(x=5)
    b2 = locs.add_block(y=8, label='block_label')
    return b0, b1, b2

def _make_edge_ends(locs: Locations):
    e0 = locs.add_edge_end(x=5, y=1, direction=Direction.DOWN)
    e1 = locs.add_edge_end(x=1, y=8, direction=Direction.RIGHT, label='ee_label')
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

def test_locations_init_default():
    locs = Locations()
    assert locs._blocks_id_counter == 0
    assert locs._edge_ends_id_counter == 0

    assert locs.bg_color == (255,255,255)
    assert locs.highlight_bg_color == (255,255,255)
    assert locs.highlight_fg_color == (0,0,0)

def test_locations_init():
    locs = Locations((0,0,1), (0,0,2), (255,255,243))
    assert locs._blocks_id_counter == 0
    assert locs._edge_ends_id_counter == 0

    assert locs.bg_color == (0,0,1)
    assert locs.highlight_bg_color == (0,0,2)
    assert locs.highlight_fg_color == (255,255,243)

def test_add_block_default():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    assert locs.block(b0).coords == (0,0)
    assert locs.block(b0).size == (1,1)
    assert locs.block(b0).depth == 0
    assert locs.block(b0).color == (204,204,204)
    assert len(locs.block(b0).edge_ends) == 0

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

def test_add_block_label():
    locs = Locations()
    b0, _, b2 = _make_blocks(locs)
    assert locs.block(b0).label is None
    assert locs.block(b2).label == 'block_label'

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
    e0 = locs.add_edge_end()
    assert locs.edge_end(e0).coords == (0,0)
    assert locs.edge_end(e0).color == (0,0,0)
    assert locs.edge_end(e0).is_source == False
    assert locs.edge_end(e0).direction == Direction.UP
    assert locs.edge_end(e0).block_id == None

def test_add_edge_end():
    locs = Locations()
    _, b1, _ = _make_blocks(locs)
    e0, _ = _make_edge_ends(locs)
    locs.assign_edge_to_block(e0, b1)
    assert locs.edge_end(e0).coords == (5,1)
    assert locs.edge_end(e0).direction == Direction.DOWN
    assert e0 in locs.block(b1).edge_ends
    assert b1 == locs.edge_end(e0).block_id

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
    assert b0 == locs.edge_end(e0).block_id

def test_del_edge_end_with_block():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    e0 = locs.add_edge_end(block_id=b0)
    locs.del_edge_end(e0)
    assert e0 not in locs.block(b0).edge_ends
    with pytest.raises(KeyError):
        locs.block(b0)._del_edge_end(locs.edge_end(e0))

def test_add_edge_end_label():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    assert locs.edge_end(e0).label is None
    assert locs.edge_end(e1).label == 'ee_label'

def test_del_edge_end_with_edge():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    e0 = locs.add_edge_end(block_id=b0)
    e1 = locs.add_edge_end(block_id=b0)
    locs.add_edge(e0, e1)
    locs.del_edge_end(e0)
    assert e0 not in locs.block(b0).edge_ends
    assert e0 not in locs.edge_end(e1).edge_ends
    assert e1 in locs.block(b0).edge_ends
    assert b0 == locs.edge_end(e1).block_id

def test_del_block_with_edge_end():
    locs = Locations()
    b0, _, _ = _make_blocks(locs)
    e0 = locs.add_edge_end(block_id=b0)
    locs.del_block(b0)
    assert locs.edge_end(e0).block_id is None

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
    with pytest.raises(AssertionError):
        locs.add_edge(e1, e0)

def test_del_edge():
    locs = Locations()
    e0, e1 = _make_edge_ends(locs)
    e2 = locs.add_edge_end()
    locs.add_edge(e0, e1)
    locs.add_edge(e0, e2)

    locs.del_edge(e0, e1)
    assert e1 not in locs.edge_end(e0).edge_ends
    with pytest.raises(KeyError):
        locs.edge_end(e0)._del_edge_end(locs.edge_end(e1))

    assert e2 in locs.edge_end(e0).edge_ends
    assert e0 in locs.edge_end(e2).edge_ends
    assert len(locs.edge_end(e0).edge_ends) == 1
    assert len(locs.edge_end(e2).edge_ends) == 1

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

def test_locations_to_obj():
    locs = _make_complex_locations()

    assert locs.to_obj() == {
        'width': 6,
        'height': 9,
        'bgColor': 16777215,
        'highlightBgColor': 16777215,
        'highlightFgColor': 0,
        'blocks': [
            {
                'id': 1,
                'x': 5,'y': 0,
                'width': 1,'height': 1,
                'depth': 0,
                'color': 13421772,
                'edgeEnds': [0],
            },
            {
                'id': 2,
                'x': 0,'y': 8,
                'width': 1,'height': 1,
                'depth': 0,
                'color': 13421772,
                'edgeEnds': [1],
                'label': 'block_label',
            },
        ],
        'edgeEnds': [
            {
                'id': 0,
                'x': 5,'y': 1,
                'color': 0,
                'direction': 3,
                'isSource': True,
                'block': 1,
                'edgeEnds': [1],
            },
            {
                'id': 1,
                'x': 1,'y': 8,
                'color': 0,
                'direction': 2,
                'isSource': False,
                'block': 2,
                'edgeEnds': [0],
                'label': 'ee_label',
            },
        ],
    }

# def test_locations_empty_schema(schema):
#     locs = Locations()
#     jsonschema.validate(instance=_reload_locs(locs), schema=schema)

# def test_locations_schema(schema):
#     locs = _make_complex_locations()
#     jsonschema.validate(instance=_reload_locs(locs), schema=schema)
