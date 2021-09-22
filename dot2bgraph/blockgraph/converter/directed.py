# Copyright 2020 Vasily Rudchenko - dot2bgraph
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
from typing import cast, List, Dict, Set, Tuple, Optional, Iterable, NewType, Iterator
from pathlib import Path
from collections import namedtuple
import glob
import os

from pygraphviz import AGraph

from blockgraph.utils.spinner import sp, SPINNER_OK
from blockgraph.converter.node import Node, Region
from blockgraph.converter.grid import Grid, place_on_grid
from blockgraph.locations import Locations, Direction, Color

ANodeToNode = NewType('ANodeToNode', Dict[str, Node])
NodeToNodeLabel = NewType('NodeToNodeLabel', Dict[Node, str])
EdgeToEdgeLabel = NewType('EdgeToEdgeLabel', Dict[Tuple[Node,Node], str])
EdgeToEdgeEnds = NewType('EdgeToEdgeEnds', Dict[Tuple[Node,Node], List[int]])
NodeToBlockId  = NewType('NodeToBlockId',  Dict[Node, int])

SubGridOffset = namedtuple('SubGridOffset', ['sub_grid', 'x', 'y', 'depth'])

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

def _direct_edges(
    agraph: AGraph, 
    seen_edges: Set[Tuple[str,str]],
) -> Set[Tuple[str,str]]:
    ''' Get direct edges in the same way as with
    nodes in _direct_nodes.
    '''
    assert agraph is not None, 'AGraph is None'

    all_edges = set(agraph.edges())
    sub_agraph_edges = set()

    for sub_agraph in _sorted_subgraphs(agraph):
        sub_agraph_edges.update(sub_agraph.edges())

    direct_edges = all_edges - sub_agraph_edges - seen_edges

    return direct_edges

def _add_graph_label(agraph, region, node_labels):
    if 'label' in agraph.graph_attr and agraph.graph_attr['label']:
        node_labels[region] = agraph.graph_attr['label']

def _add_node_label(anode, node, node_labels):
    if 'label' in anode.attr and anode.attr['label']:
        if anode.attr['label'] == '\\N':
            node_labels[node] = anode.name
        else:
            node_labels[node] = anode.attr['label']

def _add_edge_label(aedge, from_node, to_node, edge_labels):
    if 'label' in aedge.attr and aedge.attr['label']:
        edge_labels[(from_node, to_node)] = aedge.attr['label']

def _create_regions_nodes(
    agraph: AGraph,
    parent_region: Optional[Region] = None,
    in_anodes_to_nodes: Optional[ANodeToNode] = None,
    in_node_labels: Optional[NodeToNodeLabel] = None,
) -> Tuple[Region, ANodeToNode, NodeToNodeLabel]:
    ''' Create nodes in the cur_region and 
    its sub-regions.
    '''
    anodes_to_nodes: ANodeToNode = cast(ANodeToNode, {}) if in_anodes_to_nodes is None else in_anodes_to_nodes
    node_labels: NodeToNodeLabel = cast(NodeToNodeLabel, {}) if in_node_labels is None else in_node_labels

    cur_region = Region(agraph.name, parent_region)
    _add_graph_label(agraph, cur_region, node_labels)

    for anode in _direct_nodes(agraph, set(anodes_to_nodes.keys())):
        node = Node(anode, cur_region)
        _add_node_label(anode, node, node_labels)

        anodes_to_nodes[anode] = node

    for sub_agraph in _sorted_subgraphs(agraph):
        _create_regions_nodes(
            sub_agraph, 
            cur_region, 
            anodes_to_nodes, 
            node_labels,
        )

    return cur_region, anodes_to_nodes, node_labels

def _create_edges(
    base_agraph: AGraph, 
    anodes_to_nodes: ANodeToNode,
) -> EdgeToEdgeLabel:
    ''' Convert all the edges in the agraph to
    Nodes' edges.
    '''
    edge_labels: EdgeToEdgeLabel = {}

    for aedge in base_agraph.edges_iter():
        asource, adest = aedge

        from_node = anodes_to_nodes[asource]
        to_node   = anodes_to_nodes[adest]

        from_node.add_edge(to_node)
        _add_edge_label(aedge, from_node, to_node, edge_labels)

    return edge_labels

def _agraph2regions(agraph: AGraph) -> Tuple[Region,NodeToNodeLabel,EdgeToEdgeLabel]:
    ''' Create graph consisting of Regions
    based on the graph consisting of AGraphs.
    '''
    base_region, anodes_to_nodes, node_labels = _create_regions_nodes(agraph)
    edge_labels = _create_edges(agraph, anodes_to_nodes)

    return base_region, node_labels, edge_labels

def _get_color(depth: int, max_depth: int) -> Color:
    ''' Provide color shade based on relative depth.
    '''
    if max_depth == 0:
        max_depth = 1

    shift = 0.2*max_depth
    max_val = max_depth + 2*shift
    val = depth + shift
    col = 1 - val/max_val
    col = int(col * 255)

    return (col,col,col)

def _iter_sub_grid_offsets(
    grid: Grid,
    tot_offset_x: Optional[int] = 0,
    tot_offset_y: Optional[int] = 0,
    depth: Optional[int] = 0,
) -> Iterator[SubGridOffset]:

    if depth == 0:
        yield grid, tot_offset_x, tot_offset_y, depth

    new_depth = depth + 1
    sub_grids = []

    for offset_x, offset_y, sub_grid in grid.iter_offsets():
        new_offset_x = tot_offset_x + offset_x
        new_offset_y = tot_offset_y + offset_y

        yield sub_grid, new_offset_x, new_offset_y, new_depth
        sub_grids.append((sub_grid, new_offset_x, new_offset_y))

    for sub_grid, new_offset_x, new_offset_y in sub_grids:
        yield from _iter_sub_grid_offsets(
            sub_grid,
            tot_offset_x=new_offset_x,
            tot_offset_y=new_offset_y,
            depth=new_depth,
        )

def _create_locations_blocks(
    locs: Locations,
    sub_grid_offsets: Dict[Node,SubGridOffset],
    node_labels: NodeToNodeLabel,
) -> NodeToBlockId:
    node_to_block_id: NodeToBlockId = {}

    max_depth = max(item.depth for item in sub_grid_offsets.values())

    for node, offset in sub_grid_offsets.items():
        block_id = locs.add_block(
            x=offset.x,
            y=offset.y,
            width=offset.sub_grid.width,
            height=offset.sub_grid.height,
            depth=offset.depth,
            color=_get_color(offset.depth, max_depth),
            label=node_labels[node] if node in node_labels else None,
        )
        node_to_block_id[offset.sub_grid.node] = block_id

    return node_to_block_id

def _create_ee_local_next(
    locs: Locations,
    block_id: int,
    offset: SubGridOffset,
    i: int,
):
    edge_x = offset.x + i
    edge_y = offset.y + offset.sub_grid.height
    assert edge_x < offset.x + offset.sub_grid.width
    return locs.add_edge_end(
        block_id=block_id, 
        x=edge_x, 
        y=edge_y, 
        direction=Direction.DOWN
    )

def _create_ee_other_next(
    locs: Locations,
    block_id: int,
    offset: SubGridOffset,
    i: int,
):
    edge_x = offset.x + offset.sub_grid.width
    edge_y = offset.y + i
    assert edge_y < offset.y + offset.sub_grid.height
    return locs.add_edge_end(
        block_id=block_id, 
        x=edge_x, 
        y=edge_y, 
        direction=Direction.RIGHT
    )

def _create_ee_local_prev(
    locs: Locations,
    block_id: int,
    offset: SubGridOffset,
    i: int,
):
    edge_x = offset.x + i
    edge_y = offset.y - 1
    assert edge_x < offset.x + offset.sub_grid.width
    return locs.add_edge_end(
        block_id=block_id, 
        x=edge_x, 
        y=edge_y, 
        direction=Direction.DOWN
    )

def _create_ee_other_prev(
    locs: Locations,
    block_id: int,
    offset: SubGridOffset,
    i: int,
):
    edge_x = offset.x - 1
    edge_y = offset.y + i
    assert edge_y < offset.y + offset.sub_grid.height
    return locs.add_edge_end(
        block_id=block_id, 
        x=edge_x, 
        y=edge_y, 
        direction=Direction.RIGHT
    )

def _nodes_x_sorted(
    nodes: Iterable[Node],
    sub_grid_offsets: Dict[Node,SubGridOffset],
) -> Iterable[Node]:
    return sorted(nodes, key=lambda n: sub_grid_offsets[n].x)

def _nodes_y_sorted(
    nodes: Iterable[Node],
    sub_grid_offsets: Dict[Node,SubGridOffset],
) -> Iterable[Node]:
    return sorted(nodes, key=lambda n: sub_grid_offsets[n].y)

def _create_locations_edge_ends(
    locs: Locations,
    sub_grid_offsets: Dict[Node,SubGridOffset],
    node_to_block_id: NodeToBlockId,
) -> Tuple[EdgeToEdgeEnds,EdgeToEdgeEnds]:
    ee_from: EdgeToEdgeEnds = cast(EdgeToEdgeEnds, {})
    ee_to:   EdgeToEdgeEnds = cast(EdgeToEdgeEnds, {})

    for offset in sub_grid_offsets.values():
        block_id = node_to_block_id[offset.sub_grid.node]

        node_from = offset.sub_grid.node

        for i, node_to in enumerate(_nodes_x_sorted(node_from.local_next, sub_grid_offsets)):
            edge_end_id = _create_ee_local_next(locs, block_id, offset, i)
            ee_from.setdefault((node_from, node_to), []).append(edge_end_id)

        for i, node_to in enumerate(_nodes_y_sorted(node_from.other_next, sub_grid_offsets)):
            edge_end_id = _create_ee_other_next(locs, block_id, offset, i)
            ee_from.setdefault((node_from, node_to), []).append(edge_end_id)

        node_to = offset.sub_grid.node

        for i, node_from in enumerate(_nodes_x_sorted(node_to.local_prev, sub_grid_offsets)):
            edge_end_id = _create_ee_local_prev(locs, block_id, offset, i)
            ee_to.setdefault((node_from, node_to), []).append(edge_end_id)

        for i, node_from in enumerate(_nodes_y_sorted(node_to.other_prev, sub_grid_offsets)):
            edge_end_id = _create_ee_other_prev(locs, block_id, offset, i)
            ee_to.setdefault((node_from, node_to), []).append(edge_end_id)
    
    return ee_from, ee_to

def _create_locations_edges(
    locs: Locations,
    ee_from: EdgeToEdgeEnds,
    ee_to:   EdgeToEdgeEnds,
    edge_labels,
) -> None:

    for edge, edge_end_ids_from in ee_from.items():
        assert edge in ee_to
        assert len(edge_end_ids_from) == len(ee_to[edge])

        for i, edge_end_id_from in enumerate(edge_end_ids_from):
            edge_end_id_to = ee_to[edge][i]
            locs.add_edge(edge_end_id_from, edge_end_id_to)

            if edge in edge_labels:
                locs.edge_end(edge_end_id_from).label = edge_labels[edge]
                locs.edge_end(edge_end_id_to).label   = edge_labels[edge]

def _regions2grids(base_region: Region) -> Grid:
    return place_on_grid(base_region, 2, 3)

def _grids2locations(
    grid: Grid,
    node_labels: NodeToNodeLabel,
    edge_labels: EdgeToEdgeLabel,
) -> Locations:
    ''' Place a single grid's content into
    locations.
    '''
    locs: Locations = Locations()

    with sp(type='spinner') as spinner:
        spinner.text = 'Creating bgraph offsets'
        sub_grid_offsets = {
            grid.node: SubGridOffset(grid, x, y, d) 
            for grid, x, y, d in _iter_sub_grid_offsets(grid)
        }

        spinner.text = 'Creating bgraph blocks'
        node_to_block_id = _create_locations_blocks(locs, sub_grid_offsets, node_labels)

        spinner.text = 'Creating bgraph edge ends'
        ee_from, ee_to = _create_locations_edge_ends(locs, sub_grid_offsets, node_to_block_id)

        spinner.text = 'Creating bgraph edges'
        _create_locations_edges(locs, ee_from, ee_to, edge_labels)

        spinner.text = 'Creating bgraph'
        spinner.ok(SPINNER_OK)

    return locs

def _agraph2locations(agraph: AGraph) -> Locations:
    with sp(type='spinner') as spinner:
        spinner.text = 'Parsing dot graph'
        base_region, node_labels, edge_labels = _agraph2regions(agraph)
        spinner.ok(SPINNER_OK)

    with sp(type='spinner') as spinner:
        spinner.text='Placing on grid'
        base_grid = _regions2grids(base_region)
        spinner.ok(SPINNER_OK)

    locations = _grids2locations(base_grid, node_labels, edge_labels)
    
    return locations

def dot2locations(dotfile: Path) -> Locations:
    assert dotfile.is_file()
    agraph = AGraph(string=dotfile.read_text(), label=dotfile.name)
    return _agraph2locations(agraph)

def _add_subgraph_node(to_subgraph, node, node_name):
    if 'label' in node.attr and node.attr['label']:
        to_subgraph.add_node(node_name, label=node.attr['label'])
    else:
        to_subgraph.add_node(node_name)

def _add_subgraph_edge(to_subgraph, edge, edge_name):
    if 'label' in edge.attr and edge.attr['label']:
        to_subgraph.add_edge(edge_name, label=edge.attr['label'])
    else:
        to_subgraph.add_edge(edge_name)

def _add_subgraph_subgraph(to_subgraph, subgraph, subgraph_name):
    new_subgraph = to_subgraph.add_subgraph(name=subgraph_name)

    if 'label' in subgraph.graph_attr:
        new_subgraph.graph_attr['label'] = subgraph.graph_attr['label']

    return new_subgraph

def _populate_subgraph(
    to_subgraph: AGraph,
    from_subgraph: AGraph,
    node_namespace: str,
    in_seen_nodes: Optional[Set[str]] = None,
    in_seen_edges: Optional[Set[str,str]] = None,
) -> None:
    ''' Copies from_subgraph recursively into to_subgraph.
    Prepends "<node_namespace>:" to all node/edge/subgraph IDs.
    '''
    seen_nodes: Set[str] = set() if in_seen_nodes is None else in_seen_nodes
    seen_edges: Set[Tuple[str,str]] = set() if in_seen_edges is None else in_seen_edges

    for from_node in _direct_nodes(from_subgraph, seen_nodes):
        anode_name = f'{node_namespace}:{from_node}'

        _add_subgraph_node(to_subgraph, from_node, anode_name)
        seen_nodes.add(anode_name)

    for from_edge in _direct_edges(from_subgraph, seen_edges):
        edge_name = (
            f'{node_namespace}:{from_edge[0]}',
            f'{node_namespace}:{from_edge[1]}'
        )

        _add_subgraph_edge(to_subgraph, from_edge, edge_name)
        seen_edges.add(edge_name)

    for sub_from_subgraph in _sorted_subgraphs(from_subgraph):
        subgraph_name = f'{node_namespace}:{sub_from_subgraph.name}'

        sub_to_subgraph = _add_subgraph_subgraph(to_subgraph, sub_from_subgraph, subgraph_name)
        _populate_subgraph(
            sub_to_subgraph,
            sub_from_subgraph,
            node_namespace,
            seen_nodes,
        )

def _dot_files_in_dir(dotdir):
    return sorted(glob.iglob(os.path.join(dotdir, '**/*.dot'), recursive=True))

def _create_subgraphs_from_path(path, root_graph, root_folder):
    ''' Create (or re-use) subgraphs hierarchically matching
    folders in the file `path`. 

    Return the final child-most subgraph.

    For example, for "a/b/c.dot" create the subgraphs:
        a
         `- b
             `- c.dot
    and return the empty subgraph "c.dot".
    ''' 
    split_path = path.split(os.sep)

    parent_graph = root_graph
    parent_folder = root_folder

    for folder in split_path:
        child_folder = os.path.join(parent_folder, folder)

        child_graph = parent_graph.get_subgraph(child_folder)
        if child_graph is None:
            child_graph = parent_graph.add_subgraph(name=child_folder, label=child_folder)

        parent_graph = child_graph
        parent_folder = child_folder

    return parent_graph

def _recursive_agraph(dotdir: Path) -> AGraph:
    ''' Create an AGraph representing the hierarchy of
    dot graphs mirroring the file paths to those dot
    graphs and the graphs being subgraphs themselves.
    '''
    assert dotdir.is_dir()

    root_path = dotdir.expanduser()
    root_folder = root_path.name

    root_graph = AGraph(strict=False, directed=True, name=root_folder, label=root_folder)

    for found_file in sp(type='bar',
        items=_dot_files_in_dir(root_path),
        text='Loading dot file',
    ):
        dotfile = Path(found_file)
        rel_path = os.path.normpath(os.path.relpath(dotfile, root_path))

        new_subgraph = _create_subgraphs_from_path(rel_path, root_graph, root_folder)
        found_subgraph = AGraph(string=dotfile.read_text())
        node_namespace = os.path.join(root_folder, rel_path)

        _populate_subgraph(new_subgraph, found_subgraph, node_namespace)

    return root_graph

def dots2locations(dotdir: Path) -> Locations:
    agraph = _recursive_agraph(dotdir)
    return _agraph2locations(agraph)
