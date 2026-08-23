"""
VideoGameRadar - página: Catálogo
Explorador de videojuegos con filtros.
"""

import streamlit as st
import pandas as pd
from consultas import get_connection


def pagina():
    st.title("Catálogo de Videojuegos")
    st.caption("Explora todos los juegos disponibles en la base de datos")
    
    conn = get_connection()
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        generos = conn.execute("""
            SELECT DISTINCT g.nombre 
            FROM generos g 
            JOIN juego_generos jg ON g.id = jg.genero_id
            ORDER BY g.nombre
        """).fetchall()
        genero_seleccionado = st.selectbox(
            "Filtrar por género",
            ["Todos"] + [g["nombre"] for g in generos]
        )
    
    with col_filtro2:
        plataformas = conn.execute("""
            SELECT DISTINCT p.nombre 
            FROM plataformas p 
            JOIN juego_plataformas jp ON p.id = jp.plataforma_id
            ORDER BY p.nombre
        """).fetchall()
        plataforma_seleccionada = st.selectbox(
            "Filtrar por plataforma",
            ["Todas"] + [p["nombre"] for p in plataformas]
        )
    
    with col_filtro3:
        ordenar_por = st.selectbox(
            "Ordenar por",
            ["Rating (Mayor a menor)", "Rating (Menor a mayor)", 
             "Más recientes", "Nombre (A-Z)"]
        )
    
    query = """
        SELECT 
            j.id, j.nombre, j.descripcion, j.fecha_lanzamiento,
            j.rating, j.metacritic, j.playtime, j.background_image,
            j.esrb_rating,
            GROUP_CONCAT(DISTINCT g.nombre) as generos,
            GROUP_CONCAT(DISTINCT p.nombre) as plataformas
        FROM juegos j
        LEFT JOIN juego_generos jg ON j.id = jg.juego_id
        LEFT JOIN generos g ON jg.genero_id = g.id
        LEFT JOIN juego_plataformas jp ON j.id = jp.juego_id
        LEFT JOIN plataformas p ON jp.plataforma_id = p.id
    """
    
    condiciones = []
    params = []
    
    if genero_seleccionado != "Todos":
        condiciones.append("g.nombre = ?")
        params.append(genero_seleccionado)
    
    if plataforma_seleccionada != "Todas":
        condiciones.append("p.nombre = ?")
        params.append(plataforma_seleccionada)
    
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)
    
    query += " GROUP BY j.id"
    
    if "Mayor" in ordenar_por:
        query += " ORDER BY j.rating DESC"
    elif "Menor" in ordenar_por:
        query += " ORDER BY j.rating ASC"
    elif "recientes" in ordenar_por:
        query += " ORDER BY j.fecha_lanzamiento DESC"
    else:
        query += " ORDER BY j.nombre ASC"
    
    query += " LIMIT 50"
    
    juegos = conn.execute(query, params).fetchall()
    conn.close()
    
    st.write(f"Mostrando {len(juegos)} juegos")
    
    if not juegos:
        st.warning("No se encontraron juegos con los filtros seleccionados.")
        return
    
    for juego in juegos:
        with st.container():
            col_img, col_info = st.columns([1, 3])
            
            with col_img:
                if juego["background_image"]:
                    st.image(juego["background_image"], width=200)
            
            with col_info:
                st.markdown(f"### {juego['nombre']}")
                
                cols_info = st.columns(4)
                with cols_info[0]:
                    st.markdown(f"**Rating:** {juego['rating'] or 'N/A'}/5")
                with cols_info[1]:
                    st.markdown(f"**Metacritic:** {juego['metacritic'] or 'N/A'}")
                with cols_info[2]:
                    st.markdown(f"**Lanzamiento:** {juego['fecha_lanzamiento'] or 'N/A'}")
                with cols_info[3]:
                    st.markdown(f"**Tiempo medio:** {juego['playtime'] or 0}h")
                
                st.markdown(f"**Géneros:** {juego['generos'] or 'N/A'}")
                st.markdown(f"**Plataformas:** {juego['plataformas'] or 'N/A'}")
                
                if juego['esrb_rating']:
                    st.markdown(f"**Clasificación:** {juego['esrb_rating']}")
                
                if juego['descripcion']:
                    desc = juego['descripcion'][:300]
                    if len(juego['descripcion']) > 300:
                        desc += "..."
                    st.markdown(desc)
            
            st.divider()
