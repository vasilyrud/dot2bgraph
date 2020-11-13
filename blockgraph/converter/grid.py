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
from typing import Dict, Tuple, List, Set, NewType
from collections import deque, OrderedDict
from enum import Enum, auto
from itertools import chain

from blockgraph.converter.node import Node, Region

class EdgeType(Enum):
    NORMAL = auto()
    FWD = auto()
    CROSS = auto()
    BACK = auto()

EdgeTypes = NewType('EdgeTypes', Dict[Tuple[Node,Node],EdgeType])
NodeDepths = NewType('NodeDepths', 'OrderedDict[Node, int]')

class Grid:
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
    '''

    MIN_INDEX=0

    def __init__(self, 
        node: Node,
        padding_l: Optional[int] = 1,
        padding_r: Optional[int] = 1,
        padding_t: Optional[int] = 1,
        padding_b: Optional[int] = 1,
        space_col: Optional[int] = 1,
        space_row: Optional[int] = 1,
    ):
        ''' In a hierarchy of grids, only the top-level Grid
        has to be explicitly created.

        :param node: Node from which this Grid is made

        :param padding_l: Space to left   side of grid
        :param padding_r: Space to right  side of grid
        :param padding_t: Space to top    side of grid
        :param padding_b: Space to bottom side of grid

        :param space_col: Space between grid columns
        :param space_row: Space between grid rows
        '''
        self.node = node

        self.padding_l = padding_l
        self.padding_r = padding_r
        self.padding_t = padding_t
        self.padding_b = padding_b
        self.space_col = space_col
        self.space_row = space_row

        self._node2coord: Dict[Node,Tuple[int,int]] = {}
        self._node2grid:  Dict[Node,Grid] = {}
        self._coord2node: Dict[int,Dict[int,Node]] = {} # dict[y][x]

    def iter_y(self) -> Iterable[int]:
        return sorted(self._coord2node)

    def iter_x(self, y) -> Iterable[int]:
        return sorted(self._coord2node[y])

    def _nodes_iter(self) -> Iterable[Node]:
        ''' Iterate through sub-nodes by their
        y and then by their x coordinates.
        '''
        for y in self.iter_y():
            for x in self.iter_x(y):
                yield self._coord2node[y][x]

    def iter_offset_y(self) -> Iterable[Tuple[int,int]]:
        offset = 0

        # y does not necessarily start at 0
        for i, y in enumerate(self.iter_y()):
            if i == 0:
                offset += self.padding_t
            else:
                offset += self.space_row

            yield offset, y

            offset += self._row_height(y)

    def iter_offset_x(self, y) -> Iterable[Tuple[int,int]]:
        offset = 0

        # x does not necessarily start at 0
        for i, x in enumerate(self.iter_x(y)):
            if i == 0:
                offset += self.row_offset(y) + self.padding_l
            else:
                offset += self.space_col

            yield offset, x

            offset += self.sub_grid_from_coord(x, y).width

    def row_offset(self, y):
        return (self.width - self.row_width(y)) // 2

    def row_offset_end(self, y):
        return self.width - self.row_width(y) - self.row_offset(y)

    @property
    def sub_grids(self) -> Iterable[Grid]:
        return list(self._node2grid[node] for node in self._nodes_iter())

    @property
    def sub_nodes(self) -> Iterable[Node]:
        return list(self._nodes_iter())

    @property
    def is_empty(self) -> bool:
        if len(self._node2grid) == 0:
            assert len(self._node2coord) == 0
            assert len(self._coord2node) == 0
            return True
        return False

    def row_width(self, y) -> int:
        ''' Get width of a single row, including
        the padding on the left and right.
        '''
        return self._row_width(y) + self.padding_l + self.padding_r

    def _row_width(self, y) -> int:
        row = self._coord2node[y]
        return (
            sum(
                self._node2grid[node].width + self.space_col
                for node in row.values()
            )
            - self.space_col
        )

    def _row_widths(self) -> int:
        return [self._row_width(y) for y in self._coord2node]

    @property
    def width(self) -> int:
        row_widths = self._row_widths()
        row_widths_tot = 0
        if row_widths:
            row_widths_tot = max(row_widths) + self.padding_l + self.padding_r

        return max(
            1, 
            row_widths_tot,
            self.node.width,
        )

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
        row_heights = self._row_heights()
        row_heights_tot = 0
        if row_heights:
            row_heights_tot = sum(row_heights) + (len(row_heights) - 1)*self.space_row + self.padding_t + self.padding_b

        return max(
            1, 
            row_heights_tot,
            self.node.height,
        )

    def sub_grid_from_coord(self, x, y) -> Grid:
        return self.sub_grid_from_node(self._coord2node[y][x])

    def sub_grid_from_node(self, node: Node) -> Grid:
        return self._node2grid[node]

    def has_node(self, node: Node) -> bool:
        return node in self._node2coord

    def get_x(self, node: Node) -> int:
        return self._node2coord[node][0]

    def get_y(self, node: Node) -> int:
        return self._node2coord[node][1]

    def add_sub_grid(self, 
        node: Node, 
        x: Optional[int] = None, 
        y: Optional[int] = None,
    ) -> Grid:
        ''' Add node to the given x,y location.
        If y is not specified, use the last available row.
        If x is not specified, add to the end of the row.
        Generate a sub-grid for the newly added node.
        '''
        assert node.in_region == self.node

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

        assert node not in self._node2coord, 'Node {} already placed.'.format(node)
        self._node2coord[node] = (use_x,use_y)
        new_grid = Grid(node,
            padding_l=self.padding_l,
            padding_r=self.padding_r,
            padding_t=self.padding_t,
            padding_b=self.padding_b,
            space_col=self.space_col,
            space_row=self.space_row,
        )
        self._node2grid[node] = new_grid

        assert use_x not in self._coord2node[use_y], 'Location ({},{}) already occupied.'.format(use_x, use_y)
        self._coord2node[use_y][use_x] = node

        return new_grid

    def del_sub_grid(self, node: Node):
        ''' Remove node from all of grid's data structures.
        This means removing the sub-grid as well.
        '''
        coord = self._node2coord[node]
        x = coord[0]
        y = coord[1]

        del self._node2coord[node]
        del self._node2grid[node]
        del self._coord2node[y][x]
        if len(self._coord2node[y]) == 0:
            del self._coord2node[y]

    def __str__(self):
        string = ''

        string += self.__repr__()

        string += '['
        for i, y in enumerate(self.iter_y()):
            if i != 0: string += ','
            string += '['
            for j, x in enumerate(self.iter_x(y)):
                if j != 0: string += ','
                string += repr(self._coord2node[y][x])
            string += ']'
        string += ']'

        return string

    def __repr__(self):
        return 'grid<{}>'.format(self.node.name)

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

    edge_types[edge] = edge_type
    return edge_type

def _update_depth(
    edge,
    edge_types,
    node_depths,
    depth,
):
    _, next_node = edge

    if edge in edge_types and edge_types[edge] == EdgeType.BACK:
        return
    if next_node in node_depths and node_depths[next_node] > depth:
        return

    node_depths[next_node] = depth

def _get_edge_info_dfs_recurse(
    prev_edge,
    edge_types,
    node_depths,
    seen,
    depth,
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
        _update_depth(next_edge, edge_types, node_depths, depth)

        if edge_types[next_edge] == EdgeType.NORMAL:
            _get_edge_info_dfs_recurse(
                next_edge,
                edge_types,
                node_depths,
                seen,
                depth+1,
            )

    seen.time += 1
    seen.finish[cur_node] = seen.time

def _get_edge_info_dfs(
    region: Region,
    edge_types: EdgeTypes,
    node_depths: NodeDepths,
):
    ''' Call DFS to edge classification starting only
    at the source nodes.
    Assumes that source nodes will never be traversed
    to before they are used as sources.
    '''
    seen = _SeenNodes()

    for source in _sources(region):
        assert source not in seen.nodes, 'Source node was used that does not allow source-driven DFS edge classification.'
        next_edge = (None, source)

        _update_depth(next_edge, edge_types, node_depths, Grid.MIN_INDEX)
        _get_edge_info_dfs_recurse(
            next_edge, 
            edge_types, 
            node_depths, 
            seen,
            Grid.MIN_INDEX+1,
        )

def _get_edge_info(
    region: Region,
) -> Tuple[EdgeTypes,NodeDepths]:
    ''' Clasify edges in the graph based
    on their EdgeType and nodes based on
    their depth in the graph.
    '''
    edge_types: EdgeTypes = {}
    node_depths: NodeDepths = OrderedDict()

    _get_edge_info_dfs(region, edge_types, node_depths)

    return edge_types, node_depths

def place_on_grid(
    node: Node,
    in_grid: Optional[Grid] = None,
) -> Grid:
    grid = in_grid if in_grid is not None else Grid(node)

    if not node.is_region: return

    _, node_depths = _get_edge_info(node)

    for sub_node, depth in node_depths.items():
        sub_grid = grid.add_sub_grid(sub_node, y=depth)
        place_on_grid(sub_node, sub_grid)

    return grid
