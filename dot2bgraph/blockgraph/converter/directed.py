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
from typing import cast, List, Dict, Set, Tuple, Optional, Iterable, NewType
import inspect
import glob
import os

from pygraphviz import AGraph
from colour import Color

from blockgraph.converter.node import Node, Region
from blockgraph.converter.grid import Grid, place_on_grid
from blockgraph.locations import Locations, Direction

ANodeToNode = NewType('ANodeToNode', Dict[str, Node])
EdgeToEdgeEnds = NewType('EdgeToEdgeEnds', Dict[Tuple[Node,Node], List[int]])
NodeToBlockId  = NewType('NodeToBlockId',  Dict[Node, int])

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
        to_subgraph.add_node(anode_name)
        seen_nodes.add(anode_name)

    for from_edge in _direct_edges(from_subgraph, seen_edges):
        edge_name = (f'{node_namespace}:{from_edge[0]}',f'{node_namespace}:{from_edge[1]}')
        to_subgraph.add_edge(edge_name)
        seen_edges.add(edge_name)

    for sub_from_subgraph in _sorted_subgraphs(from_subgraph):
        subgraph_name = f'{node_namespace}:{sub_from_subgraph.name}'
        sub_to_subgraph = to_subgraph.add_subgraph(name=subgraph_name)

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

def _get_color(depth: int, max_depth: int) -> str:
    ''' Provide color shade based on relative depth.
    '''

    shift = 0.2*max_depth
    max_val = max_depth + 2*shift
    val = depth + shift
    col = 1 - val/max_val

    color = Color(rgb=(col, col, col))
    return color.hex_l

def _iter_sub_grid_offsets(
    grid: Grid,
    tot_offset_x: Optional[int] = 0,
    tot_offset_y: Optional[int] = 0,
    depth: Optional[int] = 0,
) -> Iterable[Tuple[Grid,int,int,int]]:

    # Caller is different from self
    if inspect.stack()[1].function != inspect.stack()[0].function:
        yield grid, tot_offset_x, tot_offset_y, depth

    new_depth = depth + 1
    sub_grids = []

    for offset_y, y in grid.iter_offset_y():
        for offset_x, x in grid.iter_offset_x(y):
            sub_grid = grid.sub_grid_from_coord(x, y)

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
    grid: Grid, 
    locs: Locations,
) -> NodeToBlockId:
    node_to_block_id: NodeToBlockId = {}

    max_depth = max(item[3] for item in _iter_sub_grid_offsets(grid))

    for sub_grid, offset_x, offset_y, depth in _iter_sub_grid_offsets(grid):
        block_id = locs.add_block(
            x=offset_x,
            y=offset_y,
            width=sub_grid.width,
            height=sub_grid.height,
            depth=depth,
            color=_get_color(depth, max_depth),
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

def _create_locations_edge_ends(
    grid: Grid, 
    locs: Locations,
    node_to_block_id: NodeToBlockId,
) -> Tuple[EdgeToEdgeEnds,EdgeToEdgeEnds]:
    ee_from: EdgeToEdgeEnds = cast(EdgeToEdgeEnds, {})
    ee_to:   EdgeToEdgeEnds = cast(EdgeToEdgeEnds, {})

    for sub_grid, offset_x, offset_y, depth in _iter_sub_grid_offsets(grid):
        block_id = node_to_block_id[sub_grid.node]

        node_from = sub_grid.node

        for i, node_to in enumerate(node_from.local_next):
            edge_end_id = _create_locations_ee_local_next(sub_grid, locs, block_id, offset_x, offset_y, i)
            ee_from.setdefault((node_from, node_to), []).append(edge_end_id)

        for i, node_to in enumerate(node_from.other_next):
            edge_end_id = _create_locations_ee_other_next(sub_grid, locs, block_id, offset_x, offset_y, i)
            ee_from.setdefault((node_from, node_to), []).append(edge_end_id)

        node_to = sub_grid.node

        for i, node_from in enumerate(node_to.local_prev):
            edge_end_id = _create_locations_ee_local_prev(sub_grid, locs, block_id, offset_x, offset_y, i)
            ee_to.setdefault((node_from, node_to), []).append(edge_end_id)

        for i, node_from in enumerate(node_to.other_prev):
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
    grid = Grid(base_region,
        padding_l=2,
        padding_r=2,
        padding_t=2,
        padding_b=2,
        space_col=3,
        space_row=3,
    )
    return place_on_grid(base_region, grid)

def _grids2locations(
    grid: Grid,
) -> Locations:
    ''' Place a single grid's content into
    locations.
    '''
    locs: Locations = Locations()

    node_to_block_id = _create_locations_blocks(grid, locs)
    ee_from, ee_to = _create_locations_edge_ends(grid, locs, node_to_block_id)
    _create_locations_edges(locs, ee_from, ee_to)

    return locs

def agraph2locations(agraph: AGraph) -> Locations:
    base_region = _agraph2regions(agraph)
    base_grid = _regions2grids(base_region)
    return _grids2locations(base_grid)

def dot2locations(dotfile: str) -> Locations:
    assert os.path.isfile(dotfile)

    with open(dotfile, 'r') as f:
        dot = ''.join(f.readlines())

    agraph = AGraph(string=dot)
    return agraph2locations(agraph)

def dots2locations(dotdir: str):
    assert os.path.isdir(dotdir)

    root_dir = os.path.expanduser(dotdir)
    root_name = os.path.split(root_dir)[-1]

    agraph = AGraph(strict=False, directed=True, name=root_name)

    for filename in glob.iglob(os.path.join(root_dir, '**/*.dot'), recursive=True):
        path = os.path.normpath(os.path.relpath(filename, root_dir))
        split_path = path.split(os.sep)

        prev_subgraph = agraph
        prev_dir = root_name
        for dir in split_path:
            next_dir = os.path.join(prev_dir, dir)
            prev_subgraph = prev_subgraph.add_subgraph(name=next_dir)
            prev_dir = next_dir

        with open(filename, 'r') as f:
            dot = ''.join(f.readlines())

        from_agraph = AGraph(string=dot)
        _populate_subgraph(prev_subgraph, from_agraph, os.path.join(root_name, path))

    return agraph2locations(agraph)
