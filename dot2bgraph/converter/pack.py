# Copyright 2021 Vasily Rudchenko - dot2bgraph
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
from typing import List, Tuple, Optional
from collections import namedtuple

from rectpack import newPacker

Rectangle = namedtuple('Rectangle', ['w', 'h', 'rid'])
Packed = namedtuple('Packed', ['b', 'x', 'y', 'w', 'h', 'rid'])

def _do_pack(bin: Tuple[int,int], rects: List[Rectangle]) -> List[Packed]:
    packer = newPacker(rotation=False)

    packer.add_bin(*bin)
    for r in rects:
        packer.add_rect(*r)

    packer.pack()
    return packer.rect_list()

def _square_bin_bounds(
    rectangles: List[Rectangle]
) -> Tuple[int,Optional[int],List[Packed]]:
    ''' Search for largest square bin size that accommodates 
    the rectangles.

    Return the best-fit bin size (upper bound), the size 
    of the preceding bin that didn't fit (lower bound), 
    and the new packed rectangles.

    if `non_fit is None` indicates that there is no better 
    fit possible.
    '''
    non_fit = None
    fit = max(max(r.w, r.h) for r in rectangles)
    packed_rectangles = _do_pack((fit,fit), rectangles)

    while len(packed_rectangles) != len(rectangles):
        non_fit = fit
        fit *= 2
        packed_rectangles = _do_pack((fit,fit), rectangles)

    return fit, non_fit, packed_rectangles

def _next_bin(
    original_fit: int, new_fit: int, 
    opt_x: bool, opt_y: bool,
) -> Tuple[int,int]:
    return (
        new_fit if opt_x else original_fit,
        new_fit if opt_y else original_fit,
    )

def _bin_binary_search(
    rectangles: List[Rectangle],
    original_non_fit: int, original_fit: int,
    opt_x: bool, opt_y: bool,
) -> Tuple[int,List[Packed]]:
    assert original_non_fit is not None
    assert original_fit     is not None
    assert original_non_fit < original_fit

    non_fit = original_non_fit
    fit     = original_fit

    new_fit = original_fit
    packed_rectangles = _do_pack(
        _next_bin(original_fit, new_fit, opt_x, opt_y), 
        rectangles
    )

    better_fit = new_fit
    better_packed = packed_rectangles

    while True:
        if non_fit + 1 == fit:
            break

        new_fit = non_fit + (fit - non_fit) // 2
        packed_rectangles = _do_pack(
            _next_bin(original_fit, new_fit, opt_x, opt_y), 
            rectangles
        )

        cur_worked = len(packed_rectangles) == len(rectangles)
        if cur_worked:
            fit = new_fit
        else:
            non_fit = new_fit

        if cur_worked and new_fit < better_fit:
            better_fit = new_fit
            better_packed = packed_rectangles

    return better_fit, better_packed

def pack_rectangles(rectangles: List[Rectangle]) -> Tuple[int,int,List[Packed]]:
    ''' Try packing rectangles in boxes of different sizes
    until the smallest size is found.
    '''
    if not rectangles: return 0, 0, []

    fit, non_fit, packed = _square_bin_bounds(rectangles)
    if non_fit is not None:
        fit, packed = _bin_binary_search(rectangles, non_fit, fit, True, True)

    width_fit,  width_packed  = _bin_binary_search(rectangles, 0, fit, True, False)
    height_fit, height_packed = _bin_binary_search(rectangles, 0, fit, False, True)

    if width_fit < height_fit:
        width, height, packed = width_fit,  fit, width_packed
    else:
        width, height, packed = fit, height_fit, height_packed

    assert len(rectangles) == len(packed)
    return width, height, packed
