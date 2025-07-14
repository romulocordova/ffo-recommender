# export_for_gephi.py

import pickle
import networkx as nx

print("Cargando el grafo desde 'grafo_bandas.pkl'...")
try:
    with open("grafo_bandas.pkl", "rb") as f:
        G = pickle.load(f)
except FileNotFoundError:
    print("❌ Error: No se encontró 'grafo_bandas.pkl'.")
    print("Asegúrate de haber ejecutado 'scrape_posts.py' y 'grafo_bandas.py' primero.")
    exit()

# El formato GEXF es ideal para Gephi porque guarda todos los atributos
# de los nodos (país, followers, etc.) y las aristas (weight).
output_filename = "grafo_para_gephi.gexf"
nx.write_gexf(G, output_filename)

print(f"✅ Grafo exportado exitosamente a '{output_filename}'")
print("Ahora puedes abrir este archivo con Gephi.")