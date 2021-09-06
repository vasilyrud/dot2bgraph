import pytest

from blockgraph.converter.pack import (
    Rectangle, pack_rectangles,
    _do_pack, _square_bin_bounds,
    _bin_binary_search,
)

def test_do_pack_empty():
    assert _do_pack((0,0), []) == []
    assert _do_pack((1,1), []) == []

def test_do_pack_zero_bin():
    assert _do_pack((0,0), []) == []
    assert _do_pack((0,0), [(1,1)]) == []
    assert _do_pack((0,1), [(1,1)]) == []
    assert _do_pack((1,0), [(1,1)]) == []

def test_do_pack_zero_rect():
    with pytest.raises(AssertionError):
        _do_pack((1,1), [(0,0)])
    with pytest.raises(AssertionError):
        _do_pack((1,1), [(0,1)])
    with pytest.raises(AssertionError):
        _do_pack((1,1), [(1,0)])

def test_do_pack_same_order():
    for rects in [
        [(1,1),(1,2),(2,1)],
        [(1,2),(2,1),(1,1)],
        [(1,2),(1,1),(2,1)],
    ]:
        assert _do_pack((10,10), rects) == [
            (0, 0, 0, 1, 2, None),
            (0, 1, 0, 2, 1, None),
            (0, 3, 0, 1, 1, None),
        ]

def test_do_pack_different_order():
    for _ in range(10):
        assert _do_pack((10,10), [(2,1),(1,1),(1,2)]) == [
            (0, 0, 0, 2, 1, None),
            (0, 2, 0, 1, 2, None),
            (0, 0, 1, 1, 1, None),
        ]

def test_square_bin_bounds_single_rect_x():
    assert _square_bin_bounds([
        Rectangle(10,1,None),
    ]) == (10, None, [
        (0, 0, 0, 10, 1, None)
    ])

def test_square_bin_bounds_single_rect_y():
    assert _square_bin_bounds([
        Rectangle(1,10,None),
    ]) == (10, None, [
        (0, 0, 0, 1, 10, None)
    ])

def test_square_bin_bounds_several_rect_no_fit():
    assert _square_bin_bounds([
        Rectangle(10,2,None),
        Rectangle(10,2,None),
        Rectangle(10,2,None),
    ]) == (10, None, [
        (0, 0, 0, 10, 2, None),
        (0, 0, 2, 10, 2, None),
        (0, 0, 4, 10, 2, None),
    ])

def test_square_bin_bounds_several_rect_better_fit():
    assert _square_bin_bounds([
        Rectangle(3,3,None),
        Rectangle(4,4,None),
    ]) == (8, 4, [
        (0, 0, 0, 4, 4, None),
        (0, 4, 0, 3, 3, None),
    ])

def test_square_bin_bounds_many_rect():
    fit, no_fit, rects = _square_bin_bounds([
        Rectangle(2,2,None) for _ in range(100)
    ])
    assert fit == 32
    assert no_fit == 16
    assert len(rects) == 100

def test_square_bin_binary_search_input_none():
    with pytest.raises(AssertionError):
        _bin_binary_search([Rectangle(1,1,None)], None, 5, True, True)
    with pytest.raises(AssertionError):
        _bin_binary_search([Rectangle(1,1,None)], 5, None, True, True)

def test_square_bin_binary_search_non_fit_mismatch():
    with pytest.raises(AssertionError):
        _bin_binary_search([Rectangle(1,1,None)], 5, 5, True, True)
    with pytest.raises(AssertionError):
        _bin_binary_search([Rectangle(1,1,None)], 6, 5, True, True)

def test_square_bin_binary_search_empty_rects():
    assert _bin_binary_search([], 2, 20, True, True) == (3, [])

def test_square_bin_binary_search_single_rect():
    assert _bin_binary_search([
        Rectangle(1,10,None),
    ], 2, 20, True, True) == (10, [
        (0, 0, 0, 1, 10, None),
    ])

def test_square_bin_binary_search_no_better_fit():
    assert _bin_binary_search([
        Rectangle(2,2,None),
        Rectangle(2,2,None),
    ], 1, 4, True, True) == (4, [
        (0, 0, 0, 2, 2, None),
        (0, 2, 0, 2, 2, None),
    ])

def test_square_bin_binary_search_close_fit_non_fit():
    for non_fit, fit in [
        (3, 4), (2, 4), (1, 4), (0, 4),
        (3, 5), (2, 5), (1, 5), (0, 5),
        (3, 6), (2, 6), (1, 6), (0, 6),
    ]:
        assert _bin_binary_search([
            Rectangle(2,2,None),
            Rectangle(2,2,None),
        ], non_fit, fit, True, True) == (4, [
            (0, 0, 0, 2, 2, None),
            (0, 2, 0, 2, 2, None),
        ])

def test_square_bin_binary_search_many():
    for non_fit, fit in [
        (16,   32),
        (19,   21),
        (16,   21),
        (15,   21),
        ( 0,   21),
        ( 0,   20),
        ( 0, 1000),
        (19, 1000),
        (19, 1001),
    ]:
        bin, rects = _bin_binary_search([
            Rectangle(2,2,None) for _ in range(100)
        ], non_fit, fit, True, True)
        assert bin == 20
        assert len(rects) == 100

def test_width_bin_binary_search_many():
    for fit, expected_bin, expected_last in [
        (  32, 14, (0, 12,  24, 2, 2, None)),
        (  21, 20, (0, 18,  18, 2, 2, None)),
        (  20, 20, (0, 18,  18, 2, 2, None)),
        (1000,  2, (0,  0, 198, 2, 2, None)),
        (1001,  2, (0,  0, 198, 2, 2, None)),
    ]:
        bin, rects = _bin_binary_search([
            Rectangle(2,2,None) for _ in range(100)
        ], 0, fit, True, False)

        assert bin == expected_bin
        assert len(rects) == 100
        assert rects[-1] == expected_last

def test_height_bin_binary_search_many():
    for fit, expected_bin, expected_last in [
        (  32, 14, (0,  30,  6, 2, 2, None)),
        (  21, 20, (0,  18, 18, 2, 2, None)),
        (  20, 20, (0,  18, 18, 2, 2, None)),
        (1000,  2, (0, 198,  0, 2, 2, None)),
        (1001,  2, (0, 198,  0, 2, 2, None)),
    ]:
        bin, rects = _bin_binary_search([
            Rectangle(2,2,None) for _ in range(100)
        ], 0, fit, False, True)

        assert bin == expected_bin
        assert len(rects) == 100
        assert rects[-1] == expected_last

def test_pack_rectangles_empty():
    assert pack_rectangles([]) == (0, 0, [])

def test_pack_rectangles_single_rect():
    assert pack_rectangles([
        Rectangle(10,10,None),
    ]) == (10, 10, [
        (0, 0, 0, 10, 10, None)
    ])

def test_pack_rectangles_several_rect_better_fit():
    assert pack_rectangles([
        Rectangle(3,3,None),
        Rectangle(4,4,None),
    ]) == (7, 4, [
        (0, 0, 0, 4, 4, None),
        (0, 4, 0, 3, 3, None),
    ])

def test_pack_rectangles_width_fit_single():
    assert pack_rectangles([
        Rectangle(1,3,None),
    ]) == (1, 3, [
        (0, 0, 0, 1, 3, None),
    ])

def test_pack_rectangles_width_fit():
    assert pack_rectangles([
        Rectangle(1,3,None),
        Rectangle(1,3,None),
    ]) == (2, 3, [
        (0, 0, 0, 1, 3, None),
        (0, 1, 0, 1, 3, None),
    ])

def test_pack_rectangles_height_fit_single():
    assert pack_rectangles([
        Rectangle(3,1,None),
    ]) == (3, 1, [
        (0, 0, 0, 3, 1, None),
    ])

def test_pack_rectangles_height_fit():
    assert pack_rectangles([
        Rectangle(3,1,None),
        Rectangle(3,1,None),
    ]) == (3, 2, [
        (0, 0, 0, 3, 1, None),
        (0, 0, 1, 3, 1, None),
    ])

def test_pack_rectangles_many_rects():
    w, h, rects = pack_rectangles([
        Rectangle(20 // (i+1), i + 20, str(i)) for i in range(20)
    ])

    assert w == 46
    assert h == 43
    assert len(rects) == 20
