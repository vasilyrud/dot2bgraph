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
from typing import cast, List, Dict, Set, Tuple, Optional, Iterable, NewType, Iterator
from pathlib import Path
import glob
import os

from pygraphviz import AGraph

from blockgraph.utils.spinner import sp, SPINNER_OK
from blockgraph.converter.node import Node, Region
from blockgraph.converter.grid import Grid, place_on_grid
from blockgraph.locations import Locations, Direction, Color

ANodeToNode = NewType('ANodeToNode', Dict[str, Node])
EdgeToEdgeEnds = NewType('EdgeToEdgeEnds', Dict[Tuple[Node,Node], List[int]])
NodeToBlockId  = NewType('NodeToBlockId',  Dict[Node, int])
SubGridOffset  = NewType('SubGridOffset',  Tuple[Grid,int,int,int])

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

def _create_regions_nodes(
    agraph: AGraph,
    parent_region: Optional[Region] = None,
    in_anodes_to_nodes: Optional[ANodeToNode] = None,
) -> Tuple[Region, ANodeToNode]:
    ''' Create nodes in the cur_region and 
    its sub-regions.
    '''
    anodes_to_nodes: ANodeToNode = cast(ANodeToNode, {}) if in_anodes_to_nodes is None else in_anodes_to_nodes

    cur_region = Region(agraph.name, parent_region)

    if 'label' in agraph.graph_attr:
        cur_region.label = agraph.graph_attr['label']

    for anode in _direct_nodes(agraph, set(anodes_to_nodes.keys())):
        node = Node(anode, cur_region)

        if 'label' in anode.attr and anode.attr['label'] is not None:
            # "\N" in graphviz indicates "use node name"
            if anode.attr['label'] == '\\N':
                node.label = anode.name
            else:
                node.label = anode.attr['label']

        anodes_to_nodes[anode] = node

    for sub_agraph in _sorted_subgraphs(agraph):
        _create_regions_nodes(
            sub_agraph, 
            cur_region, 
            anodes_to_nodes, 
        )

    return cur_region, anodes_to_nodes

def _populate_subgraph(
    to_subgraph: AGraph,
    from_subgraph: AGraph,
    node_namespace: str,
    in_seen_nodes: Optional[Set[str]] = None,
    in_seen_edges: Optional[Set[str,str]] = None,
) -> None:
    ''' Copies from_subgraph recursively into to_subgraph.
    '''
    seen_nodes: Set[str] = set() if in_seen_nodes is None else in_seen_nodes
    seen_edges: Set[Tuple[str,str]] = set() if in_seen_edges is None else in_seen_edges

    for from_node in _direct_nodes(from_subgraph, seen_nodes):
        anode_name = f'{node_namespace}:{from_node}'

        if 'label' in from_node.attr and from_node.attr['label'] is not None:
            to_subgraph.add_node(anode_name, label=from_node.attr['label'])
        else:
            to_subgraph.add_node(anode_name)

        seen_nodes.add(anode_name)

    for from_edge in _direct_edges(from_subgraph, seen_edges):
        edge_name = (f'{node_namespace}:{from_edge[0]}',f'{node_namespace}:{from_edge[1]}')
        to_subgraph.add_edge(edge_name)

        seen_edges.add(edge_name)

    for sub_from_subgraph in _sorted_subgraphs(from_subgraph):
        subgraph_name = f'{node_namespace}:{sub_from_subgraph.name}'
        sub_to_subgraph = to_subgraph.add_subgraph(name=subgraph_name)

        if 'label' in sub_from_subgraph.graph_attr:
            sub_to_subgraph.graph_attr['label'] = sub_from_subgraph.graph_attr['label']

        _populate_subgraph(
            sub_to_subgraph,
            sub_from_subgraph,
            node_namespace,
            seen_nodes,
        )

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

def _get_color(depth: int, max_depth: int) -> Color:
    ''' Provide color shade based on relative depth.
    '''
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
) -> NodeToBlockId:
    node_to_block_id: NodeToBlockId = {}

    max_depth = max(item[3] for item in sub_grid_offsets.values())

    for node, offsets in sub_grid_offsets.items():
        sub_grid, offset_x, offset_y, depth = offsets
        block_id = locs.add_block(
            x=offset_x,
            y=offset_y,
            width=sub_grid.width,
            height=sub_grid.height,
            depth=depth,
            color=_get_color(depth, max_depth),
            label=node.label,
        )
        node_to_block_id[sub_grid.node] = block_id

    return node_to_block_id

def _create_locations_ee_local_next(
    sub_grid: Grid,
    locs: Locations,
    block_id: int,
    offset_x: int,
    offset_y: int,
    i: int,
):
    edge_x = offset_x + i
    edge_y = offset_y + sub_grid.height
    assert edge_x < offset_x + sub_grid.width
    return locs.add_edge_end(
        block_id=block_id, 
        x=edge_x, 
        y=edge_y, 
        direction=Direction.DOWN
    )

def _create_locations_ee_other_next(
    sub_grid: Grid,
    locs: Locations,
    block_id: int,
    offset_x: int,
    offset_y: int,
    i: int,
):
    edge_x = offset_x + sub_grid.width
    edge_y = offset_y + i
    assert edge_y < offset_y + sub_grid.height
    return locs.add_edge_end(
        block_id=block_id, 
        x=edge_x, 
        y=edge_y, 
        direction=Direction.RIGHT
    )

def _create_locations_ee_local_prev(
    sub_grid: Grid,
    locs: Locations,
    block_id: int,
    offset_x: int,
    offset_y: int,
    i: int,
):
    edge_x = offset_x + i
    edge_y = offset_y - 1
    assert edge_x < offset_x + sub_grid.width
    return locs.add_edge_end(
        block_id=block_id, 
        x=edge_x, 
        y=edge_y, 
        direction=Direction.DOWN
    )

def _create_locations_ee_other_prev(
    sub_grid: Grid,
    locs: Locations,
    block_id: int,
    offset_x: int,
    offset_y: int,
    i: int,
):
    edge_x = offset_x - 1
    edge_y = offset_y + i
    assert edge_y < offset_y + sub_grid.height
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
    return sorted(nodes, key=lambda n: sub_grid_offsets[n][1])

def _nodes_y_sorted(
    nodes: Iterable[Node],
    sub_grid_offsets: Dict[Node,SubGridOffset],
) -> Iterable[Node]:
    return sorted(nodes, key=lambda n: sub_grid_offsets[n][2])

def _create_locations_edge_ends(
    locs: Locations,
    sub_grid_offsets: Dict[Node,SubGridOffset],
    node_to_block_id: NodeToBlockId,
) -> Tuple[EdgeToEdgeEnds,EdgeToEdgeEnds]:
    ee_from: EdgeToEdgeEnds = cast(EdgeToEdgeEnds, {})
    ee_to:   EdgeToEdgeEnds = cast(EdgeToEdgeEnds, {})

    for sub_grid, offset_x, offset_y, _ in sub_grid_offsets.values():
        block_id = node_to_block_id[sub_grid.node]

        node_from = sub_grid.node

        for i, node_to in enumerate(_nodes_x_sorted(node_from.local_next, sub_grid_offsets)):
            edge_end_id = _create_locations_ee_local_next(sub_grid, locs, block_id, offset_x, offset_y, i)
            ee_from.setdefault((node_from, node_to), []).append(edge_end_id)

        for i, node_to in enumerate(_nodes_y_sorted(node_from.other_next, sub_grid_offsets)):
            edge_end_id = _create_locations_ee_other_next(sub_grid, locs, block_id, offset_x, offset_y, i)
            ee_from.setdefault((node_from, node_to), []).append(edge_end_id)

        node_to = sub_grid.node

        for i, node_from in enumerate(_nodes_x_sorted(node_to.local_prev, sub_grid_offsets)):
            edge_end_id = _create_locations_ee_local_prev(sub_grid, locs, block_id, offset_x, offset_y, i)
            ee_to.setdefault((node_from, node_to), []).append(edge_end_id)

        for i, node_from in enumerate(_nodes_y_sorted(node_to.other_prev, sub_grid_offsets)):
            edge_end_id = _create_locations_ee_other_prev(sub_grid, locs, block_id, offset_x, offset_y, i)
            ee_to.setdefault((node_from, node_to), []).append(edge_end_id)
    
    return ee_from, ee_to

def _create_locations_edges(
    locs: Locations,
    ee_from: EdgeToEdgeEnds,
    ee_to:   EdgeToEdgeEnds,
) -> None:

    for edge, edge_end_ids_from in ee_from.items():
        assert edge in ee_to
        assert len(edge_end_ids_from) == len(ee_to[edge])

        for i, edge_end_id_from in enumerate(edge_end_ids_from):
            edge_end_id_to = ee_to[edge][i]
            locs.add_edge(edge_end_id_from, edge_end_id_to)

def _regions2grids(base_region: Region) -> Grid:
    return place_on_grid(base_region, 2, 3)

def _grids2locations(
    grid: Grid,
) -> Locations:
    ''' Place a single grid's content into
    locations.
    '''
    locs: Locations = Locations()

    with sp(type='spinner') as spinner:
        spinner.text = 'Creating bgraph offsets'
        sub_grid_offsets = {grid.node: (grid,x,y,d) for grid, x, y, d in _iter_sub_grid_offsets(grid)}

        spinner.text = 'Creating bgraph blocks'
        node_to_block_id = _create_locations_blocks(locs, sub_grid_offsets)

        spinner.text = 'Creating bgraph edge ends'
        ee_from, ee_to = _create_locations_edge_ends(locs, sub_grid_offsets, node_to_block_id)

        spinner.text = 'Creating bgraph edges'
        _create_locations_edges(locs, ee_from, ee_to)

        spinner.text = 'Creating bgraph'
        spinner.ok(SPINNER_OK)

    return locs

def _agraph2locations(agraph: AGraph) -> Locations:
    with sp(type='spinner') as spinner:
        spinner.text = 'Parsing dot graph'
        base_region = _agraph2regions(agraph)
        spinner.ok(SPINNER_OK)

    with sp(type='spinner') as spinner:
        spinner.text='Placing on grid'
        base_grid = _regions2grids(base_region)
        spinner.ok(SPINNER_OK)

    locations = _grids2locations(base_grid)
    
    return locations

def dot2locations(dotfile: Path) -> Locations:
    assert dotfile.is_file()
    agraph = AGraph(string=dotfile.read_text(), label=dotfile.name)
    return _agraph2locations(agraph)

def _dot_files_in_dir(dotdir):
    return sorted(glob.iglob(os.path.join(dotdir, '**/*.dot'), recursive=True))

def _recursive_agraph(dotdir: Path) -> AGraph:
    assert dotdir.is_dir()

    root_path = dotdir.expanduser()
    root_folder = root_path.name

    agraph = AGraph(strict=False, directed=True, name=root_folder, label=root_folder)

    for found_file in sp(type='bar',
        items=_dot_files_in_dir(root_path),
        text='Loading dot file',
    ):
        dotfile = Path(found_file)
        rel_path = os.path.normpath(os.path.relpath(dotfile, root_path))
        split_path = rel_path.split(os.sep)

        prev_subgraph = agraph
        prev_folder = root_folder
        for folder in split_path:
            cur_folder = os.path.join(prev_folder, folder)

            cur_subgraph = prev_subgraph.get_subgraph(cur_folder)
            if cur_subgraph is None:
                cur_subgraph = prev_subgraph.add_subgraph(name=cur_folder, label=cur_folder)

            prev_subgraph = cur_subgraph
            prev_folder = cur_folder

        from_agraph = AGraph(string=dotfile.read_text())
        _populate_subgraph(prev_subgraph, from_agraph, os.path.join(root_folder, rel_path))

    return agraph

def dots2locations(dotdir: Path) -> Locations:
    agraph = _recursive_agraph(dotdir)
    return _agraph2locations(agraph)
