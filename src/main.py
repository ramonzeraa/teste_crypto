import asyncio
from src.core.runner import BotRunner
import logging

# Adicione estas linhas no início
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Iniciando aplicação...")

if __name__ == "__main__":
    runner = BotRunner()
    asyncio.run(runner.start())