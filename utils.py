import networkx as nx
import pandas as pd
import ast
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt
import powerlaw
import numpy as np
from collections import defaultdict
from scipy.interpolate import UnivariateSpline

@nx._dispatchable(
    graphs="B", preserve_node_attrs=True, preserve_graph_attrs=True, returns_graph=True
)
def projected_graph_custom(B, nodes, multigraph=False):
    """
    Genera la proyección de B a uno de sus sets de nodos. Los nodos
    eliminados mantienen sus atributos en forma de arista.
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
                    episodes = set()
                    edge_data = G.get_edge_data(u, n)
                    for edge_key, attrs in edge_data.items():
                        pages += attrs["n de paginas"]
                        votes += attrs["votos"]
                        rating += attrs["votos"]*attrs["rating"]
                        episodes.add(edge_key)
                    d_attr = {"n de paginas": pages, "rating": rating/votes, "votos": votes, "n_episodios": len(episodes)}
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


def plot_distribution(values, title):

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # Sin bins
    x, y = raw_frequency(values)
    axes[0,0].scatter(x, y)
    axes[0,0].set_title("Sin bins")

    # Bins lineales
    x, y = bin_frequency(values)
    axes[0,1].scatter(x, y)
    axes[0,1].set_title("Bins lineales")

    # Bins log
    x, y = bin_frequency(values, logaritmic_bins=True)
    axes[0,2].scatter(x, y)
    axes[0,2].set_title("Bins log")

    # Sin bins + loglog
    x, y = raw_frequency(values)
    axes[1,0].scatter(x, y)
    axes[1,0].loglog()
    axes[1,0].set_title("Sin bins (log-log)")

    # Bins lineales + loglog
    x, y = bin_frequency(values)
    axes[1,1].scatter(x, y)
    axes[1,1].loglog()
    axes[1,1].set_title("Bins lineales (log-log)")

    # Bins log + loglog
    x, y = bin_frequency(values, logaritmic_bins=True)
    axes[1,2].scatter(x, y)
    axes[1,2].loglog()
    axes[1,2].set_title("Bins log (log-log)")

    fig.suptitle(title)
    plt.show()

def plot_rating_vs_metric(
    G,
    metric,
    metric_name="Metric",
    rating_attr="rating",
    bipartite_value="episode"
):
    """
    G            : grafo NetworkX
    metric       : dict {nodo: valor} o vista tipo G.degree()
    metric_name  : nombre para títulos y ejes
    """

    ratings = []
    metric_values = []

    for node, data in G.nodes(data=True):

        if data.get("bipartite") == bipartite_value:

            rating = data.get(rating_attr)

            if pd.notna(rating):

                ratings.append(rating)
                metric_values.append(metric[node])

    # Promedio de la métrica por intervalos de rating de tamaño 0.5
    df_aux = pd.DataFrame({
        "rating": ratings,
        "metric": metric_values
    })

    bins = np.arange(
        np.floor(min(ratings) * 2) / 2,
        np.ceil(max(ratings) * 2) / 2 + 0.5,
        0.5
    )

    df_aux["rating_bin"] = pd.cut(df_aux["rating"], bins=bins)

    print(f"\nPromedio de {metric_name} por intervalos de rating de 0.5:")
    print(
        df_aux.groupby("rating_bin", observed=False)["metric"]
        .mean()
        .round(4)
    )

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    configs = [
        ("Linear-Linear", False, False),
        ("Log X", True, False),
        ("Log Y", False, True),
        ("Log X + Log Y", True, True)
    ]

    for ax, (title, logx, logy) in zip(axes.flatten(), configs):

        ax.scatter(ratings, metric_values)

        if logx:
            ax.set_xscale("log")

        if logy:
            ax.set_yscale("log")

        ax.set_title(title)
        ax.set_xlabel("Rating")
        ax.set_ylabel(metric_name)
        ax.grid(True)

    plt.suptitle(f"Rating vs {metric_name}", fontsize=14)
    plt.tight_layout()
    plt.show()

def plot_metric_vs_metric(
    metric1,
    metric2,
    metric1_name="Metric1",
    metric2_name="Metric2",
    vertical_lines=None
):
    """
    metric1, metric2 : listas o arrays de valores
    metric1_name     : nombre eje X
    metric2_name     : nombre eje Y
    vertical_lines   : lista de valores x donde dibujar líneas verticales
    """

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    configs = [
        ("Linear-Linear", False, False),
        ("Log X", True, False),
        ("Log Y", False, True),
        ("Log X + Log Y", True, True)
    ]

    for ax, (title, logx, logy) in zip(axes.flatten(), configs):

        ax.scatter(metric1, metric2)

        if vertical_lines is not None:
            for v in vertical_lines:
                ax.axvline(
                    x=v,
                    linestyle="--",
                    linewidth=1,
                    alpha=0.8,
                    color="red"
                )

        if logx:
            ax.set_xscale("log")

        if logy:
            ax.set_yscale("log")

        ax.set_title(title)
        ax.set_xlabel(metric1_name)
        ax.set_ylabel(metric2_name)
        ax.grid(True)

    plt.suptitle(f"{metric1_name} vs {metric2_name}", fontsize=14)
    plt.tight_layout()
    plt.show()

def get_members_combination(nodes):
    largo = len(nodes)
    nodes_2 = []
    for i in range(largo):
        if i == (largo - 1):
            break
        for l in range(i + 1, largo):
            if l == largo:
                break
            nodes_2.append((nodes[i], nodes[l]))
    return nodes_2

def avg_previous_team_rating(B, nodes, largo):
    if largo == 0:
        return 0
    suma = 0
    updated_nodes = []
    for u in nodes:
        if B.has_node(u):
            updated_nodes.append(u)
    for u in updated_nodes:
        suma_temp = 0
        for ep in B[u]:
            suma_temp += B.nodes[ep]["rating"]
        suma += (suma_temp/len(B[u]))
    
    return (suma/largo)

def avg_previous_individual_exp(B, nodes, largo):
    if largo == 0:
        return 0
    suma = 0
    updated_nodes = []
    for u in nodes:
        if B.has_node(u):
            updated_nodes.append(u)
    for u in updated_nodes:
        suma += len(B[u])
    
    return (suma/largo)

def avg_previous_tm_exp(G, nodes_2, largo):
    """ Calcula la experiencia promedio previa de un set de nodos."""
    if largo == 0:
        return 0
    suma = 0
    for u, v in nodes_2:
        if not G.has_node(u) or not G.has_node(v):
            continue
        if G.has_edge(u, v):
            node_attrs = G.get_edge_data(u, v)
            suma += node_attrs["n_episodios"]
    
    return (suma/largo)

def avg_previous_tm_shared_colabs(G, nodes_2, largo):
    if largo == 0:
        return 0
    suma = 0
    for u, v in nodes_2:
        if not G.has_node(u) or not G.has_node(v):
            continue
        suma += len(nx.common_neighbors(G, u, v))
    
    return (suma/largo)

def avg_previous_tm_clustering_coeff(G, nodes, largo):
    if largo == 0:
        return 0
    suma = 0
    updated_nodes = []
    for u in nodes:
        if G.has_node(u):
            updated_nodes.append(u)
    clustering = nx.clustering(G, nodes)
    for u in updated_nodes:
        suma += clustering[u]
    
    return (suma/largo)

def avg_previous_tm_closeness(G, nodes, largo):
    if largo == 0:
        return 0
    suma = 0
    for u in nodes:
        if G.has_node(u):
            suma += nx.closeness_centrality(G, u)
    
    return (suma/largo)

def avg_previous_tm_betweenness(G, nodes, prev_betweenness, largo):
    if largo == 0:
        return 0
    suma = 0
    updated_nodes = []
    for u in nodes:
        if G.has_node(u):
            updated_nodes.append(u)
    for u in updated_nodes:
        suma += prev_betweenness[u]
    
    return (suma/largo)

def train_generator(
    csv_path,
    target_column,
    smoothing_factor=0.8,
):
    """
    Entrena un generador sintético para una variable numérica en función
    del número de episodio.
    """

    df = pd.read_csv(csv_path)

    df = (
        df[["episodio", target_column]]
        .dropna()
        .sort_values("episodio")
    )

    if not np.issubdtype(df[target_column].dtype, np.number):
        raise TypeError(
            f"La columna '{target_column}' debe contener únicamente valores numéricos."
        )

    x = df["episodio"].to_numpy()
    y = df[target_column].to_numpy()

    spline = UnivariateSpline(
        x,
        y,
        s=len(x) * smoothing_factor
    )

    residuos = y - spline(x)

    return {
        "x": x,
        "y": y,
        "target_column": target_column,
        "spline": spline,
        "residuos": residuos
    }


def generate_synthetic(
    model,
    episodes=None,
    window=None,
    clip=None,
    decimals=2,
    seed=None,
):
    """
    Genera valores sintéticos para una variable en función del episodio.
    """

    rng = np.random.default_rng(seed)

    x_train = model["x"]
    spline = model["spline"]
    residuos = model["residuos"]

    if episodes is None:
        episodes = x_train

    episodes = np.asarray(episodes)

    synthetic = {}

    for episode in episodes:

        # Tendencia estimada por el spline
        trend = float(spline(episode))

        if window is None:
            # Utilizar todos los residuos del dataset
            local_residuals = residuos

        else:
            # Episodio real más cercano
            idx = np.argmin(np.abs(x_train - episode))

            # Ventana local
            start = max(0, idx - window)
            end = min(len(residuos), idx + window + 1)

            local_residuals = residuos[start:end]

        # Muestrear un residuo observado
        noise = rng.choice(local_residuals)

        synthetic_value = trend + noise

        if clip is not None:

            minimum = -np.inf if clip[0] is None else clip[0]
            maximum = np.inf if clip[1] is None else clip[1]

            synthetic_value = np.clip(
                synthetic_value,
                minimum,
                maximum
            )

        synthetic[int(episode)] = round(
            float(synthetic_value),
            decimals
        )

    return synthetic