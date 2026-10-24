"""
VideoGameRadar - página: Visión general
Dashboard principal con KPIs y contexto del catálogo.
"""

import streamlit as st
import pandas as pd
from consultas import (
    estadisticas_generales, generos_principales,
    plataformas_principales, juegos_top
)


def pagina():
    st.title("VideoGame Radar")
    st.subheader("Tu guía para descubrir videojuegos")

    stats = estadisticas_generales()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Juegos", f"{stats['total_juegos']:,}")
    with col2:
        st.metric("Géneros", stats['total_generos'])
    with col3:
        st.metric("Plataformas", stats['total_plataformas'])
    with col4:
        rating = stats.get('rating_promedio', 0) or 0
        st.metric("Rating Promedio", f"{rating:.1f}/5")

    st.divider()

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("Géneros principales")
        generos = generos_principales(8)
        if generos:
            df_gen = pd.DataFrame(generos)
            st.bar_chart(df_gen.set_index("nombre")["total"])

    with col_der:
        st.subheader("Plataformas principales")
        plataformas = plataformas_principales(8)
        if plataformas:
            df_plat = pd.DataFrame(plataformas)
            st.bar_chart(df_plat.set_index("nombre")["total"])

    st.divider()

    st.subheader("Top 10 juegos mejor valorados")
    top_juegos = juegos_top(10)
    if top_juegos:
        for i, juego in enumerate(top_juegos, 1):
            col_num, col_info = st.columns([1, 4])
            with col_num:
                st.markdown(f"### {i}")
            with col_info:
                st.markdown(f"**{juego['nombre']}**")
                generos_texto = juego.get('generos', 'N/A')
                rating = juego.get('rating', 'N/A')
                metacritic = juego.get('metacritic', 'N/A')
                st.caption(f"Géneros: {generos_texto} | Rating: {rating}/5 | Metacritic: {metacritic}")
