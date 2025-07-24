import os, sys, gc, logging, requests, re
from typing import List
from dataclasses import dataclass

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

@dataclass
class NewsArticle:
    title: str
    url: str
    description: str

class ContentFilter:
    """Clase para filtrar y limpiar contenido web extraído"""
    
    @staticmethod
    def remove_navigation_elements(content: str) -> str:
        """Remueve elementos de navegación comunes"""
        # Patrones de navegación a remover
        nav_patterns = [
            r'\[.*?\]\(.*?\)',  # Enlaces markdown [text](url)
            r'!\[.*?\]\(.*?\)', # Imágenes markdown ![alt](url)
            r'#{1,6}\s*(Menú|Menu|Navegación|Navigation).*?(?=\n|\Z)',
            r'#{1,6}\s*(Acerca de|About|Contacto|Contact|Servicios|Services).*?(?=\n|\Z)',
            r'X Close Menu.*?(?=\n|\Z)',
            r'Saltar al contenido.*?(?=\n|\Z)',
            r'Idioma\s*\*.*?(?=\n|\Z)',
            r'Cambio.*?(?=\n|\Z)',
        ]
        
        for pattern in nav_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content
    
    @staticmethod
    def remove_legal_content(content: str) -> str:
        """Remueve contenido legal y avisos"""
        legal_patterns = [
            r'Términos y Condiciones.*?(?=\n\n|\Z)',
            r'Privacy.*?(?=\n\n|\Z)',
            r'Cookie.*?(?=\n\n|\Z)',
            r'© \d{4}.*?(?=\n|\Z)',
            r'Todos los Derechos Reservados.*?(?=\n|\Z)',
            r'Estás saliendo del sitio.*?(?=\n\n|\Z)',
            r'This website uses cookies.*?(?=\n\n|\Z)',
            r'Privacy Preference Center.*?(?=\n\n|\Z)',
            r'Powered by.*?(?=\n|\Z)',
        ]
        
        for pattern in legal_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        return content
    
    @staticmethod
    def remove_social_media_links(content: str) -> str:
        """Remueve enlaces de redes sociales"""
        social_patterns = [
            r'\[.*?(Facebook|Twitter|Youtube|Instagram|tumblr|Spotify).*?\].*?(?=\n|\Z)',
            r'\[.*?(App Store|Google Play).*?\].*?(?=\n|\Z)',
        ]
        
        for pattern in social_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content
    
    @staticmethod
    def remove_repetitive_content(content: str) -> str:
        """Remueve contenido repetitivo"""
        lines = content.split('\n')
        seen_lines = set()
        unique_lines = []
        
        for line in lines:
            line_clean = line.strip()
            if line_clean and line_clean not in seen_lines:
                seen_lines.add(line_clean)
                unique_lines.append(line)
            elif not line_clean:  # Mantener líneas vacías
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    @staticmethod
    def extract_main_content(content: str, keywords: List[str] = None) -> str:
        """Extrae el contenido principal basado en palabras clave"""
        if not keywords:
            return content
        
        paragraphs = content.split('\n\n')
        relevant_paragraphs = []
        
        for paragraph in paragraphs:
            # Verificar si el párrafo contiene alguna palabra clave
            if any(keyword.lower() in paragraph.lower() for keyword in keywords):
                relevant_paragraphs.append(paragraph)
            # También incluir párrafos que sigan a párrafos relevantes (contexto)
            elif relevant_paragraphs and len(paragraph.strip()) > 50:
                relevant_paragraphs.append(paragraph)
        
        return '\n\n'.join(relevant_paragraphs) if relevant_paragraphs else content
    
    @staticmethod
    def clean_markdown_formatting(content: str) -> str:
        """Limpia formato markdown excesivo"""
        # Remover múltiples saltos de línea
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remover espacios al inicio y final de líneas
        lines = [line.rstrip() for line in content.split('\n')]
        content = '\n'.join(lines)
        
        # Remover líneas que solo contengan símbolos
        lines = [line for line in content.split('\n') 
                if not re.match(r'^[\s\-_=*]+$', line)]
        content = '\n'.join(lines)
        
        return content.strip()
    
    @classmethod
    def clean_content(cls, content: str, keywords: List[str] = None) -> str:
        """Aplica todos los filtros de limpieza"""
        # Aplicar filtros en orden
        content = cls.remove_navigation_elements(content)
        content = cls.remove_legal_content(content)
        content = cls.remove_social_media_links(content)
        content = cls.remove_repetitive_content(content)
        
        # Extraer contenido principal si hay palabras clave
        if keywords:
            content = cls.extract_main_content(content, keywords)
        
        content = cls.clean_markdown_formatting(content)
        
        return content

class WebFinder:
    def url_finder(self, query: str, num_results: int = 5, exclude_youtube: bool = True):
        try:
            # Modificar la consulta para excluir YouTube si es necesario
            if exclude_youtube:
                # Añadir exclusión de YouTube a la búsqueda
                modified_query = f"{query} -site:youtube.com -site:youtu.be"
            else:
                modified_query = query
                
            results = GoogleSearchAPIWrapper().results(modified_query, num_results=num_results)
            
            # Filtro adicional para asegurar que no hay URLs de YouTube
            if exclude_youtube:
                filtered_results = []
                for result in results:
                    url = result.get("link", "")
                    if not self._is_youtube_url(url):
                        filtered_results.append(result)
                return filtered_results
            
            return results
        except Exception as e:
            log.error(f"Error en búsqueda de Google: {e}")
            return []
    
    def _is_youtube_url(self, url: str) -> bool:
        """Verifica si una URL pertenece a YouTube"""
        youtube_domains = [
            'youtube.com',
            'youtu.be',
            'www.youtube.com',
            'm.youtube.com',
            'music.youtube.com'
        ]
        
        url_lower = url.lower()
        return any(domain in url_lower for domain in youtube_domains)

    async def crawl_urls(self, urls: list[str], keywords: List[str] = None):
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
                            # Aplicar filtros de limpieza
                            filtered_content = ContentFilter.clean_content(
                                clean_markdown, 
                                keywords
                            )
                            
                            # Solo añadir si el contenido filtrado tiene suficiente información
                            if len(filtered_content.strip()) > 100:
                                out.append(filtered_content)
                    
        except Exception as e:
            log.error(f"Error en crawling: {e}")
        finally:
            # Restaurar stdout/stderr
            sys.stdout = original_stdout  
            sys.stderr = original_stderr
            gc.collect()
        
        return out

    async def find_and_crawl(self, query: str, num_results: int = 5, exclude_youtube: bool = True):
        search_results = self.url_finder(query, num_results, exclude_youtube)
        urls = [r["link"] for r in search_results if "link" in r]
        if not urls:
            return []
        
        # Extraer palabras clave de la consulta para filtrado
        keywords = query.split()
        return await self.crawl_urls(urls, keywords)

class WebFinderTools:
    def __init__(self):
        self._finder = WebFinder()

    def google_urls(self, query: str, num_results: int = 5, exclude_youtube: bool = True) -> list[str]:
        """Obtiene URLs de búsqueda de Google (excluyendo YouTube por defecto)"""
        try:
            results = self._finder.url_finder(query, num_results, exclude_youtube)
            return [r["link"] for r in results if "link" in r]
        except Exception as e:
            log.error(f"Error obteniendo URLs: {e}")
            return []

    async def crawl(self, urls: list[str]) -> list[str]:
        """Extrae contenido de URLs usando crawl4ai"""
        if not urls:
            return []
        return await self._finder.crawl_urls(urls)

    async def search_and_crawl(self, query: str, num_results: int = 5, exclude_youtube: bool = True) -> list[str]:
        """Busca en Google y extrae contenido de los resultados (excluyendo YouTube por defecto)"""
        return await self._finder.find_and_crawl(query, num_results, exclude_youtube)

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
                NewsArticle(
                    title=art.get("title", ""),
                    url=art.get("url", ""),
                    description=art.get("description", "")
                )
                for art in articles
                if art.get("title") and art.get("url")
            ]
        except Exception as e:
            log.error(f"Error obteniendo noticias: {e}")
            return []