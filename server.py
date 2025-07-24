import sys, logging, os
from fastmcp import FastMCP
from tools import WebFinderTools
from prompts import WebFinderPrompts

if os.name == "nt":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stderr)])
log = logging.getLogger(__name__)

class WebFinderMCPServer:
    def __init__(self, name: str = "WebFinder"):
        self.mcp = FastMCP(name, stateless_http=True)
        
        self.tools = WebFinderTools()
        self.prompts = WebFinderPrompts()
        self._register_tools()
        self._register_prompts()

    # tools
    def _register_tools(self):
        self.mcp.tool()(self.tools.google_urls)
        self.mcp.tool()(self.tools.crawl)
        self.mcp.tool()(self.tools.search_and_crawl)
        self.mcp.tool()(self.tools.news)

    # prompts
    def _register_prompts(self):
        self.mcp.prompt()(self.prompts.google_urls_prompt)
        self.mcp.prompt()(self.prompts.crawl_prompt)
        self.mcp.prompt()(self.prompts.search_and_crawl_prompt)
        self.mcp.prompt()(self.prompts.news_prompt)

    def run(self, transport: str = "streamable-http", port: int = None, host: str = None):
        if port is None:
            port = int(os.getenv("PORT", 8081))
        if host is None:
            host = os.getenv("HOST", "0.0.0.0")
        log.info(f"Starting server on {host}:{port} with transport {transport}")
        try:
            self.mcp.run(transport=transport, port=port, host=host)
        except Exception as e:
            log.error(f"Failed to start server: {e}")
            raise

# exportación requerida por `mcp run`
mcp = WebFinderMCPServer().mcp

if __name__ == "__main__":
    log.info("Initializing WebFinder MCP Server...")
    server = WebFinderMCPServer()
    log.info("Server initialized, starting...")
    server.run(transport="streamable-http")
