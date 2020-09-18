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
from typing import Dict, NewType

from pygraphviz import AGraph

from blockgraph.converter.node import Node, Region
from blockgraph.locations import Locations

ANodeToNode = NewType('ANodeToNode', Dict[str, Node])

def _sorted_subgraphs(agraph: AGraph) -> Iterable[AGraph]:
    ''' Normally, graphviz sorts subgraphs by time 
    when they were created, but there is a bug:
    https://gitlab.com/graphviz/graphviz/-/issues/1767
    which prevented this from happening.
    For now, use alphabetical order.
    '''
    return sorted(agraph.subgraphs_iter(), key=lambda sg: sg.name)

def _direct_nodes(
    agraph: AGraph, 
    seen_nodes: Set[str],
) -> Set[str]:
    ''' Get only the nodes that are part of
    the agraph itself, but not part of the
    agraph's sub-graphs and not part of nodes
    that have already been seen by its siblings.
    '''
    assert agraph is not None, 'AGraph is None'

    all_nodes = set(agraph.nodes())
    sub_agraph_nodes = set()

    for sub_agraph in _sorted_subgraphs(agraph):
        sub_agraph_nodes.update(sub_agraph.nodes())

    direct_nodes = all_nodes - sub_agraph_nodes - seen_nodes

    return direct_nodes

def _create_regions_nodes(
    agraph: AGraph,
    parent_region: Optional[Region] = None,
    in_anodes_to_nodes: Optional[ANodeToNode] = None,
) -> None:
    ''' Create nodes in the cur_region and 
    its sub-regions.
    '''
    anodes_to_nodes = {} if in_anodes_to_nodes is None else in_anodes_to_nodes

    cur_region = Region(agraph.name, parent_region)

    for anode in _direct_nodes(agraph, set(anodes_to_nodes.keys())):
        node = Node(anode, cur_region)
        anodes_to_nodes[anode] = node

    for sub_agraph in _sorted_subgraphs(agraph):
        _create_regions_nodes(
            sub_agraph, 
            cur_region, 
            anodes_to_nodes, 
        )

    return cur_region, anodes_to_nodes

def _create_edges(
    base_agraph: AGraph, 
    anodes_to_nodes: ANodeToNode,
) -> None:
    ''' Convert all the edges in the agraph to
    Nodes' edges.
    '''
    for asource, adest in base_agraph.edges_iter():
        from_node = anodes_to_nodes[asource]
        to_node   = anodes_to_nodes[adest]

        from_node.add_edge(to_node)

def _agraph2regions(agraph: AGraph) -> Region:
    ''' Create graph consisting of Regions
    based on the graph consisting of AGraphs.
    '''
    base_region, anodes_to_nodes = _create_regions_nodes(agraph)
    _create_edges(agraph, anodes_to_nodes)

    return base_region

def _sources(region):
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

def _regions2locations(base_region: Region) -> Locations:
    locations = Locations()

    # Determine sources and sinks
    

    # Determine cur_region depth
    # Determine cur_region width
    # Place nodes in the region
    # Center nodes

    return locations

def dot2locations(dot: str) -> Locations:

    agraph = AGraph(string=dot)

    # print('VAS nodes')
    # print(agraph.nodes())

    # print('VAS subg')
    # print(agraph.subgraphs()[0])
    # print(agraph.subgraphs()[0].subgraphs()[0])

    base_region = _agraph2regions(agraph)
    base_region.print_nodes()

    locations = _regions2locations(base_region)

    return locations
