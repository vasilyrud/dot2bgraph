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

from typing import Dict, NewType

from pygraphviz import AGraph

from blockgraph.node import Node, Region

ANodeToNode = NewType('ANodeToNode', Dict[str, Node])

def __direct_nodes(agraph: AGraph) -> set:
    all_nodes = set(agraph.nodes())
    sub_agraph_nodes = set()

    for sub_agraph in agraph.subgraphs_iter():
        sub_agraph_nodes.update(sub_agraph.nodes())

    return all_nodes - sub_agraph_nodes

def __add_regions_nodes(
    cur_region: Region,
    anodes_to_nodes: ANodeToNode,
) -> None:
    for anode in __direct_nodes(cur_region.agraph):
        node = Node(anode, cur_region)
        cur_region.add_node(node)
        anodes_to_nodes[anode] = node

    for sub_agraph in cur_region.agraph.subgraphs_iter():
        sub_region = Region(sub_agraph, cur_region)
        cur_region.add_node(sub_region)
        __add_regions_nodes(sub_region, anodes_to_nodes)

def __add_edges(
    base_region: Region, 
    anodes_to_nodes: ANodeToNode,
) -> None:
    for asource, adest in base_region.agraph.edges_iter():
        from_node = anodes_to_nodes[asource]
        to_node   = anodes_to_nodes[adest]

        from_node.add_next(to_node)
        to_node.add_prev(from_node)

def __agraph2regions(agraph: AGraph):
    anodes_to_nodes: ANodeToNode = {}
    base_region = Region(agraph)

    __add_regions_nodes(base_region, anodes_to_nodes)
    __add_edges(base_region, anodes_to_nodes)

    return base_region

def __regions2locations(base_region: Region):
    locations = Locations(base_region)

    # Determine sources and sinks
    # Determine cur_region depth
    # Determine cur_region width
    # Place nodes in the region
    # Center nodes

    return locations

def dot2locations(dot: str):

    # print('VAS nodes')
    # print(agraph.nodes())

    # print('VAS subg')
    # print(agraph.subgraphs()[0])
    # print(agraph.subgraphs()[0].subgraphs()[0])

    agraph = AGraph(string=dot)

    base_region = __agraph2regions(agraph)
    base_region.print_nodes()

    locations = __regions2locations(base_region)

    return None

class Locations:
    def __init__(self, base_region: Region):
        self.base_region = base_region
