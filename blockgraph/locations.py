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

    def add_edge_end(self, edge_end):
        self.edge_ends.append(edge_end)

    def __repr__(self):
        return 'B {} ({},{}) {}x{} [{}]'.format(
            self.block_id,
            self.x,
            self.y,
            self.width,
            self.height,
            ','.join(str(edge_end.edge_end_id) for edge_end in self.edge_ends),
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

    def add_edge(self, to_edge_end):
        self.edge_ends.append(to_edge_end)

    def __repr__(self):
        return 'E {} ({},{}) {} -> [{}]'.format(
            self.edge_end_id,
            self.x,
            self.y,
            self.direction,
            ','.join(str(edge_end.edge_end_id) for edge_end in self.edge_ends),
        )

class Locations:
    ''' Object for all locations of blocks and edges
    in the graph.

    Define dedicated adder functions rather than simply 
    using sub-object's constructors in order to keep 
    track of IDs from the Locations object.
    '''
    def __init__(self):
        self.__blocks_id_counter = 0
        self.__blocks = {} # Use dict as Blocks can be deleted
        self.__edge_ends_id_counter = 0
        self.__edge_ends = {}

    def add_block(self, *args, **kwargs):
        new_block_id = self.__blocks_id_counter
        self.__blocks_id_counter += 1

        self.__blocks[new_block_id] = _Block(new_block_id, *args, **kwargs)
        return new_block_id

    def add_edge_end(self, block_id=None, *args, **kwargs):
        new_edge_end_id = self.__edge_ends_id_counter
        self.__edge_ends_id_counter += 1

        self.__edge_ends[new_edge_end_id] = _EdgeEnd(new_edge_end_id, *args, **kwargs)
        if block_id is not None:
            self.add_edge_end_to_block(block_id, new_edge_end_id)

        return new_edge_end_id

    def add_edge_end_to_block(self, block_id, edge_end_id):
        if (
            block_id    in self.__blocks and 
            edge_end_id in self.__edge_ends
        ):
            self.__blocks[block_id].add_edge_end(self.__edge_ends[edge_end_id])

    def add_edge(self, from_id, to_id):
        if (
            from_id in self.__edge_ends and 
            to_id   in self.__edge_ends
        ):
            self.__edge_ends[from_id].add_edge(self.__edge_ends[to_id])

    def del_block(self, block_id):
        del self.__blocks[block_id]
    
    def del_edge_end(self, block_id):
        del self.__blocks[block_id]

    def to_obj(self):
        obj = {
            'blocks': [],
            'edge_ends': [],
        }

        return obj

    def print_locations(self):
        print('Blocks:')
        for block in self.__blocks.values():
            print('  {}'.format(block))
        
        print('EdgeEnds:')
        for edge_end in self.__edge_ends.values():
            print('  {}'.format(edge_end))

    def __repr__(self):
        return '<{}> blocks:{}, edge_ends:{}'.format(
            hex(id(self)),
            len(self.__blocks),
            len(self.__edge_ends),
        )
