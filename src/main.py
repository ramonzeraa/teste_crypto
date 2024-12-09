import asyncio
import logging
from src.core.bot import TradingBot
from src.utils.logger import CustomLogger
import sys
import signal
import time
from datetime import datetime

class BotRunner:
    def __init__(self):
        self.logger = CustomLogger("bot_runner").logger
        self.bot = None
        self.is_running = False
        
    async def start(self):
        """Inicia o bot"""
        try:
            self.logger.info("Iniciando bot de trading...")
            self.bot = TradingBot()
            self.is_running = True
            
            # Mensagem inicial
            self.bot.monitor.send_alert(
                "🚀 Bot iniciado\n"
                f"Par: {self.bot.symbol}\n"
                f"Timeframe: {self.bot.timeframe}\n"
                "Monitorando mercado..."
            )
            
            # Loop principal
            while self.is_running:
                try:
                    self.logger.info(f"Analisando mercado: {datetime.now()}")
                    
                    # Processa dados de mercado
                    analysis = await self.bot._process_market_data()
                    
                    if analysis:
                        self.logger.info(f"Análise técnica: {analysis.get('technical', {})}")
                        self.logger.info(f"Análise sentimento: {analysis.get('sentiment', {})}")
                    
                    # Atualiza status do portfólio
                    portfolio = self.bot._update_portfolio_status()
                    if portfolio:
                        self.logger.info(f"Status do portfólio: {portfolio}")
                    
                    # Aguarda intervalo configurado
                    await asyncio.sleep(60)  # Analisa a cada 1 minuto
                    
                except Exception as e:
                    self.logger.error(f"Erro no loop principal: {e}")
                    await asyncio.sleep(5)
            
        except Exception as e:
            self.logger.error(f"Erro fatal: {e}")
            self._handle_shutdown()
    
    def _handle_shutdown(self, signum=None, frame=None):
        """Gerencia desligamento gracioso"""
        try:
            self.logger.info("Iniciando desligamento...")
            self.is_running = False
            
            if self.bot:
                self.bot.monitor.send_alert(
                    "🛑 Bot finalizado\n"
                    "Todas as operações foram encerradas."
                )
            
            sys.exit(0)
            
        except Exception as e:
            self.logger.error(f"Erro no desligamento: {e}")
            sys.exit(1)

if __name__ == "__main__":
    runner = BotRunner()
    asyncio.run(runner.start())