"""
VideoGameRadar - ingesta.py
Descarga información de videojuegos desde la API de RAWG
y la almacena en SQLite con cache.
"""

import os
import json
import sqlite3
import time
import tomllib
from pathlib import Path
from datetime import datetime

import requests
from tqdm import tqdm

DB_PATH = Path(__file__).resolve().parent / "datos.db"
RAWG_BASE = "https://api.rawg.io/api"


def cargar_config() -> dict:
    """Carga la API key desde secrets.toml o variables de entorno."""
    api_key = os.environ.get("RAWG_API_KEY")
    if api_key:
        return {"api_key": api_key}

    ruta = Path(__file__).resolve().parent / "secrets.toml"
    if ruta.exists():
        with ruta.open("rb") as f:
            cfg = tomllib.load(f)
        return cfg.get("rawg", {})
    return {}


def inicializar_db(conn: sqlite3.Connection):
    """Crea las tablas necesarias si no existen."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS api_cache (
            endpoint TEXT,
            params TEXT,
            response TEXT,
            fecha TEXT,
            PRIMARY KEY (endpoint, params)
        );

        CREATE TABLE IF NOT EXISTS juegos (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE,
            nombre TEXT,
            descripcion TEXT,
            fecha_lanzamiento TEXT,
            rating REAL,
            rating_top INTEGER,
            ratings_count INTEGER,
            metacritic INTEGER,
            playtime INTEGER,
            background_image TEXT,
            esrb_rating TEXT,
            updated TEXT
        );

        CREATE TABLE IF NOT EXISTS generos (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            slug TEXT
        );

        CREATE TABLE IF NOT EXISTS plataformas (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            slug TEXT
        );

        CREATE TABLE IF NOT EXISTS juego_generos (
            juego_id INTEGER,
            genero_id INTEGER,
            PRIMARY KEY (juego_id, genero_id),
            FOREIGN KEY (juego_id) REFERENCES juegos(id),
            FOREIGN KEY (genero_id) REFERENCES generos(id)
        );

        CREATE TABLE IF NOT EXISTS juego_plataformas (
            juego_id INTEGER,
            plataforma_id INTEGER,
            PRIMARY KEY (juego_id, plataforma_id),
            FOREIGN KEY (juego_id) REFERENCES juegos(id),
            FOREIGN KEY (plataforma_id) REFERENCES plataformas(id)
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            slug TEXT
        );

        CREATE TABLE IF NOT EXISTS juego_tags (
            juego_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (juego_id, tag_id),
            FOREIGN KEY (juego_id) REFERENCES juegos(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        );
    """)


def fetch_cache(conn: sqlite3.Connection, endpoint: str, params: dict) -> dict | None:
    """Busca en cache si ya tenemos esta petición."""
    params_str = json.dumps(params, sort_keys=True)
    row = conn.execute(
        "SELECT response FROM api_cache WHERE endpoint = ? AND params = ?",
        (endpoint, params_str)
    ).fetchone()
    if row:
        return json.loads(row[0])
    return None


def guard_cache(conn: sqlite3.Connection, endpoint: str, params: dict, response: dict):
    """Guarda la respuesta en cache."""
    params_str = json.dumps(params, sort_keys=True)
    resp_str = json.dumps(response)
    fecha = datetime.now().isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO api_cache (endpoint, params, response, fecha) VALUES (?, ?, ?, ?)",
        (endpoint, params_str, resp_str, fecha)
    )
    conn.commit()


def fetch_api(conn: sqlite3.Connection, api_key: str, endpoint: str, params: dict = None) -> dict:
    """Hace una petición a la API con cache.

    La key se añade solo a la petición: no se guarda en la caché para que la base
    pueda compartirse sin exponerla.
    """
    params = dict(params or {})

    cached = fetch_cache(conn, endpoint, params)
    if cached:
        return cached

    url = f"{RAWG_BASE}/{endpoint}"
    resp = requests.get(url, params={**params, "key": api_key}, timeout=30)
    resp.raise_for_status()
    # RAWG devuelve URLs de paginacion (next/previous) que incluyen la key: se borra
    # antes de guardar la respuesta en la cache.
    data = json.loads(resp.text.replace(api_key, "REDACTED"))

    guard_cache(conn, endpoint, params, data)
    return data


def descargar_generos(conn: sqlite3.Connection, api_key: str):
    """Descarga todos los géneros disponibles."""
    print("Descargando géneros...")
    data = fetch_api(conn, api_key, "genres")

    for genre in data.get("results", []):
        conn.execute(
            "INSERT OR IGNORE INTO generos (id, nombre, slug) VALUES (?, ?, ?)",
            (genre["id"], genre["name"], genre["slug"])
        )
    conn.commit()
    print(f"  -> {len(data.get('results', []))} géneros guardados")


def descargar_plataformas(conn: sqlite3.Connection, api_key: str):
    """Descarga todas las plataformas disponibles."""
    print("Descargando plataformas...")
    data = fetch_api(conn, api_key, "platforms")

    for plat in data.get("results", []):
        conn.execute(
            "INSERT OR IGNORE INTO plataformas (id, nombre, slug) VALUES (?, ?, ?)",
            (plat["id"], plat["name"], plat["slug"])
        )
    conn.commit()
    print(f"  -> {len(data.get('results', []))} plataformas guardadas")


def descargar_juegos(conn: sqlite3.Connection, api_key: str, num_juegos: int = 500):
    """Descarga información detallada de videojuegos."""
    print(f"Descargando {num_juegos} videojuegos...")

    page_size = 40
    pages = (num_juegos // page_size) + 1

    total_guardados = 0

    for page in range(1, pages + 1):
        params = {
            "page": page,
            "page_size": page_size,
            # Por popularidad: ordenar por rating trae sobre todo juegos con muy pocos votos.
            "ordering": "-added",
            "dates": "2000-01-01,2026-12-31",
        }

        data = fetch_api(conn, api_key, "games", params)
        results = data.get("results", [])

        for juego in results:
            try:
                guardar_juego(conn, juego)
                total_guardados += 1
            except Exception as e:
                print(f"  Error guardando juego {juego.get('name', '?')}: {e}")

        if total_guardados >= num_juegos:
            break

        time.sleep(0.5)

    print(f"  -> {total_guardados} juegos guardados en total")


def guardar_juego(conn: sqlite3.Connection, juego: dict):
    """Guarda un juego y sus relaciones en la base de datos."""
    juego_id = juego["id"]

    esrb = juego.get("esrb_rating")
    esrb_name = esrb.get("name") if esrb else None

    conn.execute("""
        INSERT OR REPLACE INTO juegos
        (id, slug, nombre, descripcion, fecha_lanzamiento, rating, rating_top,
         ratings_count, metacritic, playtime, background_image, esrb_rating, updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        juego_id,
        juego.get("slug"),
        juego.get("name"),
        juego.get("description", ""),
        juego.get("released"),
        juego.get("rating"),
        juego.get("rating_top"),
        juego.get("ratings_count"),
        juego.get("metacritic"),
        juego.get("playtime"),
        juego.get("background_image"),
        esrb_name,
        juego.get("updated")
    ))

    for genre in juego.get("genres") or []:
        conn.execute(
            "INSERT OR IGNORE INTO generos (id, nombre, slug) VALUES (?, ?, ?)",
            (genre["id"], genre["name"], genre["slug"])
        )
        conn.execute(
            "INSERT OR IGNORE INTO juego_generos (juego_id, genero_id) VALUES (?, ?)",
            (juego_id, genre["id"])
        )

    for tag in juego.get("tags") or []:
        conn.execute(
            "INSERT OR IGNORE INTO tags (id, nombre, slug) VALUES (?, ?, ?)",
            (tag["id"], tag["name"], tag["slug"])
        )
        conn.execute(
            "INSERT OR IGNORE INTO juego_tags (juego_id, tag_id) VALUES (?, ?)",
            (juego_id, tag["id"])
        )

    for plat in juego.get("platforms") or []:
        platform = plat.get("platform", {})
        conn.execute(
            "INSERT OR IGNORE INTO plataformas (id, nombre, slug) VALUES (?, ?, ?)",
            (platform["id"], platform["name"], platform["slug"])
        )
        conn.execute(
            "INSERT OR IGNORE INTO juego_plataformas (juego_id, plataforma_id) VALUES (?, ?)",
            (juego_id, platform["id"])
        )

    conn.commit()


def main():
    """Función principal de ingesta."""
    import argparse
    parser = argparse.ArgumentParser(description="Ingesta de datos desde RAWG API")
    parser.add_argument("--force", action="store_true", help="Forzar descarga ignorando cache")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar consultas sin ejecutar")
    parser.add_argument("--juegos", type=int, default=500, help="Número de juegos a descargar")
    args = parser.parse_args()

    config = cargar_config()
    api_key = config.get("api_key")

    if not api_key:
        print("ERROR: No se encontró la API key de RAWG.")
        print("Copia secrets_ejemplo.toml como secrets.toml y añade tu API key.")
        print("O establece la variable de entorno RAWG_API_KEY.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    inicializar_db(conn)

    if args.force:
        conn.execute("DELETE FROM api_cache")
        conn.commit()
        print("Cache borrado.")

    if args.dry_run:
        paginas = args.juegos // 40 + 1
        print("Consultas previstas: genres, platforms y "
              f"{paginas} páginas de games (40 juegos por página, ordenadas por rating).")
        conn.close()
        return

    print("=== VideoGameRadar - Ingesta de datos ===\n")

    descargar_generos(conn, api_key)
    descargar_plataformas(conn, api_key)
    descargar_juegos(conn, api_key, args.juegos)

    total = conn.execute("SELECT COUNT(*) FROM juegos").fetchone()[0]
    print(f"\nTotal de juegos en base de datos: {total}")

    conn.close()
    print("\n¡Ingesta completada!")


if __name__ == "__main__":
    main()
