"""
VideoGameRadar - consultas.py
Funciones de acceso a datos para la app y análisis.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "datos.db"


def get_connection() -> sqlite3.Connection:
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def total_juegos() -> int:
    """ Retorna el total de juegos en la base de datos."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM juegos").fetchone()[0]
    conn.close()
    return total


def generos_principales(limite: int = 10) -> list[dict]:
    """Retorna los géneros con más juegos."""
    conn = get_connection()
    query = """
        SELECT g.nombre, COUNT(jg.juego_id) as total
        FROM generos g
        JOIN juego_generos jg ON g.id = jg.genero_id
        GROUP BY g.id
        ORDER BY total DESC
        LIMIT ?
    """
    rows = conn.execute(query, (limite,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def plataformas_principales(limite: int = 10) -> list[dict]:
    """Retorna las plataformas con más juegos."""
    conn = get_connection()
    query = """
        SELECT p.nombre, COUNT(jp.juego_id) as total
        FROM plataformas p
        JOIN juego_plataformas jp ON p.id = jp.plataforma_id
        GROUP BY p.id
        ORDER BY total DESC
        LIMIT ?
    """
    rows = conn.execute(query, (limite,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def juegos_top(limite: int = 10, min_votos: int = 100) -> list[dict]:
    """Retorna los juegos mejor valorados con al menos min_votos valoraciones."""
    conn = get_connection()
    query = """
        SELECT j.nombre, j.rating, j.metacritic, j.fecha_lanzamiento,
               GROUP_CONCAT(DISTINCT g.nombre) as generos
        FROM juegos j
        LEFT JOIN juego_generos jg ON j.id = jg.juego_id
        LEFT JOIN generos g ON jg.genero_id = g.id
        WHERE j.rating IS NOT NULL AND j.ratings_count >= ?
        GROUP BY j.id
        ORDER BY j.rating DESC
        LIMIT ?
    """
    rows = conn.execute(query, (min_votos, limite)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def juegos_recientes(limite: int = 10) -> list[dict]:
    """Retorna los juegos más recientes."""
    conn = get_connection()
    query = """
        SELECT j.nombre, j.rating, j.fecha_lanzamiento, j.background_image,
               GROUP_CONCAT(DISTINCT g.nombre) as generos
        FROM juegos j
        LEFT JOIN juego_generos jg ON j.id = jg.juego_id
        LEFT JOIN generos g ON jg.genero_id = g.id
        WHERE j.fecha_lanzamiento IS NOT NULL
        GROUP BY j.id
        ORDER BY j.fecha_lanzamiento DESC
        LIMIT ?
    """
    rows = conn.execute(query, (limite,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def buscar_juego(termino: str) -> list[dict]:
    """Busca juegos por nombre."""
    conn = get_connection()
    query = """
        SELECT j.id, j.nombre, j.rating, j.background_image,
               GROUP_CONCAT(DISTINCT g.nombre) as generos,
               GROUP_CONCAT(DISTINCT p.nombre) as plataformas
        FROM juegos j
        LEFT JOIN juego_generos jg ON j.id = jg.juego_id
        LEFT JOIN generos g ON jg.genero_id = g.id
        LEFT JOIN juego_plataformas jp ON j.id = jp.juego_id
        LEFT JOIN plataformas p ON jp.plataforma_id = p.id
        WHERE j.nombre LIKE ?
        GROUP BY j.id
        ORDER BY j.rating DESC
        LIMIT 20
    """
    rows = conn.execute(query, (f"%{termino}%",)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def juegos_por_genero(genero_slug: str) -> list[dict]:
    """Retorna juegos de un género específico."""
    conn = get_connection()
    query = """
        SELECT j.nombre, j.rating, j.fecha_lanzamiento, j.background_image
        FROM juegos j
        JOIN juego_generos jg ON j.id = jg.juego_id
        JOIN generos g ON jg.genero_id = g.id
        WHERE g.slug = ?
        ORDER BY j.rating DESC
    """
    rows = conn.execute(query, (genero_slug,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def juegos_por_plataforma(plataforma_slug: str) -> list[dict]:
    """Retorna juegos de una plataforma específica."""
    conn = get_connection()
    query = """
        SELECT j.nombre, j.rating, j.fecha_lanzamiento, j.background_image
        FROM juegos j
        JOIN juego_plataformas jp ON j.id = jp.juego_id
        JOIN plataformas p ON jp.plataforma_id = p.id
        WHERE p.slug = ?
        ORDER BY j.rating DESC
    """
    rows = conn.execute(query, (plataforma_slug,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def estadisticas_generales() -> dict:
    """Retorna estadísticas generales de la base de datos."""
    conn = get_connection()

    stats = {
        "total_juegos": conn.execute("SELECT COUNT(*) FROM juegos").fetchone()[0],
        "total_generos": conn.execute("SELECT COUNT(*) FROM generos").fetchone()[0],
        "total_plataformas": conn.execute("SELECT COUNT(*) FROM plataformas").fetchone()[0],
        "rating_promedio": conn.execute("SELECT AVG(rating) FROM juegos WHERE rating IS NOT NULL").fetchone()[0],
        "metacritic_promedio": conn.execute("SELECT AVG(metacritic) FROM juegos WHERE metacritic IS NOT NULL").fetchone()[0],
    }

    conn.close()
    return stats


def datos_para_eda() -> list[dict]:
    """Retorna todos los juegos para análisis exploratorio."""
    conn = get_connection()
    query = """
        SELECT
            j.*,
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
