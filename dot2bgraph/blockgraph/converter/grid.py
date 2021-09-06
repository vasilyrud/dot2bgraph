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
from typing import Dict, Tuple, Set, List, NewType, Iterable, Optional
from collections import deque
from enum import Enum, auto
from itertools import chain
from abc import ABC, abstractmethod

from blockgraph.converter.node import Node, Region
from blockgraph.converter.pack import Rectangle, pack_rectangles

class EdgeType(Enum):
    NORMAL = auto()
    FWD = auto()
    CROSS = auto()
    BACK = auto()

EdgeTypes = NewType('EdgeTypes', Dict[Tuple[Node,Node],EdgeType])
NodeDepths = NewType('NodeDepths', Dict[Node,int])

class Grid(ABC):
    ''' Base class for grid interface. '''

    MIN_INDEX=0

    def __init__(self,
        node: Node,
        padding_outer: int,
        padding_inner: int,
    ):
        ''' 
        :param node: Node from which this Grid is made
        :param padding_outer: Space to sides of grid
        :param padding_inner: Space between sub-grids
        '''
        self.node = node
        self.padding_outer = padding_outer
        self.padding_inner = padding_inner

        self._node2coord: Dict[Node,Tuple[int,int]] = {}
        self._node2grid:  Dict[Node,Grid] = {}
        self._coord2node: Dict[int,Dict[int,Node]] = {} # dict[y][x]

        self._width:  Optional[int] = None
        self._height: Optional[int] = None

    @abstractmethod
    def iter_offsets(self) -> Iterable[Tuple[int,int,Grid]]:
        pass

    @property
    @abstractmethod
    def width(self) -> int:
        pass

    @property
    @abstractmethod
    def height(self) -> int:
        pass

    @abstractmethod
    def add_sub_grid(self, 
        grid: Grid, 
        x: Optional[int] = None, 
        y: Optional[int] = None,
    ) -> Grid:
        pass

    def _add_sub_grid(self,
        grid: Grid,
        x: int,
        y: int,
    ):
        ''' Common sub grid addition code. '''
        self._width, self._height = None, None
        assert grid.node.in_region == self.node

        assert grid.node not in self._node2coord, 'Node {} already placed.'.format(grid.node)
        self._node2coord[grid.node] = (x,y)
        self._node2grid[grid.node] = grid

        if y not in self._coord2node:
            self._coord2node[y] = {}
        assert x not in self._coord2node[y], 'Location ({},{}) already occupied.'.format(x, y)
        self._coord2node[y][x] = grid.node

    def _is_empty(self) -> bool:
        if len(self._node2grid) == 0:
            assert len(self._node2coord) == 0
            assert len(self._coord2node) == 0
            return True
        return False

    def _iter_y(self) -> Iterable[int]:
        return sorted(self._coord2node)

    def _iter_x(self, y) -> Iterable[int]:
        return sorted(self._coord2node[y])

    def _nodes_iter(self) -> Iterable[Node]:
        ''' Iterate through sub-nodes by their
        y and then by their x coordinates.
        '''
        for y in self._iter_y():
            for x in self._iter_x(y):
                yield self._coord2node[y][x]

    def _sub_grid_from_coord(self, x, y) -> Grid:
        return self._sub_grid_from_node(self._coord2node[y][x])

    def _sub_grid_from_node(self, node: Node) -> Grid:
        return self._node2grid[node]

    @property
    def sub_grids(self) -> Iterable[Grid]:
        return list(self._node2grid[node] for node in self._nodes_iter())

    @property
    def sub_nodes(self) -> Iterable[Node]:
        return list(self._nodes_iter())

    def __str__(self):
        string = ''

        string += self.__repr__()

        string += '['
        for i, y in enumerate(self._iter_y()):
            if i != 0: string += ','
            string += '['
            for j, x in enumerate(self._iter_x(y)):
                if j != 0: string += ','
                string += repr(self._coord2node[y][x])
            string += ']'
        string += ']'

        return string

    def __repr__(self):
        return 'grid<{}>'.format(self.node.name)

class GridPack(Grid):
    ''' A loose grid with any packing allowed, 
    e.g.:
        + - - - - - - - - + - - +
        | 0,0             | 9,0 |
        + - - - - + - - - + - - + - +
        | 0,2     | 5,2             |
        + - - + - +                 |
        | 0,4 |   |                 |
        + - - + + + - - + - - - - - +
        | 0,6   | 4,4   |
        + - - - + - - - +

    Each coord represents the absolute position
    as integers x,y.
    '''

    def iter_offsets(self) -> Iterable[Tuple[int,int,Grid]]:
        for node in self._nodes_iter():
            offset_x, offset_y = self._node2coord[node]
            sub_grid = self._node2grid[node]
            yield offset_x + self.padding_outer, offset_y + self.padding_outer, sub_grid

    @property
    def width(self) -> int:
        if self._width is not None:
            return self._width

        width_tot = 0
        if self.sub_grids:
            width_tot = max(
                self._node2coord[node][0] + grid.width
                for node, grid in self._node2grid.items()
            )
            width_tot += self.padding_outer * 2

        self._width = max(
            1, 
            width_tot,
            self.node.width,
        )
        return self._width

    @property
    def height(self) -> int:
        if self._height is not None:
            return self._height

        height_tot = 0
        if self.sub_grids:
            height_tot = max(
                self._node2coord[node][1] + grid.height
                for node, grid in self._node2grid.items()
            )
            height_tot += self.padding_outer * 2

        self._height = max(
            1, 
            height_tot,
            self.node.height,
        )
        return self._height

    def add_sub_grid(self, 
        grid: Grid, 
        x: Optional[int] = None, 
        y: Optional[int] = None,
    ) -> Grid:
        assert x is not None
        assert y is not None

        self._add_sub_grid(grid, x, y)

class GridRows(Grid):
    ''' An ordering of nodes per-region on a
    pseudo-grid, e.g.:
        + - - - - - - - - + - - +
        | 0,0             | 1,0 |
        + - - - - + - - - + - - + - +
        | 0,1     | 1,1             |
        + - - - - +                 |
                  |                 |
        + - - +   + - - - - - - - - +
        | 0,2 |
        + - - + + - - - +
        | 0,4   | 2,4   |
        + - - - + - - - +

    Each coord represents the relative position
    of a sub-grid, not it's x,y location.
    '''

    def _iter_offset_y(self) -> Iterable[Tuple[int,int]]:
        offset = 0

        # y does not necessarily start at 0
        for i, y in enumerate(self._iter_y()):
            if i == 0:
                offset += self.padding_outer
            else:
                offset += self.padding_inner

            yield offset, y

            offset += self._row_height(y)

    def _iter_offset_x(self, y) -> Iterable[Tuple[int,int]]:
        offset = 0

        # x does not necessarily start at 0
        for i, x in enumerate(self._iter_x(y)):
            if i == 0:
                offset += self._row_offset(y) + self.padding_outer
            else:
                offset += self.padding_inner

            yield offset, x

            offset += self._sub_grid_from_coord(x, y).width

    def iter_offsets(self) -> Iterable[Tuple[int,int,Grid]]:
        for offset_y, y in self._iter_offset_y():
            for offset_x, x in self._iter_offset_x(y):

                sub_grid = self._sub_grid_from_coord(x, y)
                yield offset_x, offset_y, sub_grid

    def _row_offset(self, y):
        return (self.width - self._row_width_total(y)) // 2

    def _row_offset_end(self, y):
        return self.width - self._row_width_total(y) - self._row_offset(y)

    def _row_width_total(self, y) -> int:
        ''' Get width of a single row, including
        the padding on the left and right.
        '''
        return self._row_width(y) + self.padding_outer * 2

    def _row_width(self, y) -> int:
        row = self._coord2node[y]
        return (
            sum(
                self._node2grid[node].width
                for node in row.values()
            )
            + self.padding_inner * (len(row) - 1)
        )

    def _row_widths(self) -> int:
        return [self._row_width(y) for y in self._coord2node]

    @property
    def width(self) -> int:
        if self._width is not None:
            return self._width

        row_widths = self._row_widths()
        row_widths_tot = 0
        if row_widths:
            row_widths_tot = max(row_widths)
            row_widths_tot += self.padding_outer * 2

        self._width = max(
            1, 
            row_widths_tot,
            self.node.width,
        )
        return self._width

    def _row_height(self, y) -> int:
        row = self._coord2node[y]
        return max(
            self._node2grid[node].height
            for node in row.values()
        )

    def _row_heights(self) -> int:
        return [self._row_height(y) for y in self._coord2node]

    @property
    def height(self) -> int:
        if self._height is not None:
            return self._height

        row_heights = self._row_heights()
        row_heights_tot = 0
        if row_heights:
            row_heights_tot = sum(row_heights)
            row_heights_tot += self.padding_inner * (len(row_heights) - 1)
            row_heights_tot += self.padding_outer * 2

        self._height = max(
            1, 
            row_heights_tot,
            self.node.height,
        )
        return self._height

    def _has_node(self, node: Node) -> bool:
        return node in self._node2coord

    def _get_x(self, node: Node) -> int:
        return self._node2coord[node][0]

    def _get_y(self, node: Node) -> int:
        return self._node2coord[node][1]

    def add_sub_grid(self, 
        grid: Grid, 
        x: Optional[int] = None, 
        y: Optional[int] = None,
    ) -> Grid:
        ''' Add node to the given x,y location.
        If y is not specified, use the last available row.
        If x is not specified, add to the end of the row.
        Generate a sub-grid for the newly added node.
        '''
        use_y = y if y is not None else max(
            self._coord2node.keys(), 
            default=Grid.MIN_INDEX
        )
        if use_y not in self._coord2node:
            self._coord2node[use_y] = {}

        use_x = x if x is not None else max(
            (k+1 for k in self._coord2node[use_y].keys()), 
            default=Grid.MIN_INDEX
        )

        self._add_sub_grid(grid, use_x, use_y)

class _SeenNodes:
    ''' Helper class to store info about nodes
    during traversal.
    '''
    def __init__(self):
        self.nodes: Set[Node] = set()

        self.time: int = 0
        self.start:  Dict[Node,int] = {}
        self.finish: Dict[Node,int] = {}

def _sources_per_conn_comp(conn_comp: Iterable[Node]) -> Set[Node]:
    ''' Find either the sources that are naturally
    sources or pick one source that is the least 
    connected inwards.
    Assume we are given a connected component.
    '''
    assert conn_comp, 'Got empty set of connected components to get sources from.'

    # Get node that doesn't have inward connections.
    sources = {node for node in conn_comp if not node.prev}
    if sources: return sources

    # Otherwise, pick a node out of nodes with fewest inward connections 
    # that also has the most outward connections.
    min_inward  = min(len(node.prev) for node in conn_comp)
    max_outward = max(len(node.next) for node in conn_comp)

    for node in sorted(conn_comp, key=lambda n: n.name):
        if (
            len(node.prev) == min_inward and
            len(node.next) == max_outward
        ):
            return {node}

    assert False, 'Somehow didn\'t find any source node.'

def _get_conn_comp_dfs_recurse(node, seen, conn_comp):
    seen.nodes.add(node)
    conn_comp.add(node)

    # Iterate over edges while ignoring directedness
    for next_node in chain(node.local_next, node.local_prev):
        if next_node in seen.nodes: continue

        _get_conn_comp_dfs_recurse(next_node, seen, conn_comp)

def _sources(region: Region) -> Iterable[Node]:
    ''' Get sources, one per connected component.
    Return in alphabetical order.
    '''
    seen = _SeenNodes()
    sources = set()

    for node in region.nodes_sorted:
        if node in seen.nodes: continue

        conn_comp = set()
        _get_conn_comp_dfs_recurse(node, seen, conn_comp)

        sources |= _sources_per_conn_comp(conn_comp)

    return list(sorted(sources, key=lambda s: s.name))

def _classify_edge(
    edge,
    edge_types,
    seen,
):
    cur_node, next_node = edge

    if next_node not in seen.nodes:
        edge_type = EdgeType.NORMAL

    elif next_node not in seen.finish:
        edge_type = EdgeType.BACK

    elif seen.start[cur_node] < seen.start[next_node]:
        edge_type = EdgeType.FWD

    else:
        edge_type = EdgeType.CROSS

    if edge not in edge_types:
        edge_types[edge] = edge_type

def _get_edge_types_recurse(
    prev_edge,
    edge_types,
    seen,
):
    ''' Helper function to classify all nodes in the
    graph by traversing in DFS order.
    Assumes caller iterates over source nodes.
    '''
    _, cur_node = prev_edge

    seen.time += 1
    seen.start[cur_node] = seen.time
    seen.nodes.add(cur_node)

    for next_node in cur_node.local_next:
        next_edge = (cur_node,next_node)

        _classify_edge(next_edge, edge_types, seen)

        if edge_types[next_edge] == EdgeType.NORMAL:
            _get_edge_types_recurse(
                next_edge,
                edge_types,
                seen,
            )

    seen.time += 1
    seen.finish[cur_node] = seen.time

def _get_edge_types(
    region: Region,
):
    ''' Clasify edges in the graph.

    Call DFS to edge classification starting only
    at the source nodes.

    Assumes that source nodes will never be traversed
    to before they are used as sources.
    '''
    edge_types: EdgeTypes = {}
    seen = _SeenNodes()

    for source in _sources(region):
        assert source not in seen.nodes, 'Source node was used that does not allow source-driven DFS edge classification.'
        next_edge = (None, source)

        _get_edge_types_recurse(
            next_edge, 
            edge_types, 
            seen,
        )

    return edge_types

def _num_local_prev_forward_edges(
    node: Node,
    edge_types: EdgeTypes,
):
    ''' Return the number of local prev edges
    that are not back edges. '''

    return sum(1 for prev_node in node.local_prev 
        if edge_types[(prev_node,node)] != EdgeType.BACK
    )

def _get_node_depths(
    region: Region,
    edge_types: EdgeTypes,
) -> NodeDepths:
    node_depths: NodeDepths = {}
    seen_in_edges = {}

    q = deque()

    for source in _sources(region):
        node_depths[source] = Grid.MIN_INDEX
        seen_in_edges[source] = set()

        q.append((source, Grid.MIN_INDEX))

    while q:
        cur_node, cur_depth = q.popleft()

        for next_node in cur_node.local_next:
            next_edge = (cur_node,next_node)

            node_depths.setdefault(next_node, 0)
            if edge_types[next_edge] != EdgeType.BACK:
                node_depths[next_node] = max(node_depths[next_node], cur_depth+1)

            next_seen = seen_in_edges.setdefault(next_node, set())
            next_seen.add(next_edge)

            if (len(next_seen) == 
                _num_local_prev_forward_edges(next_node, edge_types)
            ):
                q.append((next_node, cur_depth+1))

    return node_depths

def _get_edge_info(node: Node) -> Tuple[EdgeTypes,NodeDepths]:
    edge_types  = _get_edge_types(node)
    node_depths = _get_node_depths(node, edge_types)
    return edge_types, node_depths

def _independent_sub_grids(node_depths: NodeDepths):
    return (
        len(node_depths) > 1 and 
        all(depth == Grid.MIN_INDEX for depth in node_depths.values())
    )

def _make_pack_grid(
    node: Node, 
    padding_outer: int, 
    padding_inner: int,
    sub_grids: List[Tuple[Grid,int]],
):
    grid = GridPack(node, padding_outer, padding_inner)

    name2grid = {}
    rectangles = []

    for sub_grid, _ in sub_grids:
        name2grid[sub_grid.node.name] = sub_grid
        rectangles.append(Rectangle(
            sub_grid.width  + padding_inner, 
            sub_grid.height + padding_inner, 
            sub_grid.node.name
        ))

    _, _, placements = pack_rectangles(rectangles)

    for _, x, y, _, _, rid in placements:
        grid.add_sub_grid(
            name2grid[rid], 
            x, y
        )

    return grid

def _make_rows_grid(
    node: Node, 
    padding_outer: int, 
    padding_inner: int,
    sub_grids: List[Tuple[Grid,int]],
):
    grid = GridRows(node, padding_outer, padding_inner)

    for sub_grid, depth in sub_grids:
        grid.add_sub_grid(sub_grid, y=depth)

    return grid

def place_on_grid(
    node: Node,
    padding_outer: int,
    padding_inner: int,
) -> Grid:

    if not node.is_region:
        return GridRows(node, padding_outer, padding_inner)

    _, node_depths = _get_edge_info(node)

    sub_grids = []
    for sub_node, depth in node_depths.items():
        sub_grid = place_on_grid(sub_node, padding_outer, padding_inner)
        sub_grids.append((sub_grid, depth))

    if _independent_sub_grids(node_depths):
        return _make_pack_grid(node, padding_outer, padding_inner, sub_grids)

    return _make_rows_grid(node, padding_outer, padding_inner, sub_grids)
