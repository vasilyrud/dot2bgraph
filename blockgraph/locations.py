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
from typing import Optional, Iterable
import weakref

from pygraphviz import AGraph

def add_regions(cur_region: Region):
    for sub_graph in cur_region.agraph.subgraphs():
        sub_region = Region(sub_graph, cur_region)
        cur_region.add_node(sub_region)
        add_regions(sub_region)

def dot2locations(dot: str):
    agraph = AGraph(string=dot)

    print('VAS nodes')
    print(agraph.nodes())

    print('VAS subg')
    print(agraph.subgraphs()[0])
    print(agraph.subgraphs()[0].subgraphs()[0])

    base_region = Region(agraph)
    add_regions(base_region)


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
        in_region: Optional[Region] = None,
        *args, **kwargs
    ):
        if in_region is not None:
            self.in_region = weakref.ref(in_region)
        self.is_region = False

class Region(Node):
    def __init__(self,
        agraph: AGraph,
        in_region: Optional[Region] = None,
        *args, **kwargs
    ):
        self.agraph = agraph
        super().__init__(in_region)
        self.nodes = []
        self.is_region = True

    def add_node(self, node: Node):
        self.nodes.append(node)

class Locations:
    def __init__(self):
        pass
