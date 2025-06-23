from mcp.server.fastmcp.prompts import base
from typing import List, Union

class WebFinderPrompts:
    """Prompts implementation for WebFinder MCP server"""
    
    @staticmethod
    def google_urls_prompt(query: str, num_results: int = 5) -> List[base.Message]:
        """Prompt to get URLs from Google search."""
        return [
            base.UserMessage(
                f"""Busca en Google: {query}
                
                Obtén las {num_results} URLs más relevantes de la búsqueda.
                Presenta los resultados con los enlaces encontrados."""
            ),
        ]
    
    @staticmethod
    def crawl_prompt(urls: Union[str, List[str]]) -> List[base.Message]:
        """Prompt to crawl and extract content from URLs."""
        # Convert single URL to list if necessary
        url_list = [urls] if isinstance(urls, str) else urls
        return [
            base.UserMessage(
                f"""Extrae el contenido de las siguientes URLs:
                {', '.join(url_list)}
                
                Convierte el contenido a formato markdown y preséntalo."""
            ),
        ]
    
    @staticmethod
    def search_and_crawl_prompt(query: str, num_results: int = 5) -> List[base.Message]:
        """Prompt to search and crawl content from Google results."""
        return [
            base.UserMessage(
                f"""Busca en Gogle: {query}
                
                Obtén las {num_results} páginas más relevantes y extrae su contenido.
                Presenta el contenido de cada página en formato limpio y markdown"""
            ),
        ]
    
    @staticmethod
    def news_prompt(query: str) -> List[base.Message]:
        """Prompt to get news about a topic."""
        return [
            base.UserMessage(
                f"""Busca noticias sobre: {query}
                
                Obtén las noticias más recientes y preséntala con:
                - Títulos
                - URL
                - Descripción"""
            ),
        ]