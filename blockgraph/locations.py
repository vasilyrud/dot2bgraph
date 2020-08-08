# Copyright 2019 Vasily Rudchenko - bgraph
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
from typing import Optional, Iterable, Dict
import weakref

from pygraphviz import AGraph

def add_regions_nodes(
    cur_region: Region,
    anodes_to_nodes: Dict[str, Node],
) -> None:
    for anode in direct_nodes(cur_region.agraph):
        node = Node(anode, cur_region)
        cur_region.add_node(node)
        anodes_to_nodes[anode] = node

    for sub_agraph in cur_region.agraph.subgraphs_iter():
        sub_region = Region(sub_agraph, cur_region)
        cur_region.add_node(sub_region)
        add_regions_nodes(sub_region, anodes_to_nodes)

def direct_nodes(agraph: AGraph) -> set:
    all_nodes = set(agraph.nodes())
    sub_agraph_nodes = set()

    for sub_agraph in agraph.subgraphs_iter():
        sub_agraph_nodes.update(sub_agraph.nodes())

    return all_nodes - sub_agraph_nodes

def add_edges(
    base_region: Region, 
    anodes_to_nodes: Dict[str, Node],
) -> None:
    for asource, adest in base_region.agraph.edges_iter():
        from_node = anodes_to_nodes[asource]
        to_node   = anodes_to_nodes[adest]

        from_node.add_next(to_node)
        to_node.add_prev(from_node)

def dot2locations(dot: str):
    agraph = AGraph(string=dot)

    # print('VAS nodes')
    # print(agraph.nodes())

    # print('VAS subg')
    # print(agraph.subgraphs()[0])
    # print(agraph.subgraphs()[0].subgraphs()[0])

    anodes_to_nodes = {}
    base_region = Region(agraph)
    add_regions_nodes(base_region, anodes_to_nodes)
    add_edges(base_region, anodes_to_nodes)

    # print(base_region)
    base_region.print_nodes()

    # for all the Nodes in the base region:
    #     Generate node size recursively
    # Determine sources and sinks
    # Determine cur_region depth
    # Determin cur_region width
    # Place nodes in the region
    # Center nodes

    return None

class Node:
    def __init__(self, 
        name: str,
        in_region: Optional[Region] = None,
        *args, **kwargs
    ):
        self.name = name
        if in_region is not None:
            self.in_region = weakref.ref(in_region)
        self.nodes = [] # Empty for non-region

        self.prev = []
        self.next = []

    def add_next(self, next_node: Node):
        self.next.append(next_node)

    def add_prev(self, prev_node: Node):
        self.prev.append(prev_node)

    def __print_anodes(self, nodes: Iterable[Node]) -> str:
        ''' Only return the anode names
        for the given list of nodes.
        '''

        return ','.join(node.name for node in nodes)

    @property
    def is_region(self) -> bool:
        return len(self.nodes) > 0

    def print_nodes(self, depth: int = 0):
        print('{}{}'.format(depth*'  ', self))

        for node in self.nodes:
            node.print_nodes(depth+1)

    def __repr__(self):
        return '{} <{}> ({}) ({})'.format(
            self.name, 
            hex(id(self)),
            self.__print_anodes(self.prev),
            self.__print_anodes(self.next),
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

class Locations:
    def __init__(self):
        pass
