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
from typing import Dict, Set, Optional, Tuple, NewType
from enum import Enum

from blockgraph.utils.color import bgraph_color

Color = NewType('Color', Tuple[int,int,int])

class Locations:
    ''' Class for all locations of blocks and edges
    in the graph.

    Define dedicated adder functions rather than simply 
    using sub-object's constructors in order to keep 
    track of IDs from the Locations object.
    '''
    def __init__(self, 
        bg_color: Color = (255,255,255), 
        highlight_bg_color: Color = (255,255,255), 
        highlight_fg_color: Color = (0,0,0),
    ):
        '''
        :param bg_color: Background color of the graph
        :param highlight_bg_color: Background color for graph highlights
        :param highlight_fg_color: Foreground color for graph highlights
        '''
        self.bg_color = bg_color
        self.highlight_bg_color = highlight_bg_color
        self.highlight_fg_color = highlight_fg_color

        self._blocks_id_counter = 0
        self._blocks: Dict[int, _Block] = {} # Use dict as Blocks can be deleted
        self._edge_ends_id_counter = 0
        self._edge_ends: Dict[int, _EdgeEnd] = {}

    def add_block(self, *args, **kwargs):
        new_block_id = self._blocks_id_counter
        self._blocks_id_counter += 1

        self._blocks[new_block_id] = _Block(new_block_id, *args, **kwargs)
        return new_block_id

    def add_edge_end(self, *args, **kwargs):
        new_edge_end_id = self._edge_ends_id_counter
        self._edge_ends_id_counter += 1

        self._edge_ends[new_edge_end_id] = _EdgeEnd(new_edge_end_id, *args, **kwargs)
        if 'block_id' in kwargs:
            self.assign_edge_to_block(new_edge_end_id, kwargs['block_id'])

        return new_edge_end_id

    def assign_edge_to_block(self, edge_end_id: int, block_id: int):
        self.edge_end(edge_end_id).block_id = block_id
        self.block(block_id)._add_edge_end(self.edge_end(edge_end_id))

    def add_edge(self, from_edge_end_id: int, to_edge_end_id: int):
        self.edge_end(from_edge_end_id)._add_edge_end(self.edge_end(to_edge_end_id))
        self.edge_end(to_edge_end_id)._add_edge_end(self.edge_end(from_edge_end_id))

        self.edge_end(from_edge_end_id).is_source = True
        assert self.edge_end(to_edge_end_id).is_source == False

    @property
    def width(self):
        max_x = 0
        for block in self.iter_blocks():
            max_x = max(max_x, block.x + block.width)
        for edge_end in self.iter_edge_ends():
            max_x = max(max_x, edge_end.x + 1)
        return max_x

    @property
    def height(self):
        max_y = 0
        for block in self.iter_blocks():
            max_y = max(max_y, block.y + block.height)
        for edge_end in self.iter_edge_ends():
            max_y = max(max_y, edge_end.y + 1)
        return max_y

    def block(self, block_id: int):
        self._check_exists(self._blocks, block_id, 'block')
        return self._blocks[block_id]

    def iter_blocks(self):
        for i in sorted(self._blocks):
            yield self._blocks[i]

    def iter_edge_ends(self):
        for i in sorted(self._edge_ends):
            yield self._edge_ends[i]

    def edge_end(self, edge_end_id: int):
        self._check_exists(self._edge_ends, edge_end_id, 'edge_end')
        return self._edge_ends[edge_end_id]

    def del_block(self, block_id: int):
        for other_edge_end_id in self.block(block_id).edge_ends:
            self.edge_end(other_edge_end_id).block_id = None

        del self._blocks[block_id]
    
    def del_edge_end(self, edge_end_id: int):
        edge_end = self.edge_end(edge_end_id)

        if edge_end.block_id is not None:
            self.block(edge_end.block_id)._del_edge_end(edge_end)

        for other_edge_end_id in edge_end.edge_ends:
            self.edge_end(other_edge_end_id)._del_edge_end(edge_end)

        del self._edge_ends[edge_end_id]

    def del_edge(self, from_edge_end_id: int, to_edge_end_id: int):
        self.edge_end(from_edge_end_id)._del_edge_end(self.edge_end(to_edge_end_id))
        self.edge_end(to_edge_end_id)._del_edge_end(self.edge_end(from_edge_end_id))

    def _check_exists(self, items, item_id, item_str):
        if item_id not in items:
            raise KeyError('{} does not contain {} with id={}.'.format(self, item_str, item_id))

    def to_obj(self):
        obj = {
            'width':  self.width,
            'height': self.height,
            'bgColor': bgraph_color(self.bg_color),
            'highlightBgColor': bgraph_color(self.highlight_bg_color),
            'highlightFgColor': bgraph_color(self.highlight_fg_color),
            'blocks': [
                block.to_obj() 
                for block in self._blocks.values()
            ],
            'edgeEnds': [
                edge_end.to_obj() 
                for edge_end in self._edge_ends.values()
            ],
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

class _Block:
    ''' A simple block in the graph.

    The block contains edge ends, which are responsible
    for encoding information about edges they participate in.
    '''
    def __init__(self, block_id: int, *args, **kwargs):
        self.block_id = block_id

        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.width  = kwargs.get('width',  1)
        self.height = kwargs.get('height', 1)
        self.depth = kwargs.get('depth', 0)
        self.color = kwargs.get('color', (204,204,204))
        self.label = kwargs.get('label', None)

        self._edge_ends: Set[_EdgeEnd] = set()

        assert self.x >= 0
        assert self.y >= 0
        assert self.width  >= 1
        assert self.height >= 1

    @property
    def coords(self):
        return (self.x, self.y)

    @property
    def size(self):
        return (self.width, self.height)

    @property
    def edge_ends(self):
        return [edge_end.edge_end_id for edge_end in self._edge_ends]

    def _add_edge_end(self, edge_end: _EdgeEnd):
        self._edge_ends.add(edge_end)

    def _del_edge_end(self, edge_end: _EdgeEnd):
        if edge_end not in self._edge_ends:
            raise KeyError('{} does not contain {} with id={}.'.format(self, 'edge_end', edge_end.edge_end_id))
        self._edge_ends.remove(edge_end)

    def to_obj(self):
        obj = {
            'id': self.block_id,
            'x': self.x,'y': self.y,
            'width': self.width,'height': self.height,
            'depth': self.depth,
            'color': bgraph_color(self.color),
            'edgeEnds': [edge_end.edge_end_id for edge_end in self._edge_ends],
        }

        if self.label is not None:
            obj['label'] = self.label

        return obj

    def __eq__(self, other):
        return self.block_id == other.block_id

    def __hash__(self):
        return self.block_id

    def __str__(self):
        return 'B{} ({},{}) {}x{} [{}]'.format(
            self.block_id,
            self.x,
            self.y,
            self.width,
            self.height,
            ','.join(str(edge_end.edge_end_id) for edge_end in self._edge_ends),
        )

    def __repr__(self):
        return 'B{}'.format(
            self.block_id,
        )

class Direction(Enum):
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4

    def __str__(self):
        return self.name.lower()

class _EdgeEnd:
    ''' An edge end is the representation of one end of an
    edge in the graph.

    It is directional, with "is_source" and "direction" used 
    to show directionality.
    '''
    def __init__(self, edge_end_id: int, *args, **kwargs):
        self.edge_end_id = edge_end_id

        self.x: int = kwargs.get('x', 0)
        self.y: int = kwargs.get('y', 0)
        self.color: Color = kwargs.get('color', (0,0,0))
        self.direction: Direction = Direction(kwargs.get('direction', Direction.UP))
        self.is_source: bool = kwargs.get('is_source', False)
        self.block_id: Optional[int] = kwargs.get('block_id', None)
        self.label = kwargs.get('label', None)

        self._edge_ends: Set[_EdgeEnd] = set()

        assert self.x >= 0
        assert self.y >= 0

    @property
    def coords(self):
        return (self.x, self.y)

    @property
    def edge_ends(self):
        return [edge_end.edge_end_id for edge_end in self._edge_ends]

    def _add_edge_end(self, edge_end: _EdgeEnd):
        self._edge_ends.add(edge_end)

    def _del_edge_end(self, edge_end: _EdgeEnd):
        if edge_end not in self._edge_ends:
            raise KeyError('{} does not contain {} with id={}.'.format(self, 'edge_end', edge_end.edge_end_id))
        self._edge_ends.remove(edge_end)

    def to_obj(self):
        obj = {
            'id': self.edge_end_id,
            'x': self.x,'y': self.y,
            'color': bgraph_color(self.color),
            'direction': self.direction.value,
            'isSource': self.is_source,
            'block': self.block_id,
            'edgeEnds': [edge_end.edge_end_id for edge_end in self._edge_ends],
        }

        if self.label is not None:
            obj['label'] = self.label

        return obj

    def __eq__(self, other):
        return self.edge_end_id == other.edge_end_id

    def __hash__(self):
        return self.edge_end_id

    def __str__(self):
        return 'E{} ({},{}) {} -> [{}]'.format(
            self.edge_end_id,
            self.x,
            self.y,
            self.direction,
            ','.join(str(edge_end.edge_end_id) for edge_end in self._edge_ends),
        )

    def __repr__(self):
        return 'E{}'.format(
            self.edge_end_id,
        )
