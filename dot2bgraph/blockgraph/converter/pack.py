# Copyright 2021 Vasily Rudchenko - bgraph
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
from typing import List
from collections import namedtuple

from rectpack import newPacker

Rectangle = namedtuple('Rectangle', ['w', 'h', 'rid'])

def _do_pack(bin, rects):
    packer = newPacker(rotation=False)

    packer.add_bin(*bin)
    for r in rects:
        packer.add_rect(*r)

    packer.pack()
    return packer.rect_list()

def _square_bin_bounds(rectangles):
    ''' Search for largest square bin size that accomodates 
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

def _square_bin_binary_search(rectangles, non_fit, fit):
    ''' Try smaller sizes between the working and non-working 
    bin size in binary search order.

    `fit` must be an upper bound for which packing succeeds.
    `non_fit` must be a lower bound for which packing fails.

    Return None if no better square bin can be found.
    '''
    assert non_fit is not None
    assert non_fit < fit

    new_fit = fit
    better_fit = fit
    better_rectangles = _do_pack((fit,fit), rectangles)

    while True:
        if non_fit + 1 == fit:
            break

        new_fit = non_fit + (fit - non_fit) // 2

        packed_rectangles = _do_pack((new_fit,new_fit), rectangles)
        cur_worked = len(packed_rectangles) == len(rectangles)

        if cur_worked:
            fit = new_fit
        else:
            non_fit = new_fit

        if cur_worked and new_fit < better_fit:
            better_fit = new_fit
            better_rectangles = packed_rectangles

    return better_fit, better_rectangles

def pack_rectangles(rectangles: List[Rectangle]):
    ''' Try packing rectangles in boxes of different sizes
    until the smallest "square" size is found.
    '''
    if not rectangles: return 0, []

    fit, non_fit, packed_rectangles = _square_bin_bounds(rectangles)
    if non_fit is not None:
        fit, packed_rectangles = _square_bin_binary_search(rectangles, non_fit, fit)

    assert len(rectangles) == len(packed_rectangles)
    return fit, packed_rectangles
