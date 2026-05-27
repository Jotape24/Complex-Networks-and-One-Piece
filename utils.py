import networkx as nx

@nx._dispatchable(
    graphs="B", preserve_node_attrs=True, preserve_graph_attrs=True, returns_graph=True
)
def projected_graph_custom(B, nodes, multigraph=False):
    r"""Returns the projection of B onto one of its node sets.

    Returns the graph G that is the projection of the bipartite graph B
    onto the specified nodes. They retain their attributes and are connected
    in G if they have a common neighbor in B. Deleted nodes maintain their
    attributes as an edge.

    Parameters
    ----------
    B : NetworkX graph
      The input graph should be bipartite.

    nodes : list or iterable
      Nodes to project onto (the "bottom" nodes).

    multigraph: bool (default=False)
       If True return a multigraph where the multiple edges represent multiple
       shared neighbors.  They edge key in the multigraph is assigned to the
       label of the neighbor.

    Returns
    -------
    Graph : NetworkX graph or multigraph
       A graph that is the projection onto the given nodes, maintaining both
       type of nodes attributes, one as a node and the other type as an edge.
    """
    if B.is_multigraph():
        raise nx.NetworkXError("not defined for multigraphs")
    directed = False
    G = nx.MultiGraph()
    G.graph.update(B.graph)
    G.add_nodes_from((n, B.nodes[n]) for n in nodes)
    for u in nodes:
        nbrs2 = {v for nbr in B[u] for v in B[nbr] if v != u}
        for n in nbrs2:
            if directed:
                links = set(B[u]) & set(B.pred[n])
            else:
                links = set(B[u]) & set(B[n])
            for l in links:
                if not G.has_edge(u, n, l):
                    d_attr = B.nodes[l]
                    G.add_edge(u, n, key=l)
                    nx.set_edge_attributes(G, {(u, n, l): d_attr})
    if not multigraph:
        directed = False
        G2 = nx.Graph()
        G2.graph.update(B.graph)
        G2.add_nodes_from((n, B.nodes[n]) for n in nodes)
        g_nodes = G.nodes()
        for u in g_nodes:
            # revisar los links de u
            for n in G.neighbors(u):
                if not G2.has_edge(u, n):
                    votes = 0
                    pages = 0
                    rating = 0
                    episodes = []
                    edge_data = G.get_edge_data(u, n)
                    for edge_key, attrs in edge_data.items():
                        pages += attrs["n de paginas"]
                        votes += attrs["votos"]
                        rating += attrs["votos"]*attrs["rating"]
                        episodes.append(edge_key)
                    d_attr = {"n de paginas": pages, "rating": rating/votes, "votos": votes, "n episodios": len(episodes)}
                    G2.add_edge(u, n)
                    nx.set_edge_attributes(G2, {(u, n): d_attr})
        return G2
    return G