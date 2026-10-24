"""
VideoGameRadar - página: chat RAG
Chat que responde preguntas sobre videojuegos usando Chroma (recuperación)
+ un LLM local via Ollama (generación).

Sin Ollama, el chat sigue funcionando: responde solo con los datos
recuperados de Chroma (modo "datos").
"""

import os
import tomllib
from pathlib import Path

import streamlit as st

from consultas import get_connection

try:
    import chromadb
    from openai import OpenAI
except ImportError:  # demo web (stlite): sin Chroma ni cliente de LLM
    chromadb = None
    OpenAI = None

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
COLLECTION = "videojuegos"


def _config_ollama() -> dict:
    """Config de Ollama desde st.secrets o el secrets.toml del proyecto."""
    cfg = st.secrets.get("ollama") or {}
    if not cfg.get("base_url"):
        ruta = Path(__file__).resolve().parent.parent / "secrets.toml"
        try:
            with ruta.open("rb") as f:
                cfg = tomllib.load(f).get("ollama") or {}
        except (OSError, tomllib.TOMLDecodeError):
            cfg = {}
    return cfg


SUGERENCIAS = {
    ":blue[:material/gamepad:] ¿Qué juegos multijugador me recomiendas?": (
        "¿Qué juegos multijugador me recomiendas?"),
    ":green[:material/category:] ¿Cuáles son los mejores juegos de rol?": (
        "¿Cuáles son los mejores juegos de rol?"),
    ":orange[:material/whatshot:] Busca juegos de acción para PS5": (
        "Busca juegos de acción disponibles para PlayStation 5"),
    ":violet[:material/emoji_emotions:] Juegos casuales para jugar en familia": (
        "Recomiéndame juegos casuales para jugar en familia"),
    ":red[:material/visibility_off:] Juegos de terror populares": (
        "¿Cuáles son los juegos de terror más populares?"),
    ":gray[:material/schedule:] Juegos cortos para completar en un fin de semana": (
        "¿Qué juegos puedo completar en un fin de semana?"),
}


@st.cache_resource
def obtener_coleccion():
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_collection(COLLECTION)


@st.cache_resource
def obtener_cliente_llm():
    if OpenAI is None:
        return None, ""
    cfg = _config_ollama()
    base_url = cfg.get("base_url")
    model = cfg.get("model")
    if not base_url or not model:
        return None, ""
    try:
        cliente = OpenAI(base_url=base_url, api_key="ollama")
        return cliente, model
    except Exception:
        return None, ""


# Palabras de la pregunta (en español) -> género o tag de RAWG, para el modo sin Chroma.
TERMINOS = {
    "multijugador": "Multiplayer", "cooperativ": "Co-op", "acción": "Action",
    "accion": "Action", "rol": "RPG", "terror": "Horror", "casual": "Casual",
    "familia": "Family", "estrategia": "Strategy", "aventura": "Adventure",
    "shooter": "Shooter", "deporte": "Sports", "carreras": "Racing",
    "puzle": "Puzzle", "plataformas": "Platformer", "indie": "Indie",
    "mundo abierto": "Open World", "playstation 5": "PlayStation 5",
    "ps5": "PlayStation 5", "xbox": "Xbox", "switch": "Nintendo Switch", "pc": "PC",
}


def recuperar_sql(pregunta: str, k: int) -> list[dict]:
    """Sin Chroma: filtra por los géneros, tags y plataformas que nombra la pregunta."""
    p = pregunta.lower()
    terminos = [v for clave, v in TERMINOS.items() if clave in p]
    corto = any(x in p for x in ("fin de semana", "corto", "cortos", "poco tiempo"))
    condiciones, params = [], []
    for t in terminos:
        condiciones.append("""(EXISTS (SELECT 1 FROM juego_generos jg JOIN generos g ON g.id = jg.genero_id
                                       WHERE jg.juego_id = j.id AND g.nombre LIKE ?)
                             OR EXISTS (SELECT 1 FROM juego_tags jt JOIN tags t ON t.id = jt.tag_id
                                       WHERE jt.juego_id = j.id AND t.nombre LIKE ?)
                             OR EXISTS (SELECT 1 FROM juego_plataformas jp JOIN plataformas pl ON pl.id = jp.plataforma_id
                                       WHERE jp.juego_id = j.id AND pl.nombre LIKE ?))""")
        params += [f"%{t}%"] * 3
    if corto:
        condiciones.append("j.playtime BETWEEN 1 AND 10")
    where = " AND ".join(condiciones) or "1=1"
    conn = get_connection()
    filas = conn.execute(f"""
        SELECT j.nombre, j.rating, j.metacritic, j.playtime, j.fecha_lanzamiento,
               (SELECT GROUP_CONCAT(g.nombre, ', ') FROM juego_generos jg JOIN generos g ON g.id = jg.genero_id
                WHERE jg.juego_id = j.id) AS generos,
               (SELECT GROUP_CONCAT(pl.nombre, ', ') FROM juego_plataformas jp JOIN plataformas pl ON pl.id = jp.plataforma_id
                WHERE jp.juego_id = j.id) AS plataformas
        FROM juegos j WHERE {where}
        ORDER BY j.rating DESC LIMIT ?""", params + [k]).fetchall()
    conn.close()
    resultados = []
    for f in filas:
        doc = (f"JUEGO: {f['nombre']}\nGÉNEROS: {f['generos']}\nPLATAFORMAS: {f['plataformas']}\n"
               f"TIEMPO PROMEDIO: {f['playtime']} horas")
        resultados.append({"documento": doc, "metadatos": {
            "nombre": f["nombre"], "generos": f["generos"], "plataformas": f["plataformas"],
            "rating": f["rating"], "metacritic": f["metacritic"],
            "fecha_lanzamiento": f["fecha_lanzamiento"]}})
    return resultados


def recuperar(coleccion, pregunta: str, k: int) -> list[dict]:
    """Busca los k juegos más relevantes en Chroma (o con SQL si no hay Chroma)."""
    if coleccion is None:
        return recuperar_sql(pregunta, k)
    try:
        resultados = coleccion.query(
            query_texts=[pregunta], n_results=k, include=["documents", "metadatas"]
        )
    except Exception:
        return []
    docs = (resultados.get("documents") or [[]])[0]
    metas = (resultados.get("metadatas") or [[]])[0]
    return [{"documento": d, "metadatos": m}
            for d, m in zip(docs, metas) if d]


def formato_contexto(resultados: list[dict]) -> str:
    """Formatea los resultados recuperados como contexto para el LLM."""
    lineas = []
    for i, r in enumerate(resultados, 1):
        m = r["metadatos"] or {}
        nombre = m.get("nombre", "?")
        generos = m.get("generos", "N/A")
        plataformas = m.get("plataformas", "N/A")
        rating = m.get("rating", "N/A")
        metacritic = m.get("metacritic", "N/A")
        fecha = m.get("fecha_lanzamiento", "N/A")

        lineas.append(
            f"[{i}] {nombre}\n"
            f"    Géneros: {generos}\n"
            f"    Plataformas: {plataformas}\n"
            f"    Rating: {rating}/5 | Metacritic: {metacritic}\n"
            f"    Fecha: {fecha}\n"
            f"    {r['documento'][:500]}\n"
        )
    return "\n".join(lineas)


def generar_respuesta(pregunta: str, contexto: str,
                      historial: list[dict]) -> str:
    """Genera una respuesta usando el LLM con el contexto recuperado."""
    cliente, model = obtener_cliente_llm()
    if not cliente:
        return (
            "Sin un LLM conectado no redacto la respuesta, pero estos son los "
            f"juegos que mejor encajan con tu pregunta:\n\n{contexto[:2000]}"
        )

    system = (
        "Eres VideoGame Radar, un asistente experto en videojuegos que responde "
        "preguntas sobre juegos, géneros, plataformas y recomendaciones. "
        "Responde usando SOLO la información de los juegos recuperados (contexto). "
        "Si no hay datos suficientes, dilo. "
        "Sé concreto, menciona nombres de juegos específicos cuando puedas. "
        "Responde en el idioma de la pregunta.\n\n"
        "Juegos recuperados:\n"
        f"{contexto}"
    )
    mensajes = [{"role": "system", "content": system}]
    for m in historial[-6:]:
        mensajes.append({"role": m["role"], "content": m["content"]})
    mensajes.append({"role": "user", "content": pregunta})

    respuesta = cliente.chat.completions.create(
        model=model,
        messages=mensajes,
        stream=True,
        temperature=0.2,
    )
    return respuesta


def pagina():
    st.title("Chat con tu asistente gamer")

    st.caption(
        "Pregunta sobre videojuegos, géneros, plataformas o pide recomendaciones. "
        "El chat recupera los juegos más relevantes de Chroma y los usa como contexto. "
        "Conecta Ollama para respuestas generadas por IA; sin él, responde "
        "con los datos recuperados directamente."
    )

    with st.sidebar:
        k = st.slider("Nº de juegos recuperados (k)", 1, 15, 5)
        if st.button("Borrar conversación"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    coleccion = None
    if chromadb is None:
        st.info("Versión web: el chat busca con SQL por género, etiqueta y plataforma "
                "(sin búsqueda semántica ni LLM).")
    else:
        try:
            coleccion = obtener_coleccion()
        except Exception:
            st.info("No hay colección Chroma (`python preparar_corpus.py`); "
                    "el chat busca con SQL por género, etiqueta y plataforma.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    sugerencia = None
    if not st.session_state.messages:
        seleccion = st.pills(
            "Prueba a preguntar:",
            list(SUGERENCIAS.keys()),
            label_visibility="collapsed",
        )
        if seleccion:
            sugerencia = SUGERENCIAS[seleccion]

    # Una sugerencia pulsada sigue el mismo camino que una pregunta escrita.
    prompt = st.chat_input(
        "Pregunta sobre videojuegos...", submit_mode="disable") or sugerencia

    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            resultados = recuperar(coleccion, prompt, k)
            if not resultados:
                respuesta = ("No he encontrado juegos relacionados. Prueba a "
                             "preguntar sobre géneros, plataformas o títulos específicos.")
            else:
                respuesta = generar_respuesta(
                    prompt, formato_contexto(resultados), st.session_state.messages[:-1])
            if isinstance(respuesta, str):
                st.write(respuesta)
            else:
                respuesta = st.write_stream(respuesta)
            st.session_state.messages.append(
                {"role": "assistant", "content": respuesta})

        st.rerun()
