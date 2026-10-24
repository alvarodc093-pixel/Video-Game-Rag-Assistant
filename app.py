"""
VideoGameRadar - app.py
Punto de entrada de la app Streamlit con las pestañas:
- Visión general (KPIs y contexto)
- Catálogo de videojuegos
- Análisis por géneros
- Análisis por plataformas
- Búsqueda avanzada
- Chat RAG
"""

from pathlib import Path

import streamlit as st
from paginas import vision, catalogo, generos, plataformas, buscar, chat

RAIZ = Path(__file__).resolve().parent
HEADER = RAIZ / "assets" / "header.png"
LOGO = RAIZ / "assets" / "logo.png"

st.set_page_config(
    page_title="VideoGame Radar",
    page_icon=":material/sports_esports:",
    layout="wide",
)

if LOGO.exists():
    st.logo(str(LOGO))

paginas = {
    ":material/sports_esports: Visión general": vision.pagina,
    ":material/gamepad: Catálogo": catalogo.pagina,
    ":material/category: Géneros": generos.pagina,
    ":material/devices: Plataformas": plataformas.pagina,
    ":material/search: Búsqueda": buscar.pagina,
    ":material/chat: Chat RAG": chat.pagina,
}

with st.sidebar:
    st.caption("¿Qué juego estás buscando?")
    st.divider()
    seleccion = st.radio(
        "Sección",
        list(paginas.keys()),
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Datos: [RAWG](https://rawg.io) · Streamlit + Chroma")

if HEADER.exists():
    st.image(str(HEADER), width="stretch")

paginas[seleccion]()
