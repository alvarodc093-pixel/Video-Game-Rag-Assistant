"""
VideoGameRadar - página: Géneros
Análisis de videojuegos por géneros.
"""

import streamlit as st
import pandas as pd
from consultas import get_connection, generos_principales


def pagina():
    st.title("Análisis por Géneros")
    st.caption("Descubre las tendencias en géneros de videojuegos")
    
    conn = get_connection()
    
    generos = generos_principales(20)
    
    if not generos:
        st.warning("No hay datos de géneros disponibles.")
        return
    
    df_generos = pd.DataFrame(generos)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución de juegos por género")
        st.bar_chart(df_generos.set_index("nombre")["total"])
    
    with col2:
        st.subheader("Estadísticas por género")
        
        st.dataframe(
            df_generos.rename(columns={"nombre": "Género", "total": "Total Juegos"}),
            use_container_width=True,
            hide_index=True
        )
    
    st.divider()
    
    st.subheader("Explorar por género")
    
    genero_seleccionado = st.selectbox(
        "Selecciona un género para ver sus juegos",
        [g["nombre"] for g in generos]
    )
    
    if genero_seleccionado:
        query = """
            SELECT j.nombre, j.rating, j.metacritic, j.fecha_lanzamiento,
                   j.background_image, j.descripcion
            FROM juegos j
            JOIN juego_generos jg ON j.id = jg.juego_id
            JOIN generos g ON jg.genero_id = g.id
            WHERE g.nombre = ?
            ORDER BY j.rating DESC
            LIMIT 20
        """
        
        juegos = conn.execute(query, (genero_seleccionado,)).fetchall()
        
        st.write(f"Top 20 juegos de **{genero_seleccionado}**:")
        
        for juego in juegos:
            col_img, col_info = st.columns([1, 3])
            
            with col_img:
                if juego["background_image"]:
                    st.image(juego["background_image"], width=150)
            
            with col_info:
                st.markdown(f"**{juego['nombre']}**")
                st.markdown(f"Rating: {juego['rating'] or 'N/A'}/5 | Metacritic: {juego['metacritic'] or 'N/A'}")
                st.markdown(f"Fecha: {juego['fecha_lanzamiento'] or 'N/A'}")
    
    conn.close()
