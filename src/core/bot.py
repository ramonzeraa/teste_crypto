from src.data.binance_client import BinanceDataLoader
from src.analysis.technical_analysis import TechnicalAnalyzer
from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.analysis.ml_analyzer import MLAnalyzer
from src.utils.config import Config
from src.utils.logger import CustomLogger
from src.monitoring.monitor import SystemMonitor
from src.portfolio.portfolio_manager import PortfolioManager
from src.trading.execution import OrderExecutor
from ..utils.notifications import NotificationSystem
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import numpy as np
import time
from src.trading.risk_manager import RiskManager

class TradingBot:
    def __init__(self):
        # Inicializa logger e config primeiro
        self.logger = CustomLogger("trading_bot").logger
        self.config = Config()
        
        try:
            # Carrega configurações de trading
            self.symbol = self.config.config['trading']['symbol']
            self.timeframe = self.config.config['trading']['timeframe']
            
            # Inicializa componentes
            self.data_loader = BinanceDataLoader(
                api_key=self.config.binance_api_key,
                api_secret=self.config.binance_api_secret
            )
            
            self.technical_analyzer = TechnicalAnalyzer()
            self.sentiment_analyzer = SentimentAnalyzer()
            self.monitor = SystemMonitor(
                twilio_sid=self.config.twilio_sid,
                twilio_token=self.config.twilio_token,
                whatsapp_from=self.config.whatsapp_from,
                whatsapp_to=self.config.whatsapp_to
            )
            
            self.portfolio_manager = PortfolioManager()
            self.risk_manager = RiskManager(self.config.config['risk'])
            self.order_executor = OrderExecutor(
                api_key=self.config.binance_api_key,
                api_secret=self.config.binance_api_secret,
                risk_manager=self.risk_manager
            )
            
            # Tenta iniciar o stream algumas vezes
            retries = 3
            while retries > 0:
                try:
                    self.data_loader.start_market_stream(self.symbol)
                    break
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        raise
                    self.logger.warning(f"Tentando reconectar... ({3-retries}/3)")
                    time.sleep(2)
            
            self.logger.info("Bot inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do bot", exc_info=True)
            raise

    async def _process_market_data(self):
        """Processa dados de mercado"""
        try:
            # Obtém dados históricos
            klines = self.data_loader.get_historical_klines(
                symbol=self.symbol,
                interval=self.timeframe,
                limit=100
            )
            
            if klines.empty:
                self.logger.warning("Sem dados disponíveis")
                return None
            
            # Análise técnica com novos indicadores
            technical_analysis = self.technical_analyzer.analyze(klines)
            
            # Análise de sentimento
            sentiment = self.sentiment_analyzer.analyze_market_sentiment(self.symbol)
            
            # Atualiza métricas de risco com novas métricas
            current_prices = {
                self.symbol: self.data_loader.get_current_price(self.symbol)
            }
            self.risk_manager.update_risk_metrics(
                self.portfolio_manager.positions,
                current_prices
            )
            
            # Atualiza monitor com novas métricas
            self.monitor.update_metrics({
                'technical': technical_analysis,
                'sentiment': sentiment,
                'risk': self.risk_manager.risk_metrics,
                'portfolio': self.portfolio_manager.get_portfolio_status()
            })
            
            return {
                'technical': technical_analysis,
                'sentiment': sentiment,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Erro no processamento: {e}")
            self.monitor.report_error("processamento_dados", str(e))
            return None

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

    def _evaluate_signals(self, analysis: Dict):
        """Avalia sinais e executa ordens"""
        try:
            signal_strength = analysis['technical']['trend_strength']
            trade_direction = 1 if analysis['technical']['trend'] == 'bullish' else -1
            
            # Verifica força do sinal com novos parâmetros
            if abs(signal_strength) > self.signal_threshold:
                # Verifica condições de risco atualizadas
                if not self.risk_manager.can_trade():
                    self.logger.warning("Condições de risco não permitem trades")
                    return
                
                side = 'BUY' if trade_direction > 0 else 'SELL'
                self.logger.info(f"Sinal detectado: {side} - Força: {abs(signal_strength):.2f}")
                
                # Executa ordem com novos parâmetros de risco
                order_result = self.order_executor.execute_order(
                    symbol=self.symbol,
                    side=side,
                    signal_strength=abs(signal_strength),
                    technical_data=analysis['technical']
                )
                
                if order_result['status'] == 'success':
                    self._handle_successful_order(order_result, analysis)
                else:
                    self._handle_rejected_order(order_result)
            
        except Exception as e:
            self.logger.error(f"Erro na execução: {e}")
            self.monitor.report_error("execucao_ordem", str(e))
    
    def _handle_successful_order(self, order_result: Dict, analysis: Dict):
        """Processa ordem bem sucedida"""
        try:
            # Adiciona ao portfólio
            self.portfolio_manager.add_position({
                'symbol': self.symbol,
                'side': order_result['order']['side'],
                'entry_price': order_result['entry_price'],
                'quantity': order_result['position_size'],
                'stop_loss': order_result['stops']['stop_loss'],
                'take_profit': order_result['stops']['take_profit']
            })
            
            # Notifica
            self.monitor.send_alert(
                f"✅ Ordem executada\n"
                f"Par: {self.symbol}\n"
                f"Lado: {order_result['order']['side']}\n"
                f"Preço: {order_result['entry_price']:.2f}\n"
                f"Quantidade: {order_result['position_size']:.4f}\n"
                f"Stop Loss: {order_result['stops']['stop_loss']:.2f}\n"
                f"Take Profit: {order_result['stops']['take_profit']:.2f}\n"
                f"Score de Risco: {self.risk_manager.risk_metrics['risk_score']:.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao processar ordem: {e}")
    
    def _handle_rejected_order(self, order_result: Dict):
        """Processa ordem rejeitada"""
        try:
            self.logger.warning(f"Ordem rejeitada: {order_result['reason']}")
            
            if order_result['reason'] == 'risk_limit':
                self.monitor.send_alert(
                    "⚠️ Ordem rejeitada - Limite de risco\n"
                    f"Score de Risco: {self.risk_manager.risk_metrics['risk_score']:.2f}\n"
                    f"Exposição: {self.risk_manager.risk_metrics['position_exposure']:.2%}"
                )
                
        except Exception as e:
            self.logger.error(f"Erro ao processar rejeição: {e}")
    
    def _reduce_exposure(self):
        """Reduz exposição em caso de risco alto"""
        try:
            positions = self.portfolio_manager.get_positions()
            if not positions:
                return
                
            self.monitor.send_alert(
                "🔄 Reduzindo exposição\n"
                f"Score de Risco: {self.risk_manager.risk_metrics['risk_score']:.2f}\n"
                "Fechando posições mais antigas..."
            )
            
            # Fecha posições mais antigas primeiro
            sorted_positions = sorted(
                positions.items(),
                key=lambda x: x[1]['entry_time']
            )
            
            for symbol, position in sorted_positions[:len(sorted_positions)//2]:
                self.portfolio_manager.close_position(
                    symbol=symbol,
                    exit_price=self.data_loader.get_current_price(symbol),
                    exit_reason='risk_reduction'
                )
                
        except Exception as e:
            self.logger.error(f"Erro ao reduzir exposição: {e}")

    def _update_portfolio_status(self):
        """Atualiza status do portfólio"""
        try:
            # Obtém preços atuais
            current_prices = {
                self.symbol: self.data_loader.get_current_price(self.symbol)
            }
            
            # Atualiza posições
            self.portfolio_manager.update_positions(current_prices)
            
            # Obtém resumo atualizado
            summary = self.portfolio_manager.get_portfolio_summary()
            
            # Verifica PnL não realizado de forma segura
            unrealized_pnl = summary.get('metrics', {}).get('total_unrealized_pnl', 0.0)
            total_positions = summary.get('metrics', {}).get('position_count', 0)
            return_pct = summary.get('metrics', {}).get('return_pct', 0.0)
            
            # Notifica se necessário
            if unrealized_pnl < -100:  # $100 de perda
                self.monitor.send_alert(
                    f"⚠️ Alerta de P&L\n"
                    f"P&L Não Realizado: ${unrealized_pnl:.2f}\n"
                    f"Posições Abertas: {total_positions}\n"
                    f"Retorno Total: {return_pct:.2f}%"
                )
            
        except Exception as e:
            self.logger.error(f"Erro na atualização do portfólio: {e}")

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
