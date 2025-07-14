import praw
import pickle
import re
import pandas as pd
import requests
import base64
import unicodedata
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

popularity_cache = {}

def normaliza_banda(nombre):
    if not isinstance(nombre, str):
        return ""
    nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('utf-8')
    nombre = re.sub(r'[_\-–]+', ' ', nombre)
    nombre = re.sub(r"[\"'\(\)\[\]{}<>]", '', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    return nombre.title()

def extraer_bandas_con_llm(texto_post):
    prompt = f"""
    Rol: Eres un aficionado al metal, rock, y rock progresivo que además está haciendo una app para mapear relaciones entre bandas.
    Contexto: La idea de tu tarea es obtener la más precisa información del nombre de las bandas, para organizar la base de conocimientos de una app que hace relacioens entre ellas. Pero lo importante es que sigas la tarea a cabalidad
    Tarea:Analiza el siguiente texto de un post de Reddit. Identifica la banda principal que se está presentando y la lista de bandas en el contexto "FFO" (For Fans Of).
    Devuelve un objeto JSON con dos claves:
    1. "banda_fuente": Un objeto con el "nombre" y "pais_origen" de la banda principal del post.
    2. "bandas_ffo": Una lista de objetos, donde cada objeto tiene "nombre" y "pais_origen" de las bandas recomendadas.
    Si no puedes determinar el país, deja como "Desconocido" el campo "pais_origen", el campo "nombre" es el más importante, así que haz el mayor esfuerzo posible por agregarlo y no dejar la respuesta vacía.

    Texto a analizar:
    "{texto_post}"

    Salida JSON:
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en música que solo devuelve resultados en el formato JSON especificado."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        response_content = completion.choices[0].message.content
        return json.loads(response_content)
    except Exception as e:
        print(f"❌ Error al procesar con OpenAI: {e}")
        return None

def get_artist_data(artist_name):
    normalized_name = normaliza_banda(artist_name)
    if not normalized_name:
        return None
    
    time.sleep(0.1)
    
    try:
        client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
        auth_str = f"{client_id}:{client_secret}"
        b64_auth_str = base64.b64encode(auth_str.encode()).decode()
        token_url = 'https://accounts.spotify.com/api/token'
        headers = {'Authorization': f'Basic {b64_auth_str}', 'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'client_credentials'}
        response = requests.post(token_url, headers=headers, data=data, timeout=5)
        response.raise_for_status()
        access_token = response.json().get('access_token')

        search_url = 'https://api.spotify.com/v1/search'
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'q': normalized_name, 'type': 'artist', 'limit': 1}
        search_response = requests.get(search_url, headers=headers, params=params, timeout=5)
        search_response.raise_for_status()
        items = search_response.json().get('artists', {}).get('items', [])
        
        if not items:
            return {'popularity': None, 'followers': None}

        artist_data = items[0]
        popularity = artist_data.get('popularity')
        followers = artist_data.get('followers', {}).get('total')
        return {'popularity': popularity, 'followers': followers}

    except Exception as e:
        print(f"⚠️ Excepción al buscar {normalized_name} en Spotify: {e}")
        return {'popularity': None, 'followers': None}

def cache_artist_data(nombre):
    normalized_name = normaliza_banda(nombre)
    if normalized_name in popularity_cache:
        # print(f"🧠 Cache: {normalized_name} encontrado.")
        return popularity_cache[normalized_name]
    else:
        print(f"🔎 Consultando Spotify: {normalized_name}")
        data = get_artist_data(normalized_name)
        popularity_cache[normalized_name] = data
        return data

def tiene_ffo(texto):
    return bool(re.search(r'\b(f[\.\-/ ]?f[\.\-/ ]?o|f[\.\-/ ]?o[\.\-/ ]?f|for fans of|sounds like|if you like)\b', texto, re.IGNORECASE))

def scrape_posts_reddit(subreddits=["progmetal"], keywords=None, limit=2000, client_id="", client_secret="", user_agent="FFO Scraper"):
    print("🚀 Iniciando el scraper de Reddit...")
    if keywords is None:
        keywords = ["FFO", "For Fans Of", "Sounds Like", "If You Like"]

    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    posts = []
    
    print(f"📡 Conectando con Reddit para buscar en {len(subreddits)} subreddits.")
    for subreddit_name in subreddits:
        print(f"🔎 Buscando posts en r/{subreddit_name} (límite: {limit})...")
        subreddit = reddit.subreddit(subreddit_name)
        
        # --- LÓGICA CORREGIDA: Buscamos en 'top', 'new' y 'hot' ---
        sources = [
            subreddit.top(limit=limit),
            subreddit.new(limit=limit),
            subreddit.hot(limit=limit)
        ]
        
        for source in sources:
            for post in source:
                contenido = f"{post.title} {getattr(post, 'selftext', '')}".lower()
                if tiene_ffo(contenido):
                    posts.append({
                        "title": post.title, 
                        "selftext": getattr(post, 'selftext', '')
                    })
        # --- FIN DE LA CORRECCIÓN ---

    # Eliminamos duplicados por título (más eficientemente)
    titles_seen = set()
    unique_posts = [post for post in posts if post['title'] not in titles_seen and not titles_seen.add(post['title'])]
    print(f"\n🎯 Total de posts filtrados y únicos: {len(unique_posts)}")
    
    # El resto de la función (DataFrame, LLM, validación) sigue igual que en la versión anterior.
    df = pd.DataFrame(unique_posts)
    df['contenido_completo'] = df['title'] + " " + df['selftext']

    print("🤖 Usando OpenAI para extraer bandas y países...")
    df['datos_extraidos'] = df['contenido_completo'].apply(extraer_bandas_con_llm)
    df = df.dropna(subset=['datos_extraidos'])

    print("🔍 Validando bandas contra la API de Spotify para obtener seguidores y popularidad...")
    
    entradas_grafo = []
    for index, row in df.iterrows():
        datos = row['datos_extraidos']
        banda_fuente_info = datos.get('banda_fuente')
        bandas_ffo_info = datos.get('bandas_ffo', [])

        if not banda_fuente_info or not bandas_ffo_info:
            continue
        
        nombre_fuente = normaliza_banda(banda_fuente_info.get('nombre'))
        if not nombre_fuente: continue
        
        datos_fuente_spotify = cache_artist_data(nombre_fuente)
        if not datos_fuente_spotify or datos_fuente_spotify.get('popularity') is None:
            continue
        
        banda_fuente_info['followers'] = datos_fuente_spotify['followers']
        banda_fuente_info['popularity'] = datos_fuente_spotify['popularity']
        banda_fuente_info['nombre'] = nombre_fuente

        for banda_ffo in bandas_ffo_info:
            nombre_ffo = normaliza_banda(banda_ffo.get('nombre'))
            if not nombre_ffo: continue
            
            datos_ffo_spotify = cache_artist_data(nombre_ffo)
            if not datos_ffo_spotify or datos_ffo_spotify.get('popularity') is None:
                continue
            
            banda_ffo['followers'] = datos_ffo_spotify['followers']
            banda_ffo['popularity'] = datos_ffo_spotify['popularity']
            banda_ffo['nombre'] = nombre_ffo
            
            entradas_grafo.append({'fuente': banda_fuente_info, 'ffo': banda_ffo})

    print(f"✅ Se procesaron {len(entradas_grafo)} relaciones de FFO válidas.")
    
    with open("relaciones_ffo.pkl", "wb") as f:
        pickle.dump(entradas_grafo, f)
    print("💾 Relaciones FFO guardadas en 'relaciones_ffo.pkl'")

    with open("popularidad_cache.pkl", "wb") as f:
        pickle.dump(popularity_cache, f)
    print("💾 Cache de popularidad guardado correctamente.")