# Random hierarchical DAG generator 

from random import seed, random, randrange
from pygraphviz import AGraph

global_id = 0

def add_edges(subgraph, old_nodes, new_nodes, do_add_edge):
    for old_node in old_nodes:
        for new_node in new_nodes:
            if do_add_edge():
                subgraph.add_edge((old_node, new_node))

def add_nodes(subgraph, global_nodes):
    global global_id
    local_nodes = []

    for _ in range(randrange(2, 12)):
        new_nodes = []

        for _ in range(randrange(1, 3)):
            new_node = str(global_id)
            global_id += 1

            new_nodes.append(new_node)

            # Removed to prevent inclusion of unconnected nodes
            # subgraph.add_node(new_node)

        add_edges(subgraph,  local_nodes, new_nodes, lambda: random() <= 0.1)
        add_edges(subgraph, global_nodes, new_nodes, lambda: random() <= 0.00001)
        local_nodes += new_nodes

    global_nodes += local_nodes

def do_add_subgraph(depth):
    return random() <= (1.3 ** (1.25 - depth) - 0.4)

def add_subgraphs(cur_subgraph, global_nodes, depth=0):
    global global_id
    new_subgraphs = []

    for _ in range(12):
        if do_add_subgraph(depth):
            new_subgraph = cur_subgraph.add_subgraph(name=f'cluster{str(global_id)}')
            global_id += 1
            new_subgraphs.append(new_subgraph)

    if new_subgraphs:
        for new_subgraph in new_subgraphs:
            add_subgraphs(new_subgraph, global_nodes, depth + 1)
    else:
        add_nodes(cur_subgraph, global_nodes)

def main():
    global global_id
    seed(0)

    graph = AGraph(strict=False, directed=True, name='G')

    global_nodes = []
    add_subgraphs(graph, global_nodes)

    print(graph)

if __name__ == "__main__":
    main()
