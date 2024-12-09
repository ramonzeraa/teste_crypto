from ..utils.config import Config
from ..utils.notifications import NotificationSystem
from ..data.binance_client import BinanceDataLoader
from ..analysis.technical_analysis import TechnicalAnalyzer
from ..analysis.news_analyzer import NewsAnalyzer
from ..analysis.ml_analyzer import MLAnalyzer
from ..trading.order_manager import OrderManager
import logging
import pandas as pd
from datetime import datetime

class TradingBot:
    def __init__(self):
        # Inicialização dos componentes
        self.config = Config()
        self.notifications = NotificationSystem()
        self.data_loader = BinanceDataLoader(
            self.config.binance_api_key,
            self.config.binance_api_secret
        )
        self.technical_analyzer = TechnicalAnalyzer()
        self.news_analyzer = NewsAnalyzer()
        self.ml_analyzer = MLAnalyzer()
        self.order_manager = OrderManager(
            self.config.binance_api_key,
            self.config.binance_api_secret
        )
        
        # Configurações de trading
        self.symbol = "BTCUSDT"
        self.timeframe = "1h"
        self.is_running = False
        self.last_analysis = None
        
    def start(self):
        """Inicia o bot de trading"""
        try:
            self.is_running = True
            self.notifications.send_alert(
                "🤖 Bot iniciado com sucesso!",
                priority="normal"
            )
            
            while self.is_running:
                analysis = self._process_market_data()
                self._evaluate_signals(analysis)
                
        except Exception as e:
            logging.error(f"Erro crítico: {str(e)}")
            self.notifications.send_alert(
                f"🚨 Erro crítico no bot: {str(e)}",
                priority="high"
            )
            self.stop()

    def _process_market_data(self):
        """Processa dados do mercado em tempo real"""
        try:
            # Coleta dados
            current_data = self.data_loader.get_historical_klines(
                symbol=self.symbol,
                interval=self.timeframe
            )
            
            if current_data is not None:
                # Análise técnica
                technical_analysis = self.technical_analyzer.analyze_realtime(current_data)
                
                # Análise de notícias
                news_analysis = self.news_analyzer.analyze_news()
                
                # Previsões ML
                ml_predictions = self.ml_analyzer.predict(
                    technical_analysis,
                    news_analysis
                )
                
                # Combina todas as análises
                analysis = {
                    'timestamp': datetime.now(),
                    'technical': technical_analysis,
                    'news': news_analysis,
                    'predictions': ml_predictions
                }
                
                # Aprende com resultados anteriores
                if self.last_analysis:
                    actual_price_change = current_data['close'].iloc[-1] - current_data['close'].iloc[-2]
                    self.ml_analyzer.learn(self.last_analysis, actual_price_change)
                
                self.last_analysis = analysis
                return analysis
                
        except Exception as e:
            logging.error(f"Erro no processamento: {e}")
            return None

    def _evaluate_signals(self, analysis: dict):
        """Avalia sinais e executa ordens"""
        if not analysis:
            return
            
        try:
            confidence = analysis['predictions'].get('confidence', 0)
            direction = analysis['predictions'].get('direction', None)
            
            # Alta confiança na previsão
            if confidence > 0.8:
                # Determina direção da ordem
                side = "BUY" if direction else "SELL"
                
                # Executa ordem
                order_result = self.order_manager.execute_order(
                    symbol=self.symbol,
                    side=side,
                    confidence=confidence
                )
                
                # Notifica resultado
                if order_result['status'] == 'success':
                    self.notifications.send_alert(
                        f"🎯 Ordem executada: {side}\n"
                        f"Preço: {order_result['position']['entry_price']}\n"
                        f"Tamanho: {order_result['position']['size']}\n"
                        f"Confiança: {confidence:.2%}",
                        priority="high"
                    )
                else:
                    logging.warning(f"Ordem rejeitada: {order_result['reason']}")
            
        except Exception as e:
            logging.error(f"Erro na execução de ordens: {e}")

    def stop(self):
        """Para a execução do bot"""
        self.is_running = False
        self.notifications.send_alert(
            "🛑 Bot finalizado",
            priority="normal"
        )
