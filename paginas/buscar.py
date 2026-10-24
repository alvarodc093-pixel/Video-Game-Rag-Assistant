"""
VideoGameRadar - página: Búsqueda
Búsqueda avanzada de videojuegos con filtros inteligentes.
"""

import streamlit as st
from consultas import get_connection, buscar_juego


# Los géneros y tags de RAWG están en inglés: las sugerencias buscan el término original.
SUGERENCIAS_BUSQUEDA = {
    ":blue[:material/gamepad:] Juegos multijugador": "Multiplayer",
    ":green[:material/people:] Juegos cooperativos": "Co-op",
    ":orange[:material/whatshot:] Juegos de acción": "Action",
    ":violet[:material/psychology:] Juegos de rol": "RPG",
    ":red[:material/visibility_off:] Juegos de terror": "Horror",
    ":gray[:material/emoji_emotions:] Juegos casuales": "Casual",
}


def pagina():
    st.title("Búsqueda Avanzada")
    st.caption("Encuentra el juego perfecto para ti")

    col_sugerencias, col_busqueda = st.columns([1, 2])

    with col_sugerencias:
        st.markdown("### Búsquedas populares")
        seleccion = st.pills(
            "Selecciona una categoría",
            list(SUGERENCIAS_BUSQUEDA.keys()),
            label_visibility="collapsed",
        )
        if seleccion:
            termino = SUGERENCIAS_BUSQUEDA[seleccion]
            st.session_state["busqueda"] = termino

    with col_busqueda:
        st.markdown("### Búsqueda personalizada")
        busqueda = st.text_input(
            "Busca por nombre, género o palabra clave",
            value=st.session_state.get("busqueda", ""),
            placeholder="Ej: zelda, multiplayer, shooter, playstation..."
        )

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        rating_minimo = st.slider("Rating mínimo", 0.0, 5.0, 0.0, 0.5)

    with col_f2:
        metacritic_minimo = st.slider("Metacritic mínimo", 0, 100, 0, 10)

    with col_f3:
        tiene_imagen = st.checkbox("Solo con imagen")

    st.divider()

    if busqueda:
        st.session_state["busqueda"] = busqueda

        conn = get_connection()

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
            WHERE (
                j.nombre LIKE ?
                OR j.descripcion LIKE ?
                OR g.nombre LIKE ?
                OR p.nombre LIKE ?
                OR EXISTS (
                    SELECT 1 FROM juego_tags jt
                    JOIN tags t ON jt.tag_id = t.id
                    WHERE jt.juego_id = j.id AND t.nombre LIKE ?
                )
            )
        """

        params = [f"%{busqueda}%"] * 5

        if rating_minimo > 0:
            query += " AND j.rating >= ?"
            params.append(rating_minimo)

        if metacritic_minimo > 0:
            query += " AND j.metacritic >= ?"
            params.append(metacritic_minimo)

        if tiene_imagen:
            query += " AND j.background_image IS NOT NULL"

        query += " GROUP BY j.id ORDER BY j.rating DESC LIMIT 30"

        juegos = conn.execute(query, params).fetchall()
        conn.close()

        st.write(f"### Resultados para «{busqueda}» ({len(juegos)} juegos encontrados)")

        if not juegos:
            st.info("No se encontraron juegos. Prueba con otros términos.")
            return

        for juego in juegos:
            col_img, col_info = st.columns([1, 3])

            with col_img:
                if juego["background_image"]:
                    st.image(juego["background_image"], width=200)
                else:
                    st.markdown("*Sin imagen*")

            with col_info:
                st.markdown(f"### {juego['nombre']}")

                cols_datos = st.columns(4)
                with cols_datos[0]:
                    st.markdown(f"**Rating:** {juego['rating'] or 'N/A'}/5")
                with cols_datos[1]:
                    st.markdown(f"**Metacritic:** {juego['metacritic'] or 'N/A'}")
                with cols_datos[2]:
                    st.markdown(f"**Lanzamiento:** {juego['fecha_lanzamiento'] or 'N/A'}")
                with cols_datos[3]:
                    st.markdown(f"**Tiempo medio:** {juego['playtime'] or 0}h")

                st.markdown(f"**Géneros:** {juego['generos'] or 'N/A'}")
                st.markdown(f"**Plataformas:** {juego['plataformas'] or 'N/A'}")

                if juego['descripcion']:
                    desc = juego['descripcion'][:400]
                    if len(juego['descripcion']) > 400:
                        desc += "..."
                    st.markdown(desc)

            st.divider()
    else:
        st.info("Escribe un término de búsqueda o selecciona una categoría popular.")

        st.markdown("""
        ### Consejos de búsqueda

        Los géneros y etiquetas vienen de RAWG y están en inglés:

        - **Por nombre**: "zelda", "portal", "witcher"
        - **Por género**: "action", "adventure", "rpg", "strategy"
        - **Por etiqueta**: "multiplayer", "co-op", "open world"
        - **Por plataforma**: "playstation", "xbox", "nintendo", "pc"
        """)
