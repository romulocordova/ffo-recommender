import pickle
import networkx as nx

print("Cargando relaciones FFO desde 'relaciones_ffo.pkl'...")
try:
    with open("relaciones_ffo.pkl", "rb") as f:
        relaciones = pickle.load(f)
except FileNotFoundError:
    print("❌ Error: No se encontró 'relaciones_ffo.pkl'.")
    print("Asegúrate de haber ejecutado 'scrape_posts.py' primero.")
    exit()

G = nx.Graph()

print("Construyendo el grafo con atributos...")
for relacion in relaciones:
    fuente = relacion['fuente']
    ffo = relacion['ffo']

    # Añadir/actualizar nodo fuente con sus atributos
    G.add_node(
        fuente['nombre'],
        country=fuente.get('pais_origen', 'Desconocido'),
        followers=fuente.get('followers', 0),
        popularity=fuente.get('popularity', 0)
    )

    # Añadir/actualizar nodo FFO con sus atributos
    G.add_node(
        ffo['nombre'],
        country=ffo.get('pais_origen', 'Desconocido'),
        followers=ffo.get('followers', 0),
        popularity=ffo.get('popularity', 0)
    )

    # Añadir o incrementar el peso de la arista
    if G.has_edge(fuente['nombre'], ffo['nombre']):
        G[fuente['nombre']][ffo['nombre']]['weight'] += 1
    else:
        G.add_edge(fuente['nombre'], ffo['nombre'], weight=1)

print(f"Grafo construido con {G.number_of_nodes()} bandas y {G.number_of_edges()} conexiones.")

with open("grafo_bandas.pkl", "wb") as f:
    pickle.dump(G, f)

print("✅ Grafo guardado en 'grafo_bandas.pkl'")