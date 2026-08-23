"""
VideoGameRadar - página: Plataformas
Análisis de videojuegos por plataformas.
"""

import streamlit as st
import pandas as pd
from consultas import get_connection, plataformas_principales


def pagina():
    st.title("Análisis por Plataformas")
    st.caption("Compara juegos disponibles en cada plataforma")
    
    conn = get_connection()
    
    plataformas = plataformas_principales(20)
    
    if not plataformas:
        st.warning("No hay datos de plataformas disponibles.")
        return
    
    df_plataformas = pd.DataFrame(plataformas)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Juegos por plataforma")
        st.bar_chart(df_plataformas.set_index("nombre")["total"])
    
    with col2:
        st.subheader("Estadísticas por plataforma")
        
        st.dataframe(
            df_plataformas.rename(columns={"nombre": "Plataforma", "total": "Total Juegos"}),
            use_container_width=True,
            hide_index=True
        )
    
    st.divider()
    
    st.subheader("Comparativa de plataformas")
    
    plataformasSeleccionadas = st.multiselect(
        "Selecciona plataformas para comparar",
        [p["nombre"] for p in plataformas],
        default=[p["nombre"] for p in plataformas[:3]]
    )
    
    if plataformasSeleccionadas:
        query = """
            SELECT 
                p.nombre as plataforma,
                COUNT(DISTINCT j.id) as total_juegos,
                ROUND(AVG(j.rating), 2) as rating_promedio,
                ROUND(AVG(j.metacritic), 0) as metacritic_promedio
            FROM plataformas p
            JOIN juego_plataformas jp ON p.id = jp.plataforma_id
            JOIN juegos j ON jp.juego_id = j.id
            WHERE p.nombre IN ({})
            GROUP BY p.id
        """.format(",".join("?" * len(plataformasSeleccionadas)))
        
        stats = conn.execute(query, plataformasSeleccionadas).fetchall()
        
        if stats:
            df_stats = pd.DataFrame([dict(row) for row in stats])
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("#### Total de juegos")
                st.bar_chart(df_stats.set_index("plataforma")["total_juegos"])
            
            with col_b:
                st.markdown("#### Rating promedio")
                st.bar_chart(df_stats.set_index("plataforma")["rating_promedio"])
    
    st.divider()
    
    st.subheader("Explorar por plataforma")
    
    plataforma_seleccionada = st.selectbox(
        "Selecciona una plataforma",
        [p["nombre"] for p in plataformas]
    )
    
    if plataforma_seleccionada:
        query = """
            SELECT j.nombre, j.rating, j.metacritic, j.fecha_lanzamiento,
                   j.background_image,
                   GROUP_CONCAT(DISTINCT g.nombre) as generos
            FROM juegos j
            JOIN juego_plataformas jp ON j.id = jp.juego_id
            JOIN plataformas p ON jp.plataforma_id = p.id
            LEFT JOIN juego_generos jg ON j.id = jg.juego_id
            LEFT JOIN generos g ON jg.genero_id = g.id
            WHERE p.nombre = ?
            GROUP BY j.id
            ORDER BY j.rating DESC
            LIMIT 20
        """
        
        juegos = conn.execute(query, (plataforma_seleccionada,)).fetchall()
        
        st.write(f"Top 20 juegos en **{plataforma_seleccionada}**:")
        
        for juego in juegos:
            col_img, col_info = st.columns([1, 3])
            
            with col_img:
                if juego["background_image"]:
                    st.image(juego["background_image"], width=150)
            
            with col_info:
                st.markdown(f"**{juego['nombre']}**")
                st.markdown(f"Rating: {juego['rating'] or 'N/A'}/5 | Metacritic: {juego['metacritic'] or 'N/A'}")
                st.markdown(f"Géneros: {juego['generos'] or 'N/A'}")
                st.markdown(f"Fecha: {juego['fecha_lanzamiento'] or 'N/A'}")
    
    conn.close()
