# Random hierarchical DAG generator 

from random import seed, random, randrange
from pygraphviz import AGraph

global_id = 0

def do_add_edge():
    return random() <= 0.1

def add_edges(subgraph, old_nodes, new_nodes):
    for old_node in old_nodes:
        for new_node in new_nodes:
            if do_add_edge():
                subgraph.add_edge((old_node, new_node))

def add_nodes(subgraph):
    global global_id
    all_nodes = []

    for _ in range(randrange(2, 12)):
        new_nodes = []

        for _ in range(randrange(1, 3)):
            new_node = str(global_id)
            global_id += 1

            new_nodes.append(new_node)

            # Removed to prevent inclusion of unconnected nodes
            # subgraph.add_node(new_node)

        add_edges(subgraph, all_nodes, new_nodes)
        all_nodes += new_nodes

def do_add_subgraph(depth):
    return random() <= (1.3 ** (1.25 - depth) - 0.4)

def add_subgraphs(cur_subgraph, depth=0):
    global global_id
    new_subgraphs = []

    for _ in range(10):
        if do_add_subgraph(depth):
            new_subgraph = cur_subgraph.add_subgraph(name=str(global_id))
            global_id += 1
            new_subgraphs.append(new_subgraph)

    if new_subgraphs:
        for new_subgraph in new_subgraphs:
            add_subgraphs(new_subgraph, depth + 1)
    else:
        add_nodes(cur_subgraph)

def main():
    global global_id
    seed(0)

    graph = AGraph(strict=False, directed=True, name='G')
    add_subgraphs(graph)

    print(graph)

if __name__ == "__main__":
    main()
