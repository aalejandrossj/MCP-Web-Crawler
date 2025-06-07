import os, sys, gc, logging, requests
from typing import TypedDict, List

from dotenv import load_dotenv
from langchain_google_community import GoogleSearchAPIWrapper
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
)
from crawl4ai.async_logger import AsyncLogger, LogLevel
from logger_config import log

if os.name == "nt":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Configurar logging para silenciar crawl4ai completamente
logging.basicConfig(level=logging.ERROR, handlers=[logging.StreamHandler(sys.stderr)])
log = logging.getLogger(__name__)

# Silenciar específicamente los loggers de crawl4ai
crawl4ai_logger = logging.getLogger("crawl4ai")
crawl4ai_logger.setLevel(logging.CRITICAL)
crawl4ai_logger.disabled = True

# Silenciar otros loggers relacionados
for logger_name in ["playwright", "asyncio", "httpx", "urllib3"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).disabled = True

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

class NewsArticle(TypedDict):
    title: str
    url: str
    description: str

class WebFinder:
    def url_finder(self, query: str, num_results: int = 5):
        try:
            return GoogleSearchAPIWrapper().results(query, num_results=num_results)
        except Exception as e:
            log.error(f"Error en búsqueda de Google: {e}")
            return []

    async def crawl_urls(self, urls: list[str]):
        # Crear logger completamente silencioso
        quiet_logger = AsyncLogger(
            verbose=False,
            log_level=LogLevel.CRITICAL   
        )        
        # Configuración para evitar cachés y logs
        cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, 
            stream=False,
            verbose=False,
            log_console=False
        )
        
        gc.collect()
        out: list[str] = []
        
        try:
            # Redirigir stdout temporalmente para capturar cualquier output
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            # Crear un buffer silencioso
            from io import StringIO
            devnull = StringIO()
            sys.stdout = devnull
            sys.stderr = devnull
            
            async with AsyncWebCrawler(
                logger=quiet_logger,
                verbose=False,
                headless=True
            ) as crawler:
                results = await crawler.arun_many(urls, config=cfg)
                for r in results:
                    if r.success and r.markdown:
                        # Limpiar el markdown de caracteres problemáticos
                        clean_markdown = r.markdown.replace('\x00', '').strip()
                        if clean_markdown:
                            out.append(clean_markdown)
                    
        except Exception as e:
            log.error(f"Error en crawling: {e}")
        finally:
            # Restaurar stdout/stderr
            sys.stdout = original_stdout  
            sys.stderr = original_stderr
            gc.collect()
        
        return out

    async def find_and_crawl(self, query: str, num_results: int = 5):
        search_results = self.url_finder(query, num_results)
        urls = [r["link"] for r in search_results if "link" in r]
        if not urls:
            return []
        return await self.crawl_urls(urls)

class WebFinderTools:
    def __init__(self):
        self._finder = WebFinder()

    def google_urls(self, query: str, num_results: int = 5) -> list[str]:
        """Obtiene URLs de búsqueda de Google"""
        try:
            results = self._finder.url_finder(query, num_results)
            return [r["link"] for r in results if "link" in r]
        except Exception as e:
            log.error(f"Error obteniendo URLs: {e}")
            return []

    async def crawl(self, urls: list[str]) -> list[str]:
        """Extrae contenido de URLs usando crawl4ai"""
        if not urls:
            return []
        return await self._finder.crawl_urls(urls)

    async def search_and_crawl(self, query: str, num_results: int = 5) -> list[str]:
        """Busca en Google y extrae contenido de los resultados"""
        return await self._finder.find_and_crawl(query, num_results)

    def news(self, query: str) -> List[NewsArticle]:
        """Obtiene noticias usando NewsAPI"""
        if not NEWS_API_KEY:
            log.error("NEWS_API_KEY no configurada")
            return []
            
        try:
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": query, "apiKey": NEWS_API_KEY},
                timeout=10,
            )
            r.raise_for_status()
            articles = r.json().get("articles", [])
            return [
                {
                    "title": art.get("title", ""),
                    "url": art.get("url", ""),
                    "description": art.get("description", "")
                }
                for art in articles
                if art.get("title") and art.get("url")
            ]
        except Exception as e:
            log.error(f"Error obteniendo noticias: {e}")
            return []