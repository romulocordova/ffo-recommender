import streamlit as st
import pickle
import networkx as nx
import pandas as pd

st.set_page_config(layout="wide")
st.title("🎸 FFO Recommender")

# Load the graph with band data
try:
    with open("grafo_bandas.pkl", "rb") as f:
        G = pickle.load(f)
    bandas_disponibles = sorted(list(G.nodes()))
except FileNotFoundError:
    st.error("Graph file ('grafo_bandas.pkl') not found. Please run the scraper and graph builder scripts first.")
    st.stop()

# --- SIDEBAR FOR FILTERS ---
st.sidebar.header("Search Filters")

banda_seleccionada = st.sidebar.selectbox(
    "Select a band to see its connections:",
    bandas_disponibles,
    index=None, # No default selection
    placeholder="Choose a source band"
)

# Filters for the recommendations
st.sidebar.subheader("Filter the recommended bands:")
max_followers = st.sidebar.number_input(
    "Maximum followers:",
    min_value=0,
    value=100000
)

max_popularity = st.sidebar.slider(
    "Maximum popularity (0-100):",
    min_value=0,
    max_value=100,
    value=70
)

min_connections = st.sidebar.slider(
    "Minimum shared connections:",
    min_value=1,
    max_value=20,
    value=1
)

# Get all available countries from the graph
paises_disponibles = sorted(list(set(d['country'] for n, d in G.nodes(data=True) if 'country' in d and d['country'] != 'Desconocido')))
paises_seleccionados = st.sidebar.multiselect(
    "Filter by country (leave blank for all):",
    paises_disponibles
)

# --- RECOMMENDATION AND DISPLAY LOGIC ---
if banda_seleccionada:
    neighbors = list(G.neighbors(banda_seleccionada))
    
    recomendaciones = []
    for neighbor in neighbors:
        # Get neighbor data from the graph
        datos_vecino = G.nodes[neighbor]
        conexiones = G[banda_seleccionada][neighbor]['weight']
        
        # Apply filters
        if datos_vecino.get('followers', 0) > max_followers:
            continue
        if datos_vecino.get('popularity', 0) > max_popularity:
            continue
        if conexiones < min_connections:
            continue
        if paises_seleccionados and datos_vecino.get('country') not in paises_seleccionados:
            continue
            
        recomendaciones.append({
            "Band": neighbor,
            "Connections": conexiones,
            "Popularity": datos_vecino.get('popularity', 'N/A'),
            "Followers": datos_vecino.get('followers', 'N/A'),
            "Country": datos_vecino.get('country', 'N/A')
        })

    st.header(f"Bands connected to '{banda_seleccionada}'")
    
    if recomendaciones:
        df_recomendaciones = pd.DataFrame(recomendaciones)
        
        # Sorting options
        sort_by = st.selectbox(
            "Sort by:",
            ["Connections", "Popularity", "Followers"]
        )
        
        # Sort logic
        ascending_logic = True if sort_by == "Popularity" else False
        
        df_recomendaciones = df_recomendaciones.sort_values(
            by=sort_by,
            ascending=ascending_logic
        )
        
        st.dataframe(df_recomendaciones, use_container_width=True, hide_index=True)
    else:
        st.warning("No recommendations found with the current filters.")
else:
    st.info("Select a band from the sidebar to get started.")