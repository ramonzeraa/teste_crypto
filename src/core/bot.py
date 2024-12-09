from ..utils.config import Config
from ..data.real_time_collector import RealTimeCollector
import logging

class TradingBot:
    def __init__(self):
        config = Config()
        self.collector = RealTimeCollector(
            api_key=config.binance_api_key,
            api_secret=config.binance_api_secret
        )
    
    def start(self):
        """Inicia o bot"""
        try:
            # Inicia coleta de dados
            self.collector.start_collection('BTCUSDT')
            
            while True:
                # Obtém dados em tempo real
                current_data = self.collector.get_current_data()
                
                # TODO: Implementar análise dos dados
                # TODO: Implementar machine learning
                # TODO: Implementar tomada de decisão
                
        except KeyboardInterrupt:
            self.collector.stop_collection()
