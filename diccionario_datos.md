# Diccionario de Datos - VideoGame Radar

## Tablas Principales

### `juegos`
Almacena la información principal de cada videojuego.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Identificador único del juego (de RAWG) |
| slug | TEXT | Nombre simplificado para URLs |
| nombre | TEXT | Nombre del juego |
| descripcion | TEXT | Descripción del juego |
| fecha_lanzamiento | TEXT | Fecha de lanzamiento (YYYY-MM-DD) |
| rating | REAL | Calificación de usuarios (0-5) |
| rating_top | INTEGER | Calificación más alta recibida |
| ratings_count | INTEGER | Número de valoraciones de usuarios en RAWG |
| metacritic | INTEGER | Puntuación de Metacritic (0-100) |
| playtime | INTEGER | Tiempo promedio de juego en horas |
| background_image | TEXT | URL de la imagen principal |
| esrb_rating | TEXT | Clasificación por edades (E, E10+, T, M, AO) |
| updated | TEXT | Última actualización del registro |

### `generos`
Lista de géneros de videojuegos.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Identificador único del género |
| nombre | TEXT | Nombre del género (ej: Action, RPG) |
| slug | TEXT | Nombre simplificado para URLs |

### `plataformas`
Lista de plataformas de videojuegos.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Identificador único de la plataforma |
| nombre | TEXT | Nombre de la plataforma (ej: PlayStation 5) |
| slug | TEXT | Nombre simplificado para URLs |

### `tags`
Etiquetas o características de los juegos.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Identificador único del tag |
| nombre | TEXT | Nombre del tag (ej: multiplayer, co-op) |
| slug | TEXT | Nombre simplificado para URLs |

## Tablas de Relación

### `juego_generos`
Relación entre juegos y géneros (un juego puede tener varios géneros).

| Columna | Tipo | Descripción |
|---------|------|-------------|
| juego_id | INTEGER | ID del juego (FK → juegos.id) |
| genero_id | INTEGER | ID del género (FK → generos.id) |

### `juego_plataformas`
Relación entre juegos y plataformas (un juego puede estar en varias plataformas).

| Columna | Tipo | Descripción |
|---------|------|-------------|
| juego_id | INTEGER | ID del juego (FK → juegos.id) |
| plataforma_id | INTEGER | ID de la plataforma (FK → plataformas.id) |

### `juego_tags`
Relación entre juegos y tags.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| juego_id | INTEGER | ID del juego (FK → juegos.id) |
| tag_id | INTEGER | ID del tag (FK → tags.id) |

### `api_cache`
Cache de peticiones a la API de RAWG para evitar gastar cuota.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| endpoint | TEXT | Endpoint de la API (PRIMARY KEY) |
| params | TEXT | Parámetros de la petición (JSON) |
| response | TEXT | Respuesta de la API (JSON) |
| fecha | TEXT | Fecha de la petición |

## Fuentes de Datos

- **RAWG API**: https://api.rawg.io/docs/
- **Datos descargados**: Juegos, géneros, plataformas, calificaciones

## Notas

- Los ratings van de 0 a 5 (escala de RAWG)
- Metacritic va de 0 a 100
- El tiempo de juego es promedio en horas
- La API de RAWG es gratuita con límites de uso
