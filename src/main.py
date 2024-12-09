import asyncio
import logging
from core.bot import TradingBot
from utils.logger import CustomLogger
import sys
import signal

class BotRunner:
    def __init__(self):
        self.logger = CustomLogger("bot_runner").logger
        self.bot = None
        self.is_running = False
        
        # Configura handlers para sinais do sistema
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    async def start(self):
        """Inicia o bot"""
        try:
            self.logger.info("Iniciando bot de trading...")
            self.bot = TradingBot()
            self.is_running = True
            
            # Mensagem inicial
            self.bot.monitor.send_alert(
                "🚀 Bot iniciado\n"
                "Monitorando mercado..."
            )
            
            # Loop principal
            while self.is_running:
                try:
                    # Processa dados de mercado
                    await self.bot._process_market_data()
                    
                    # Atualiza status do portfólio
                    self.bot._update_portfolio_status()
                    
                    # Pequena pausa para não sobrecarregar
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Erro no loop principal: {e}")
                    await asyncio.sleep(5)  # Pausa maior em caso de erro
            
        except Exception as e:
            self.logger.error(f"Erro fatal: {e}")
            self._handle_shutdown()
    
    def _handle_shutdown(self, signum=None, frame=None):
        """Gerencia desligamento gracioso"""
        try:
            self.logger.info("Iniciando desligamento...")
            self.is_running = False
            
            if self.bot:
                # Fecha posições abertas se configurado
                if self.bot.config.config.get('trading', {}).get('close_positions_on_shutdown', False):
                    self.logger.info("Fechando posições abertas...")
                    for symbol in self.bot.portfolio_manager.positions:
                        current_price = self.bot.data_loader.get_current_price(symbol)
                        self.bot.portfolio_manager.close_position(
                            symbol=symbol,
                            exit_price=current_price,
                            exit_reason='shutdown'
                        )
                
                # Notifica desligamento
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