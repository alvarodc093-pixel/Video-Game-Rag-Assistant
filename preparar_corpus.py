"""
VideoGameRadar - preparar_corpus.py
Indexa la información de videojuegos en Chroma para el chat RAG.
"""

import os
import sqlite3
from pathlib import Path

import chromadb
from tqdm import tqdm

DB_PATH = Path(__file__).resolve().parent / "datos.db"
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION = "videojuegos"


def obtener_juegos() -> list[dict]:
    """Obtiene todos los juegos de la base de datos con su información completa."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    query = """
        SELECT 
            j.id,
            j.nombre,
            j.descripcion,
            j.fecha_lanzamiento,
            j.rating,
            j.metacritic,
            j.playtime,
            j.esrb_rating,
            GROUP_CONCAT(DISTINCT g.nombre) as generos,
            GROUP_CONCAT(DISTINCT p.nombre) as plataformas
        FROM juegos j
        LEFT JOIN juego_generos jg ON j.id = jg.juego_id
        LEFT JOIN generos g ON jg.genero_id = g.id
        LEFT JOIN juego_plataformas jp ON j.id = jp.juego_id
        LEFT JOIN plataformas p ON jp.plataforma_id = p.id
        GROUP BY j.id
    """
    
    rows = conn.execute(query).fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def crear_documento_juego(juego: dict) -> str:
    """Crea un documento de texto para un juego."""
    partes = []
    
    partes.append(f"JUEGO: {juego['nombre']}")
    
    if juego.get('generos'):
        partes.append(f"GÉNEROS: {juego['generos']}")
    
    if juego.get('plataformas'):
        partes.append(f"PLATAFORMAS: {juego['plataformas']}")
    
    if juego.get('fecha_lanzamiento'):
        partes.append(f"LANZAMIENTO: {juego['fecha_lanzamiento']}")
    
    if juego.get('rating'):
        partes.append(f"RATING: {juego['rating']}/5")
    
    if juego.get('metacritic'):
        partes.append(f"METACRITIC: {juego['metacritic']}/100")
    
    if juego.get('playtime'):
        partes.append(f"TIEMPO PROMEDIO: {juego['playtime']} horas")
    
    if juego.get('esrb_rating'):
        partes.append(f"CLASIFICACIÓN: {juego['esrb_rating']}")
    
    if juego.get('descripcion'):
        desc = juego['descripcion'][:500]
        partes.append(f"DESCRIPCIÓN: {desc}")
    
    return "\n".join(partes)


def crear_metadatos_juego(juego: dict) -> dict:
    """Crea metadatos para un juego."""
    return {
        "juego_id": juego['id'],
        "nombre": juego['nombre'],
        "generos": juego.get('generos', ''),
        "plataformas": juego.get('plataformas', ''),
        "rating": juego.get('rating', 0),
        "metacritic": juego.get('metacritic', 0),
        "fecha_lanzamiento": juego.get('fecha_lanzamiento', ''),
    }


def preparar_corpus(borrar: bool = False):
    """Indexa todos los juegos en Chroma."""
    print("=== VideoGameRadar - Preparar Corpus ===\n")
    
    print("Conectando a Chroma...")
    client = chromadb.PersistentClient(path=DB_DIR)
    
    if borrar:
        print("Borrando colección existente...")
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
    
    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )
    
    print("Obteniendo juegos de la base de datos...")
    juegos = obtener_juegos()
    print(f"  -> {len(juegos)} juegos encontrados\n")
    
    if not juegos:
        print("No hay juegos en la base de datos. Ejecuta ingesta.py primero.")
        return
    
    print("Indexando juegos en Chroma...")
    
    batch_size = 100
    for i in tqdm(range(0, len(juegos), batch_size), desc="Indexando"):
        batch = juegos[i:i + batch_size]
        
        ids = [f"juego_{j['id']}" for j in batch]
        documentos = [crear_documento_juego(j) for j in batch]
        metadatos = [crear_metadatos_juego(j) for j in batch]
        
        collection.upsert(
            ids=ids,
            documents=documentos,
            metadatas=metadatos
        )
    
    total = collection.count()
    print(f"\n¡Listo! {total} juegos indexados en Chroma.")
    print(f"Ubicación de la base: {DB_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Preparar corpus para chat RAG")
    parser.add_argument("--borrar", action="store_true", help="Borrar y reindexar desde cero")
    args = parser.parse_args()
    
    preparar_corpus(borrar=args.borrar)
