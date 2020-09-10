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
from typing import Optional, Iterable
import weakref

from pygraphviz import AGraph

class Node:
    def __init__(self, 
        name: str,
        in_region: Optional[Region] = None,
        *args, **kwargs
    ):
        self.name = name
        self.in_region = in_region

        self.is_region = False

        self.prev = []
        self.next = []

    def _print_node(self, depth):
        print('{}{}'.format(depth*'  ', self))

    def print_nodes(self, depth: int = 0):
        self._print_node(depth)

    @property
    def in_region(self):
        return None if self._in_region is None else self._in_region()

    @in_region.setter
    def in_region(self, in_region: Optional[Region] = None):
        self._in_region = None if in_region is None else weakref.ref(in_region)
        if self.in_region is not None:
            self.in_region._add_node(self)

    def add_edge(self, to_node: Node):
        ''' "self" is the from_node from which
        the edge is made.
        '''
        self._add_next(to_node)
        to_node._add_prev(self)

    def _add_next(self, next_node: Node):
        self.next.append(next_node)

    def _add_prev(self, prev_node: Node):
        self.prev.append(prev_node)

    def _is_local_node(self, node: Node) -> bool:
        ''' Is this node within the same region as self.
        Cannot be another local node if in top-level.
        '''
        return False if self.in_region is None else (node in self.in_region.nodes)

    def _local_nodes(self, nodes: Iterable[Node]) -> Iterable[Node]:
        return [n for n in nodes if self._is_local_node(n)]

    def _other_nodes(self, nodes: Iterable[Node]) -> Iterable[Node]:
        return [n for n in nodes if not self._is_local_node(n)]

    @property
    def local_next(self) -> Iterable[Node]:
        return self._local_nodes(self.next)

    @property
    def local_prev(self) -> Iterable[Node]:
        return self._local_nodes(self.prev)

    @property
    def other_next(self) -> Iterable[Node]:
        return self._other_nodes(self.next)

    @property
    def other_prev(self) -> Iterable[Node]:
        return self._other_nodes(self.prev)

    @property
    def width(self) -> int:
        return max(1, len(self.local_prev), len(self.local_next))

    @property
    def height(self) -> int:
        return max(1, len(self.other_prev), len(self.other_next))

    def _node_names(self, nodes: Iterable[Node]) -> str:
        ''' Only return a string of the anode names
        for the given list of nodes.
        '''
        return ','.join(node.name for node in nodes)

    def __str__(self):
        return '{} <{}x{}> ({})({}) [{}][{}]'.format(
            self.name, 
            self.width,
            self.height,
            self._node_names(self.local_prev),
            self._node_names(self.local_next),
            self._node_names(self.other_prev),
            self._node_names(self.other_next),
        )

    def __repr__(self):
        return '{}'.format(
            self.name, 
        )

class Region(Node):
    def __init__(self,
        agraph: AGraph,
        in_region: Optional[Region] = None,
        *args, **kwargs
    ):
        self.agraph = agraph
        super().__init__(agraph.get_name(), in_region)
        self.is_region = True
        self.nodes = set()

    def _add_node(self, node: Node) -> None:
        self.nodes.add(node)

    def nodes_iter(self) -> Iterable[Node]:
        ''' Return first the individual nodes in this region
        and then the sub-regions, all alphabetically.
        '''
        for node in sorted(
            filter(lambda n: not n.is_region, self.nodes), 
            key=lambda n: n.name
        ):
            yield node

        for node in sorted(
            filter(lambda n: n.is_region, self.nodes), 
            key=lambda n: n.name
        ):
            yield node

    def print_nodes(self, depth: int = 0):
        self._print_node(depth)

        for node in self.nodes_iter():
            node.print_nodes(depth+1)

    @property
    def is_empty(self):
        return len(self.nodes) == 0

    @property
    def sorted_nodes(self):
        return sorted(self.nodes, key=lambda n: n.name)

    @property
    def sources(self):
        assert not self.is_empty, 'Cannot get sources of a {} with no nodes'.format(type(self).__name__)
        sources = []

        # Get all nodes that don't have inward connections.
        for node in self.sorted_nodes:
            if node.prev: continue
            sources.append(node)

        if sources: return sources

        # Pick a node out of nodes with fewest inward connections 
        # that also has the most outward connections.
        min_inward  = min(len(node.prev) for node in self.nodes)
        max_outward = max(len(node.next) for node in self.nodes)

        for node in self.sorted_nodes:
            if len(node.prev) != min_inward:  continue
            if len(node.next) != max_outward: continue
            sources.append(node)
            break

        assert sources, 'Somehow didn\'t find any source nodes.'
        return sources

    @property
    def width(self) -> int:
        return 100

    @property
    def height(self) -> int:
        return 100
