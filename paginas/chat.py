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

import chromadb
import streamlit as st
from openai import OpenAI

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
    ":purple[:material/emoji_emotions:] Juegos casuales para jugar en familia": (
        "Recomiéndame juegos casuales para jugar en familia"),
    ":red[:material/visibility_off:] Juegos de terror populares": (
        "¿Cuáles son los juegos de terror más populares?"),
    ":cyan[:material/schedule:] Juegos cortos para completar en un fin de semana": (
        "¿Qué juegos puedo completar en un fin de semana?"),
}


@st.cache_resource
def obtener_coleccion():
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_collection(COLLECTION)


@st.cache_resource
def obtener_cliente_llm() -> tuple[OpenAI | None, str]:
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


def recuperar(coleccion, pregunta: str, k: int) -> list[dict]:
    """Busca los k juegos más relevantes en Chroma."""
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
            "Solo tengo datos (Ollama no está conectado). Respuesta basada en "
            f"los juegos recuperados:\n\n{contexto[:2000]}"
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

    try:
        coleccion = obtener_coleccion()
    except Exception:
        st.warning(
            "No hay colección Chroma. Ejecuta primero: "
            "`python preparar_corpus.py`"
        )
        coleccion = None

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if not st.session_state.messages:
        seleccion = st.pills(
            "Prueba a preguntar:",
            list(SUGERENCIAS.keys()),
            label_visibility="collapsed",
        )
        if seleccion:
            prompt = SUGERENCIAS[seleccion]
            st.session_state.messages.append(
                {"role": "user", "content": prompt})
            st.rerun()

    prompt = st.chat_input(
        "Pregunta sobre videojuegos...", submit_mode="disable")

    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            if coleccion is None:
                st.write("No hay datos indexados todavía.")
            else:
                resultados = recuperar(coleccion, prompt, k)
                if not resultados:
                    st.write(
                        "No he encontrado juegos relacionados. Prueba a "
                        "preguntar sobre géneros, plataformas o títulos específicos.")
                else:
                    contexto = formato_contexto(resultados)
                    respuesta = generar_respuesta(
                        prompt, contexto, st.session_state.messages[:-1])
                    if isinstance(respuesta, str):
                        st.write(respuesta)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": respuesta})
                    else:
                        texto = st.write_stream(respuesta)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": texto})

        st.rerun()
