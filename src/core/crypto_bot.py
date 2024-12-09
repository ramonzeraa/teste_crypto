"""
Core do Bot de Trading
"""
from typing import Dict, Any
from datetime import datetime

from src.analysis.market_analysis import MarketAnalysis
from src.data.loader import DataLoader
from src.utils.logger import TradingLogger
from src.utils.notifications import NotificationSystem
from src.utils.config import Config

class CryptoTradingBot:
    def __init__(self):
        """Inicializa o bot"""
        self.config = Config()
        self.logger = TradingLogger()
        self.data_loader = DataLoader()
        self.market_analysis = MarketAnalysis()
        self.notifier = NotificationSystem()
        
        self.current_position = None
        self.is_running = False
        self.last_update = None
        
    def start(self):
        """Inicia o bot"""
        try:
            self.is_running = True
            self.logger.log_info("Bot iniciado com sucesso")
            self.notifier.send_alert(
                title="Bot Iniciado",
                message="Sistema iniciado com sucesso",
                priority="normal"
            )
        except Exception as e:
            self.logger.log_error(e, "Erro ao iniciar bot")
            raise
    
    def stop(self):
        """Para o bot"""
        self.is_running = False
        self.logger.log_info("Bot parado")
        
    def update(self):
        """Atualiza estado do bot"""
        try:
            if not self.is_running:
                return
                
            self.last_update = datetime.now()
            market_data = self.data_loader.get_latest_data(
                self.config.trading_config['symbol'],
                self.config.trading_config['timeframe']
            )
            
            analysis = self.market_analysis.analyze(market_data)
            self._process_signals(analysis)
            
        except Exception as e:
            self.logger.log_error(e, "Erro na atualização do bot")
            raise

