import networkx as nx
import pandas as pd
import ast
from networkx.algorithms import bipartite
import powerlaw


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

# Función para convertir string de lista a lista real
def parse_list(x):
    if pd.isna(x):
        return []
    try:
        return ast.literal_eval(x)
    except:
        return []

def bipartite_graph(df):
    """Este script crea un grafo bipartito entre episodios y staff, y guarda el grafo en formato GEXF para su análisis posterior."""

    # Columnas donde hay listas de personas
    staff_columns = ["guion", "arte", "animacion", "direccion"]
    value_columns = ["n de paginas", "rating", "votos"]

    # Crear grafo bipartito
    bipartite_graph = nx.Graph()

    for _, row in df.iterrows():
        episodio = f"ep_{int(row['episodio'])}"
        
        # Agregar nodo episodio
        bipartite_graph.add_node(episodio, bipartite="episode")

        value_dict = {}
        for val in value_columns:
            value_dict[val] = row[val]
        
        nx.set_node_attributes(bipartite_graph, {episodio: value_dict})

        # Iterar por todas las áreas del staff
        for col in staff_columns:
            personas = parse_list(row[col])
            
            for persona in personas:
                persona_clean = persona.split("(")[0].strip()

                # Agregar nodo persona
                if persona_clean == '':
                    continue
                bipartite_graph.add_node(persona_clean, bipartite="staff")

                # Agregar arista
                bipartite_graph.add_edge(persona_clean, episodio)


    print(f"Number of nodes: {bipartite_graph.number_of_nodes()}, Number of edges: {bipartite_graph.number_of_edges()}")
    nx.write_gexf(bipartite_graph, "one_piece.gexf")
    return bipartite_graph


def bipartite_projection(B, group):
    """Proyección del grafo bipartito para obtener relaciones entre el staff basado en los episodios en los que han trabajado juntos."""
    # Obtener nodos de staff
    staff_nodes = {n for n, d in B.nodes(data=True) if d["bipartite"] == group}

    # Proyección
    bipartite_staff = bipartite.weighted_projected_graph(B, staff_nodes)

    print(f"Number of nodes: {bipartite_staff.number_of_nodes()}, Number of edges: {bipartite_staff.number_of_edges()}")
    nx.write_gexf(bipartite_staff, f"one_piece_{group}_projection.gexf")
    return bipartite_staff



def weighted_episode_rating(B, df, group="staff"):
    """
    Calcula el rating promedio ponderado por votos para cada nodo perteneciente al grupo indicado.
    """

    nodes = {
        n for n, d in B.nodes(data=True)
        if d["bipartite"] == group
    }

    episode_info = (
        df.set_index("episodio")[["rating", "votos"]]
        .to_dict("index")
    )

    ratings = {}

    for node in nodes:

        weighted_sum = 0
        total_votes = 0

        for ep in B.neighbors(node):

            ep_num = int(ep.replace("ep_", ""))

            if ep_num not in episode_info:
                continue

            rating = episode_info[ep_num]["rating"]
            votes = episode_info[ep_num]["votos"]

            if pd.isna(rating) or pd.isna(votes):
                continue

            weighted_sum += rating * votes
            total_votes += votes

        if total_votes > 0:
            ratings[node] = weighted_sum / total_votes

    return ratings



"""Funciones para calcular frecuencias de valores en data, tanto para valores crudos como para bins."""
def raw_frequency(data: list[float]):
  value_frequency = []
  # sacar valores distintos y ordenarlos
  distinct_values = list(set(data))
  distinct_values.sort()
  # contar valores en data
  for value in distinct_values:
    value_frequency.append(data.count(value))
  return distinct_values, value_frequency

def bin_frequency(data: list[float], logaritmic_bins=False):
  if logaritmic_bins:
    x, y = powerlaw.pdf(data, linear_bins=False)
  else:
    x, y = powerlaw.pdf(data, linear_bins=True)
  x = x[0:-1] # se descarta el último porque es la posición donde iría el siguiente bin
  return x, y