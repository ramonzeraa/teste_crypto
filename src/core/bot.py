from ..utils.config import Config
from ..utils.notifications import NotificationSystem
from ..data.binance_client import BinanceDataLoader
from ..analysis.technical_analysis import TechnicalAnalyzer
from ..analysis.sentiment_analyzer import SentimentAnalyzer
from ..analysis.ml_analyzer import MLAnalyzer
from ..trading.order_manager import OrderManager
from ..risk.risk_manager import RiskManager
from ..monitoring.monitor import SystemMonitor
from ..utils.logger import CustomLogger
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict
import json
import numpy as np

class TradingBot:
    def __init__(self):
        # Inicializa logger e config primeiro
        self.logger = CustomLogger("trading_bot").logger
        self.config = Config()
        
        try:
            # Inicializa data loader com credenciais
            self.data_loader = BinanceDataLoader(
                api_key=self.config.binance_api_key,
                api_secret=self.config.binance_api_secret
            )
            
            # Inicializa outros componentes
            self.technical_analyzer = TechnicalAnalyzer()
            self.sentiment_analyzer = SentimentAnalyzer()
            self.ml_analyzer = MLAnalyzer()
            self.monitor = SystemMonitor(
                twilio_sid=self.config.twilio_sid,
                twilio_token=self.config.twilio_token,
                whatsapp_from=self.config.whatsapp_from,
                whatsapp_to=self.config.whatsapp_to
            )
            
            # Configurações de trading
            self.symbol = self.config.config['trading']['symbol']
            self.timeframe = self.config.config['trading']['timeframe']
            self.is_running = False
            
            # Registra callbacks para dados em tempo real
            self.data_loader.add_realtime_callback(self._handle_realtime_data)
            
            # Inicia stream de mercado
            self.data_loader.start_market_stream(self.symbol)
            
            self.logger.info("Bot inicializado com sucesso")
            
        except Exception as e:
            self.logger.error("Erro na inicialização do bot", exc_info=True)
            raise

    def _handle_realtime_data(self, data: Dict):
        """Processa dados em tempo real"""
        try:
            if 'e' in data:  # Evento Binance
                if data['e'] == 'trade':
                    self._process_trade(data)
                elif data['e'] == 'depth':
                    self._process_orderbook(data)
                elif data['e'] == 'kline':
                    self._process_kline(data)
                    
        except Exception as e:
            self.logger.error(f"Erro no processamento de dados: {e}")
    
    def _process_trade(self, trade_data: Dict):
        """Processa trade em tempo real"""
        try:
            price = float(trade_data['p'])
            quantity = float(trade_data['q'])
            
            # Atualiza análises
            self.technical_analyzer.update_price(price)
            market_depth = self.data_loader.get_market_depth(self.symbol)
            
            # Verifica sinais
            if self._should_analyze_signals():
                self._analyze_trading_signals({
                    'price': price,
                    'quantity': quantity,
                    'market_depth': market_depth
                })
                
        except Exception as e:
            self.logger.error(f"Erro no processamento de trade: {e}")
    
    def _process_orderbook(self, depth_data: Dict):
        """Processa atualização do orderbook"""
        try:
            if self._should_analyze_signals():
                market_depth = self.data_loader.get_market_depth(self.symbol)
                self._analyze_trading_signals({'market_depth': market_depth})
                
        except Exception as e:
            self.logger.error(f"Erro no processamento do orderbook: {e}")
    
    def _should_analyze_signals(self) -> bool:
        """Verifica se deve analisar sinais"""
        # Implementa lógica para evitar análises muito frequentes
        return True  # Simplificado para o exemplo
    
    def _analyze_trading_signals(self, data: Dict):
        """Analisa sinais de trading"""
        try:
            # Análise técnica
            technical_signals = self.technical_analyzer.analyze()
            
            # Análise de sentimento
            sentiment = self.sentiment_analyzer.analyze_market_sentiment(self.symbol)
            
            # Análise ML
            ml_predictions = self.ml_analyzer.predict({
                'technical': technical_signals,
                'sentiment': sentiment,
                'market_depth': data.get('market_depth', {})
            })
            
            # Avalia sinais
            self._evaluate_signals({
                'technical': technical_signals,
                'sentiment': sentiment,
                'predictions': ml_predictions,
                'market_data': data
            })
            
        except Exception as e:
            self.logger.error(f"Erro na análise de sinais: {e}")

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

    def _analyze_market_conditions(self) -> Dict:
        """Analisa condições atuais do mercado"""
        try:
            current_time = datetime.now()
            
            # Análise técnica
            technical_analysis = self.technical_analyzer.analyze()
            
            # Análise de sentimento (com controle de frequência)
            sentiment_data = {}
            if (not self.last_sentiment_check or 
                current_time - self.last_sentiment_check >= self.sentiment_check_interval):
                sentiment_data = self.sentiment_analyzer.analyze_market_sentiment(self.symbol)
                self.last_sentiment_check = current_time
            
            # Dados de mercado em tempo real
            market_depth = self.data_loader.get_market_depth(self.symbol)
            
            # Combina análises
            analysis = {
                'technical': technical_analysis,
                'sentiment': sentiment_data,
                'market_depth': market_depth,
                'timestamp': current_time
            }
            
            # Registra análise
            self.logger.info(f"Análise de mercado: {json.dumps(analysis, default=str)}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de mercado: {e}")
            return {}

    def _evaluate_signals(self, analysis: Dict):
        """Avalia sinais de trading"""
        try:
            if not analysis:
                return
            
            # Obtém dados de sentimento
            sentiment = analysis.get('sentiment', {})
            sentiment_score = sentiment.get('overall', 0)
            fear_greed = sentiment.get('fear_greed_index', {}).get('value', 50)
            
            # Obtém sinais técnicos
            technical = analysis.get('technical', {})
            
            # Combina sinais
            signal_strength = self._calculate_signal_strength(
                technical_score=technical.get('trend_strength', 0),
                sentiment_score=sentiment_score,
                fear_greed_score=fear_greed
            )
            
            # Define direção do trade
            trade_direction = self._determine_trade_direction(
                technical=technical,
                sentiment=sentiment
            )
            
            # Se sinal forte o suficiente, notifica
            if abs(signal_strength) > self.config.config['analysis']['ml']['confidence_threshold']:
                self.monitor.send_alert(
                    f"🎯 Sinal forte detectado!\n"
                    f"Direção: {'COMPRA' if trade_direction > 0 else 'VENDA'}\n"
                    f"Força do Sinal: {abs(signal_strength):.2%}\n"
                    f"Sentimento: {sentiment_score:.2f}\n"
                    f"Fear & Greed: {fear_greed}\n"
                    f"Análise Técnica: {technical.get('trend', 'neutro')}"
                )
            
        except Exception as e:
            self.logger.error(f"Erro na avaliação de sinais: {e}")

    def _calculate_signal_strength(self, technical_score: float, 
                                 sentiment_score: float,
                                 fear_greed_score: float) -> float:
        """Calcula força do sinal combinando diferentes métricas"""
        try:
            # Normaliza Fear & Greed para [-1, 1]
            fear_greed_normalized = (fear_greed_score - 50) / 50
            
            # Pesos para cada componente
            weights = {
                'technical': 0.5,
                'sentiment': 0.3,
                'fear_greed': 0.2
            }
            
            # Calcula média ponderada
            signal = (
                technical_score * weights['technical'] +
                sentiment_score * weights['sentiment'] +
                fear_greed_normalized * weights['fear_greed']
            )
            
            return np.clip(signal, -1, 1)
            
        except Exception as e:
            self.logger.error(f"Erro no cálculo de força do sinal: {e}")
            return 0.0

    def _determine_trade_direction(self, technical: Dict, sentiment: Dict) -> int:
        """Determina direção do trade (-1 para venda, 1 para compra)"""
        try:
            # Pontuação técnica
            technical_score = 1 if technical.get('trend') == 'bullish' else -1
            
            # Pontuação de sentimento
            sentiment_score = np.sign(sentiment.get('overall', 0))
            
            # Combina sinais (prioriza análise técnica)
            if technical_score == sentiment_score:
                return technical_score
            else:
                return technical_score  # Em caso de divergência, segue o técnico
                
        except Exception as e:
            self.logger.error(f"Erro na determinação de direção: {e}")
            return 0
