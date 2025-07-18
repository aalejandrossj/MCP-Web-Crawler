# MCP Web-Finder

Un servicio MCP para búsqueda y análisis web avanzado.

## Requisitos

## Credenciales Necesarias
- Google API Key (para búsquedas de Google)
- Google CSE ID (para búsquedas personalizadas de Google)
- News API Key (para búsqueda de noticias)

## Guía rápida para obtener las tres credenciales necesarias


### 1. Google API Key

1. Entra en **Google Cloud Console** y elige un proyecto nuevo o existente.  
2. Abre **APIs & Services → Credentials → Create Credentials → API key**; copia la clave que se muestra.  
3. Habilita la API **“Custom Search JSON API”** desde **APIs & Services → Library** para ese proyecto.  

> Guarda la cadena resultante como `GOOGLE_API_KEY`.

---

### 2. Google Custom Search Engine ID (CSE ID)

1. Ve a **Programmable Search Engine** y crea un buscador, pon que tenga acceso a todas las URLs.  
2. Una vez creado, abre **Control Panel → Overview**; copia el valor **Search engine ID (cx)**.  

> Asigna ese valor a `GOOGLE_CSE_ID`

---

### 3. News API Key

1. Regístrate en **newsapi.org/register** (correo real; no acepta desechables).  
2. Confirma el correo y accede al panel; la clave aparece en la sección **API key**.  
3. En uso, añade la clave vía query param `apiKey` o cabecera `X-Api-Key`.  

> Almacénala como `NEWS_API_KEY`.

---

### 4. Archivo `.env` de referencia

```dotenv
# .env
GOOGLE_API_KEY=tu_clave_google
GOOGLE_CSE_ID=tu_cse_id
NEWS_API_KEY=tu_clave_newsapi
```
## Instalación

1. Clona el repositorio
2. Instala las dependencias con uv:
```bash
# Instalar uv si no lo tienes
pip install uv

# Crear y activar el entorno virtual con uv
uv venv

# En Windows:
.venv\Scripts\activate
# En Unix/MacOS:
source .venv/bin/activate

# Instalar dependencias
uv pip install -r requirements.txt
```

## Dependencias Principales

- **fastmcp**: Framework principal para el servidor MCP
- **crawl4ai**: Para web scraping y extracción de contenido
- **langchain-google-community**: Para búsquedas de Google
- **python-dotenv**: Para manejo de variables de entorno
- **requests**: Para peticiones HTTP
- **colorama**: Para formateo de logs

## Sistema de Logs

El proyecto utiliza un sistema de logging configurado en `logger_config.py`:

- Los logs principales se configuran a nivel INFO
- Se silencian los logs de las siguientes librerías:
  - crawl4ai (nivel CRITICAL)
  - playwright
  - asyncio
  - httpx
  - urllib3

Los logs se envían a stderr por defecto.

## Funcionalidades

El servidor MCP proporciona las siguientes herramientas:

1. **google_urls**: Búsqueda de URLs en Google
2. **crawl**: Extracción de contenido de páginas web
3. **search_and_crawl**: Combinación de búsqueda y extracción
4. **news**: Búsqueda y análisis de noticias

## Uso

Para iniciar el servidor:

```bash
python server.py
```

El servidor se ejecuta por defecto en modo stdio, pero puede configurarse para usar otros transportes.

## Estructura del Proyecto

- `server.py`: Punto de entrada principal y configuración del servidor MCP
- `tools.py`: Implementación de las herramientas de búsqueda web
- `prompts.py`: Definición de los prompts para cada herramienta
- `logger_config.py`: Configuración del sistema de logging


## Configuración para Claude Desktop:
```json
"webfinder": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "Path\\A\\Tu\\Directorio\\MCP-Web-Crawler",
        "python",
        "server.py"
      ],
      "env": {
        "GOOGLE_API_KEY": "",
        "GOOGLE_CSE_ID": "",
        "NEWS_API_KEY": ""
      }
}
```
## Se recomienda usar npx @modelcontextprotocol/inspector para probarlo