# Copyright 2020 Vasily Rudchenko - bgraph
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

from colour import Color

class _Block:
    def __init__(self, block_id, *args, **kwargs):
        self.block_id = block_id

        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.width  = kwargs.get('width',  1)
        self.height = kwargs.get('height', 1)
        self.depth = kwargs.get('depth', 0)
        self.color = Color(kwargs.get('color', '#cccccc'))
        self.shape = kwargs.get('shape', 'box')

        self.edge_ends = []

    def __repr__(self):
        return 'B {} ({},{}) {}x{}'.format(
            self.block_id,
            self.x,
            self.y,
            self.width,
            self.height,
        )

class _EdgeEnd:
    class _Direction:
        VALID_DIRECTIONS = [
            'up',
            'down',
            'left',
            'right',
        ]

        def __init__(self, direction):
            if direction not in self.VALID_DIRECTIONS:
                raise ValueError('{} is not a recognized direction.'.format(direction))
            self.direction = direction
        
        def __repr__(self):
            return self.direction

    def __init__(self, edge_end_id, *args, **kwargs):
        self.edge_end_id = edge_end_id

        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.direction = _EdgeEnd._Direction(kwargs.get('direction', 'up'))

        self.edge_ends = []

    def __repr__(self):
        return 'E {} ({},{}) {}'.format(
            self.edge_end_id,
            self.x,
            self.y,
            self.direction,
        )

class Locations:
    def __init__(self):
        self.blocks_id_counter = 0
        self.blocks = []
        self.edge_ends_id_counter = 0
        self.edge_ends = []

        self.blocks.append(_Block(0, x=5))
        print(self.blocks[0])
        self.edge_ends.append(_EdgeEnd(0, direction='down'))
        print(self.edge_ends[0])

    def to_obj(self):
        obj = {
            'blocks': [],
            'edge_ends': [],
        }

        return obj
