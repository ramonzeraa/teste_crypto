from ..utils.config import Config
from ..utils.notifications import NotificationSystem
from ..data.binance_client import BinanceDataLoader
from ..analysis.technical_analysis import TechnicalAnalyzer
from ..analysis.news_analyzer import NewsAnalyzer
from ..analysis.ml_analyzer import MLAnalyzer
from ..trading.order_manager import OrderManager
from ..risk.risk_manager import RiskManager
from ..monitoring.monitor import SystemMonitor
from ..utils.logger import CustomLogger
import logging
import pandas as pd
from datetime import datetime

class TradingBot:
    def __init__(self):
        # Inicializa logger e config primeiro
        self.logger = CustomLogger("trading_bot").logger
        self.config = Config()
        
        try:
            # Inicializa outros componentes
            self.monitor = SystemMonitor(
                twilio_sid=self.config.twilio_sid,
                twilio_token=self.config.twilio_token,
                whatsapp_from=self.config.whatsapp_from,
                whatsapp_to=self.config.whatsapp_to
            )
            
            # ... outros componentes ...
            
            self.logger.info("Bot inicializado com sucesso")
            
        except Exception as e:
            self.logger.error("Erro na inicialização do bot", exc_info=True)
            raise

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
        """Avalia sinais e executa ordens com gestão de risco"""
        if not analysis:
            return
            
        try:
            confidence = analysis['predictions'].get('confidence', 0)
            direction = analysis['predictions'].get('direction', None)
            
            # Verifica condições de risco
            account_info = self.data_loader.client.get_account()
            capital = float(account_info['totalAsset'])
            
            risk_check = self.risk_manager.can_open_position(
                capital=capital,
                position_size=capital * 0.01,  # 1% inicial
                confidence=confidence
            )
            
            if risk_check['allowed'] and confidence > 0.8:
                side = "BUY" if direction else "SELL"
                
                # Executa ordem
                order_result = self.order_manager.execute_order(
                    symbol=self.symbol,
                    side=side,
                    confidence=confidence
                )
                
                # Registra trade
                if order_result['status'] == 'success':
                    self.risk_manager.register_trade({
                        'symbol': self.symbol,
                        'side': side,
                        'size': order_result['position']['size'],
                        'entry_price': order_result['position']['entry_price'],
                        'confidence': confidence,
                        'profit_loss': 0  # Será atualizado no fechamento
                    })
            
            # Gera relatório periódico
            if datetime.now().minute == 0:  # A cada hora
                report = self.risk_manager.get_performance_report()
                logging.info(f"Relatório de Performance: {report}")
                
        except Exception as e:
            logging.error(f"Erro na avaliação de risco: {e}")

    def stop(self):
        """Para a execução do bot"""
        self.is_running = False
        self.notifications.send_alert(
            "🛑 Bot finalizado",
            priority="normal"
        )
