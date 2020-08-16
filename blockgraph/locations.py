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

    @property
    def coords(self):
        return (self.x, self.y)

    @property
    def size(self):
        return (self.width, self.height)

    def add_edge_end(self, edge_end):
        self.edge_ends.append(edge_end)

    def to_obj(self):
        return {
            'x': self.x,'y': self.y,
            'width': self.width,'height': self.height,
            'depth': self.depth,
            'color': self.color.hex_l,
            'shape': self.shape,
            'edge_ends': [edge_end.edge_end_id for edge_end in self.edge_ends],
        }

    def __str__(self):
        return 'B{} ({},{}) {}x{} [{}]'.format(
            self.block_id,
            self.x,
            self.y,
            self.width,
            self.height,
            ','.join(str(edge_end.edge_end_id) for edge_end in self.edge_ends),
        )

    def __repr__(self):
        return 'B{}'.format(
            self.block_id,
        )

class _EdgeEnd:
    class Direction:
        VALID_DIRECTIONS = [
            'up',
            'down',
            'left',
            'right',
        ]

        def __init__(self, direction):
            if direction not in self.VALID_DIRECTIONS:
                raise ValueError('{} is not a recognized direction.'.format(direction))
            self._direction = direction

        def __eq__(self, other):
            if isinstance(other, _EdgeEnd.Direction):
                return self._direction == other._direction
            elif isinstance(other, str):
                return self._direction == other
            return NotImplemented

        def __hash__(self):
            return hash(self._direction)

        def __str__(self):
            return self._direction

        def __repr__(self):
            return self._direction

    def __init__(self, edge_end_id, *args, **kwargs):
        self.edge_end_id = edge_end_id

        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.direction = _EdgeEnd.Direction(kwargs.get('direction', 'up'))

        self.edge_ends = []

    @property
    def coords(self):
        return (self.x, self.y)

    def add_edge_dest(self, to_edge_end):
        self.edge_ends.append(to_edge_end)

    def to_obj(self):
        return {
            'x': self.x,'y': self.y,
            'direction': str(self.direction),
            'edge_ends': [edge_end.edge_end_id for edge_end in self.edge_ends],
        }

    def __str__(self):
        return 'E{} ({},{}) {} -> [{}]'.format(
            self.edge_end_id,
            self.x,
            self.y,
            self.direction,
            ','.join(str(edge_end.edge_end_id) for edge_end in self.edge_ends),
        )

    def __repr__(self):
        return 'E{}'.format(
            self.edge_end_id,
        )

class Locations:
    ''' Object for all locations of blocks and edges
    in the graph.

    Define dedicated adder functions rather than simply 
    using sub-object's constructors in order to keep 
    track of IDs from the Locations object.
    '''
    def __init__(self):
        self._blocks_id_counter = 0
        self._blocks = {} # Use dict as Blocks can be deleted
        self._edge_ends_id_counter = 0
        self._edge_ends = {}

    def add_block(self, *args, **kwargs):
        new_block_id = self._blocks_id_counter
        self._blocks_id_counter += 1

        self._blocks[new_block_id] = _Block(new_block_id, *args, **kwargs)
        return new_block_id

    def add_edge_end(self, block_id=None, *args, **kwargs):
        new_edge_end_id = self._edge_ends_id_counter
        self._edge_ends_id_counter += 1

        self._edge_ends[new_edge_end_id] = _EdgeEnd(new_edge_end_id, *args, **kwargs)
        if block_id is not None:
            self.assign_edge_to_block(new_edge_end_id, block_id)

        return new_edge_end_id

    def assign_edge_to_block(self, edge_end_id, block_id):
        self.block(block_id).add_edge_end(self.edge_end(edge_end_id))

    def add_edge(self, from_edge_end_id, to_edge_end_id):
        self.edge_end(from_edge_end_id).add_edge_dest(self.edge_end(to_edge_end_id))

    def block(self, block_id):
        if block_id not in self._blocks:
            raise KeyError('{} does not contain block with id={}.'.format(self, block_id))
        return self._blocks[block_id]

    def edge_end(self, edge_end_id):
        if edge_end_id not in self._edge_ends:
            raise KeyError('{} does not contain edge_end with id={}.'.format(self, edge_end_id))
        return self._edge_ends[edge_end_id]

    def del_block(self, block_id):
        del self._blocks[block_id]
    
    def del_edge_end(self, edge_end_id):
        del self._edge_ends[edge_end_id]

    def to_obj(self):
        obj = {
            'blocks': {
                block_id: block.to_obj() 
                for block_id, block in self._blocks.items()
            },
            'edge_ends': {
                edge_end_id: edge_end.to_obj() 
                for edge_end_id, edge_end in self._edge_ends.items()
            },
        }

        return obj

    def print_locations(self):
        print('Blocks:')
        for block in self._blocks.values():
            print('  {}'.format(block))
        
        print('EdgeEnds:')
        for edge_end in self._edge_ends.values():
            print('  {}'.format(edge_end))

    def __repr__(self):
        return 'Locations<{}>#B={},#E={}'.format(
            hex(id(self)),
            len(self._blocks),
            len(self._edge_ends),
        )
