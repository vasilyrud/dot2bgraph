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
from collections import deque
from enum import Enum, auto

from blockgraph.converter.node import Node, Region

class _EdgeType(Enum):
    NORMAL = auto()
    FWD = auto()
    CROSS = auto()
    BACK = auto()

Coord = NewType('Coord', Tuple[int, int])
EdgeTypes = NewType('EdgeTypes', Dict[Tuple[Node,Node],_EdgeType])
NodeDepths = NewType('NodeDepths', Dict[Node, int])

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
        + - - +

        + - - + +       + - - - +
        | 0,4   |       | 2,4   |
        + - - - +       + - - - +
    '''

    MIN_INDEX=0

    def __init__(self, region: Region):
        self.region: Region = region

        self._node2coord: Dict[Node, Coord] = {}
        self._coord2node: Dict[int,Dict[int,Node]] = {}

    def has_node(self, node: Node) -> bool:
        return node in self._node2coord

    def get_x(self, node: Node) -> int:
        return self._node2coord[node][0]

    def get_y(self, node: Node) -> int:
        return self._node2coord[node][1]

    def add_node(self, 
        node: Node, 
        x: Optional[int] = None, 
        y: Optional[int] = None,
    ):
        ''' Add node to the given x,y location.
        If y is not specified, use the last available row.
        If x is not specified, add to the end of the row.
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

        assert node not in self._node2coord, 'Node {} already placed.'.format(node)
        self._node2coord[node] = (use_x,use_y)

        assert use_x not in self._coord2node[use_y], 'Location ({},{}) already occupied.'.format(use_x, use_y)
        self._coord2node[use_y][use_x] = node

    def del_node(self, node: Node):
        ''' Remove node from all of grid's data structures.
        '''
        coord = self._node2coord[node]
        x = coord[0]
        y = coord[1]

        del self._node2coord[node]
        del self._coord2node[y][x]
        if len(self._coord2node[y]) == 0:
            del self._coord2node[y]

def _sources(region: Region) -> Iterable[Node]:
    assert not region.is_empty, 'Cannot get sources of a {} with no nodes'.format(type(region).__name__)
    sources = []

    # Get all nodes that don't have inward connections.
    for node in region.nodes_sorted:
        if node.prev: continue
        sources.append(node)

    if sources: return sources

    # Pick a node out of nodes with fewest inward connections 
    # that also has the most outward connections.
    min_inward  = min(len(node.prev) for node in region.nodes)
    max_outward = max(len(node.next) for node in region.nodes)

    for node in region.nodes_sorted:
        if len(node.prev) != min_inward:  continue
        if len(node.next) != max_outward: continue
        sources.append(node)
        break

    assert sources, 'Somehow didn\'t find any source nodes.'
    return sources

class _SeenNodes:
    ''' Helper class to store info about nodes
    during traversal.
    '''
    def __init__(self):
        self.nodes: Set[Node] = set()

        self.time: int = 0
        self.start:  Dict[Node,int] = {}
        self.finish: Dict[Node,int] = {}

def _classify_edge(
    edge,
    edge_types,
    seen,
):
    cur_node  = edge[0]
    next_node = edge[1]

    if next_node not in seen.nodes:
        edge_type = _EdgeType.NORMAL

    elif next_node not in seen.finish:
        edge_type = _EdgeType.BACK

    elif seen.start[cur_node] < seen.start[next_node]:
        edge_type = _EdgeType.FWD

    else:
        edge_type = _EdgeType.CROSS

    edge_types[edge] = edge_type
    return edge_type

def _update_depth(
    edge,
    edge_types,
    depth,
    node_depths,
):
    next_node = edge[1]

    if edge in edge_types and edge_types[edge] == _EdgeType.BACK:
        return
    if next_node in node_depths and node_depths[next_node] > depth:
        return

    node_depths[next_node] = depth

def _get_edge_info_dfs(
    cur_node,
    edge_types,
    node_depths,
    seen,
    depth,
):
    ''' Helper function to classify all nodes in the
    graph by traversing in DFS order.
    Assumes caller iterates over source nodes.
    '''

    seen.time += 1
    seen.start[cur_node] = seen.time
    seen.nodes.add(cur_node)

    for next_node in cur_node.local_next:
        edge = (cur_node,next_node)

        _classify_edge(edge, edge_types, seen)
        _update_depth(edge, edge_types, depth, node_depths)

        if edge_types[edge] == _EdgeType.NORMAL:
            _get_edge_info_dfs(
                next_node,
                edge_types,
                node_depths,
                seen,
                depth+1,
            )

    seen.time += 1
    seen.finish[cur_node] = seen.time

def _get_edge_info(
    region: Region,
) -> Tuple[EdgeTypes,NodeDepths]:
    ''' Clasify edges in the graph based
    on their _EdgeType and nodes based on
    their depth from the source nodes.
    '''
    edge_types: EdgeTypes = {}
    node_depths: NodeDepths = {}
    seen = _SeenNodes()

    for source in _sources(region):
        assert source not in seen.nodes, 'Source node was used that does not allow source-driven DFS edge classification.'
        next_edge = (None, source)

        _update_depth(next_edge, edge_types, Grid.MIN_INDEX, node_depths)
        _get_edge_info_dfs(source, edge_types, node_depths, seen, Grid.MIN_INDEX+1)

    return edge_types, node_depths

def _place_nodes(grid, node_depths):
    for node, depth in node_depths.items():
        grid.add_node(node, y=depth)

def place_on_grid(
    region: Region,
):
    grid = Grid(region)

    edge_types, node_depths = _get_edge_info(region)
    _place_nodes(grid, node_depths)

    return grid, edge_types
