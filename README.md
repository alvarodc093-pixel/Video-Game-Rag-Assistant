# VideoGame Radar - Catálogo de Videojuegos con Chat RAG

Proyecto de verano: un **producto de datos completo** que descarga información de
videojuegos desde la API de [RAWG](https://rawg.io), las guarda en SQLite, las
analiza en un notebook y las presenta en una app Streamlit con **chat RAG** para
encontrar y descubrir videojuegos.

## El problema que resuelve

Mirando datos reales, la app responde preguntas como:

- ¿Qué juegos multijugador me recomiendas?
- ¿Cuáles son los mejores juegos de rol?
- ¿Qué juegos están disponibles para PlayStation 5?
- ¿Qué juegos de terror son buenos?
- ¿Qué juegos puedo completar en un fin de semana?
- ¿Qué géneros son más populares?
- ¿Qué plataformas tienen más juegos?
- ¿Cuáles son los juegos mejor valorados?

## Cómo ejecutarlo

### 1. Requisitos

- Python 3.10+
- Una cuenta gratis en RAWG para obtener `api_key`
  (https://rawg.io/apidocs)
- Opcional para el chat con IA: [Ollama](https://ollama.com) en local

### 2. Instalar dependencias

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### 3. Configurar las claves

Copia `secrets_ejemplo.toml` como `secrets.toml` y rellena tus claves:

```toml
[rawg]
api_key = "TU_API_KEY"

[ollama]
base_url = "http://localhost:11434/v1"
model = "llama3"
```

`secrets.toml` está en `.gitignore`: nunca lo subas a GitHub.

### 4. Descargar los datos (ingesta)

```bash
python ingesta.py            # descarga lo que falte (cachea en datos.db)
python ingesta.py --force    # ignora el cache y vuelve a pedirlo todo
python ingesta.py --dry-run  # muestra las consultas sin llamar a la API
python ingesta.py --juegos 1000  # descarga 1000 juegos
```

La ingesta hace peticiones a RAWG y las cachea en la tabla `api_cache`.
Re-ejecutar el script **no gasta peticiones nuevas**: solo descarga lo que
falte.

### 5. EDA

```bash
jupyter notebook notebooks/eda.ipynb
```

O desde VS Code abriendo `notebooks/eda.ipynb`.

### 6. Indexar el corpus para el chat

```bash
python preparar_corpus.py            # indexa los juegos en Chroma
python preparar_corpus.py --borrar   # reindexa desde cero
```

### 7. Lanzar la app

```bash
streamlit run app.py
```

## Estructura del repositorio

```
VideoGameRadar/
├── README.md                este archivo
├── requirements.txt
├── .gitignore
├── secrets_ejemplo.toml     plantilla de claves (sin valores reales)
├── ingesta.py               API de RAWG -> SQLite (con cache)
├── preparar_corpus.py       juegos -> Chroma (corpus del chat)
├── consultas.py             acceso a datos para app y EDA
├── datos.db                 la base SQLite (se genera al ejecutar ingesta)
├── diccionario_datos.md     documentación de columnas y tablas
├── notebooks/
│   └── eda.ipynb            análisis exploratorio con conclusiones
└── paginas/
    ├── vision.py            KPIs y contexto
    ├── catalogo.py          explorador de videojuegos con filtros
    ├── generos.py           análisis por géneros
    ├── plataformas.py       análisis por plataformas
    ├── buscar.py            búsqueda avanzada
    └── chat.py              chat RAG (Chroma + Ollama)
```

## API Utilizada

### RAWG API

- **URL**: https://rawg.io/apidocs
- **Datos**: +350,000 videojuegos
- **Información**: nombres, descripciones, géneros, plataformas, calificaciones, imágenes
- **Límites**: Gratis para uso no comercial (<100k usuarios/mes)

## Notas y limitaciones

- **RAWG API**: tiene límites de peticiones en el plan gratuito.
- **Calificaciones**: no todos los juegos tienen Metacritic.
- **Imágenes**: dependen de RAWG, pueden no estar disponibles para todos.
- **Modelo de embeddings**: Chroma descarga automáticamente un modelo de embeddings
  la primera vez que se indexa.
- **Despliegue en Streamlit Cloud**: la parte de datos funciona; el chat usa
  Ollama local para embeddings/generación, que no existe en la nube.

## Licencia y créditos

Datos de videojuegos: [RAWG API](https://rawg.io). Uso académico.
