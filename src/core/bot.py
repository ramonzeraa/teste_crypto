from ..utils.config import Config
from ..data.real_time_collector import RealTimeCollector
import logging
import pandas as pd

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
                self._process_market_data()
                
        except KeyboardInterrupt:
            self.collector.stop_collection()
    
    def _process_market_data(self):
        """Processa dados do mercado em tempo real"""
        try:
            # Obtém dados
            current_data = self.collector.get_current_data()
            
            # Análise técnica
            technical_analysis = self.technical_analyzer.analyze_realtime(
                pd.DataFrame(current_data['trades'])
            )
            
            # Análise de notícias
            news_analysis = self.news_analyzer.analyze_news()
            market_impact = self.news_analyzer.get_market_impact()
            
            # Combina análises
            analysis = {
                'technical': technical_analysis,
                'news': news_analysis,
                'market_impact': market_impact
            }
            
            # Log da análise completa
            logging.info(f"Análise completa: {analysis}")
            
            # TODO: Alimentar sistema de machine learning
            # TODO: Tomar decisões de trading
            
        except Exception as e:
            logging.error(f"Erro no processamento: {e}")
