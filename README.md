# VideoGame Radar

Catálogo de videojuegos con datos de [RAWG](https://rawg.io): descarga los juegos en SQLite, los analiza en un notebook y los presenta en una app de Streamlit con búsqueda y un chat para pedir recomendaciones.

**Demo:** https://videogame-radar.vercel.app

## Qué responde

- ¿Qué juegos de rol, terror o estrategia están mejor valorados?
- ¿Qué juegos hay para PlayStation 5, Switch o PC?
- ¿Qué géneros y plataformas tienen más juegos?
- ¿Qué juegos multijugador o cooperativos me recomiendas?

## Datos

`ingesta.py` descarga de la API de RAWG los géneros, las plataformas y los 1.000 juegos más populares lanzados desde el año 2000 (los más añadidos a colecciones de usuarios), con sus géneros, plataformas y etiquetas. Todo se guarda en `datos.db` y las respuestas de la API se cachean, así que repetir la ingesta no gasta peticiones.

Ordenar por popularidad es deliberado: ordenar por rating trae sobre todo juegos con muy pocos votos y notas infladas.

La base completa no se sube al repo (`datos.db` está en `.gitignore`). La demo usa `data/catalogo_demo.db`, una copia sin la tabla de caché.

## Resultados

Del notebook [`notebooks/eda.ipynb`](notebooks/eda.ipynb), con los datos de octubre de 2026:

- **Géneros:** Action (703 juegos), Adventure (349), Indie (307) y RPG (268).
- **Plataformas:** casi todos están en PC (971); después, Xbox One (553) y PlayStation 4 (551).
- **Valoraciones:** rating medio de 3,73/5 y Metacritic medio de 80. Las dos notas están bastante relacionadas (correlación de 0,62).
- **Mejor valorados** (con 100 votos o más): Persona 5 Royal, The Last of Us Remastered y The Witcher 3.
- **Sesgo temporal:** casi no hay juegos de 2023 en adelante, porque los recientes aún no acumulan tantos usuarios en RAWG.

## La app

| Sección | Contenido |
|---|---|
| Visión general | KPIs, géneros y plataformas principales, top 10 |
| Catálogo | Juegos filtrados por género y plataforma |
| Géneros / Plataformas | Juegos y valoración media por género y por plataforma |
| Búsqueda | Por nombre, género, plataforma o etiqueta, con rating y Metacritic mínimos |
| Chat | Recomendaciones a partir de los juegos del catálogo |

### Chat

En local, `preparar_corpus.py` indexa una ficha por juego en ChromaDB y el chat recupera las más parecidas a la pregunta. Si hay un modelo de Ollama configurado en `secrets.toml`, redacta la respuesta con esos juegos como contexto; si no, muestra los juegos recuperados.

En la demo web no hay Chroma ni LLM: el chat traduce la pregunta a géneros, etiquetas y plataformas de RAWG ("terror" → Horror, "PS5" → PlayStation 5...) y busca con SQL.

## Ejecutarlo en local

```bash
pip install -r requirements.txt
copy secrets_ejemplo.toml secrets.toml   # y añade tu API key de RAWG
python ingesta.py --juegos 1000          # por defecto descarga 500
python preparar_corpus.py
streamlit run app.py
```

La API key es gratuita en https://rawg.io/apidocs. También puede pasarse con la variable de entorno `RAWG_API_KEY`. La ingesta borra la key de las respuestas antes de guardarlas en la caché.

## Estructura

```text
├── app.py                  # Entrada de la app de Streamlit
├── index.html              # Demo web (stlite)
├── ingesta.py              # API de RAWG → SQLite (con caché)
├── preparar_corpus.py      # Juegos → ChromaDB
├── consultas.py            # Consultas SQL compartidas
├── paginas/                # Una página por sección
├── data/catalogo_demo.db   # Base de la demo
├── notebooks/eda.ipynb     # Análisis exploratorio
└── diccionario_datos.md
```

## Tecnologías

Python, SQLite, Pandas, Streamlit, ChromaDB, Ollama (opcional), Matplotlib y Seaborn.

Datos de videojuegos e imágenes: [RAWG](https://rawg.io).

## Autor

Álvaro Domingo Cordón · [LinkedIn](https://www.linkedin.com/in/alvaro-domingo/) · [GitHub](https://github.com/alvarodc093-pixel)
