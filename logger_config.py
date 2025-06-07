import os
import sys
import logging

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