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
        self.in_region = None if in_region is None else weakref.ref(in_region)
        self.nodes = [] # Empty for non-region

        self.prev = []
        self.next = []

    def add_next(self, next_node: Node):
        self.next.append(next_node)

    def add_prev(self, prev_node: Node):
        self.prev.append(prev_node)

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
        print('{}{}'.format(depth*'  ', self))

        for node in self.nodes_iter():
            node.print_nodes(depth+1)

    def __is_local_node(self, node: Node) -> bool:
        ''' Is this node within the same region as self.
        Cannot be another local node if in top-level.
        '''
        if self.in_region is None:
            return False

        return node in self.in_region().nodes

    def __local_nodes(self, nodes: Iterable[Node]) -> Iterable[Node]:
        return [n for n in nodes if self.__is_local_node(n)]

    def __other_nodes(self, nodes: Iterable[Node]) -> Iterable[Node]:
        return [n for n in nodes if not self.__is_local_node(n)]

    @property
    def local_next(self) -> Iterable[Node]:
        return self.__local_nodes(self.next)

    @property
    def local_prev(self) -> Iterable[Node]:
        return self.__local_nodes(self.prev)

    @property
    def other_next(self) -> Iterable[Node]:
        return self.__other_nodes(self.next)

    @property
    def other_prev(self) -> Iterable[Node]:
        return self.__other_nodes(self.prev)

    @property
    def is_region(self) -> bool:
        return len(self.nodes) > 0

    @property
    def width(self) -> int:
        return max(1, len(self.local_prev), len(self.local_next))

    @property
    def height(self) -> int:
        return max(1, len(self.other_prev), len(self.other_next))

    def __node_names(self, nodes: Iterable[Node]) -> str:
        ''' Only return a string of the anode names
        for the given list of nodes.
        '''
        return ','.join(node.name for node in nodes)

    def __repr__(self):
        return '{} <{}x{}> ({})({}) [{}][{}]'.format(
            self.name, 
            self.width,
            self.height,
            self.__node_names(self.local_prev),
            self.__node_names(self.local_next),
            self.__node_names(self.other_prev),
            self.__node_names(self.other_next),
        )

class Region(Node):
    def __init__(self,
        agraph: AGraph,
        in_region: Optional[Region] = None,
        *args, **kwargs
    ):
        self.agraph = agraph
        super().__init__(agraph.get_name(), in_region)

    def add_node(self, node: Node) -> None:
        self.nodes.append(node)

    def __width(self) -> int:
        return 100

    @property
    def width(self) -> int:
        return 100

    @property
    def height(self) -> int:
        return 100