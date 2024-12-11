from typing import Dict, Optional
import logging
from datetime import datetime

class TradingStrategy:
    def __init__(self, config: Dict):
        self.logger = logging.getLogger('trading_strategy')
        self.config = config
        self.min_signal_strength = 0.6
        
    def generate_signal(self, technical_data: Dict, sentiment_data: Dict) -> Dict:
        """Gera sinal de trading baseado nas análises"""
        try:
            # Análise técnica
            tech_signal = self._analyze_technical(technical_data)
            
            # Análise de sentimento
            sentiment_signal = self._analyze_sentiment(sentiment_data)
            
            # Combina sinais
            signal_strength = (
                tech_signal['strength'] * 0.7 +  # 70% peso técnico
                sentiment_signal['strength'] * 0.3  # 30% peso sentimento
            )
            
            # Valida força mínima do sinal
            if abs(signal_strength) < self.min_signal_strength:
                return {
                    'action': 'HOLD',
                    'strength': 0,
                    'reason': 'Sinal fraco'
                }
            
            # Determina ação
            action = 'BUY' if signal_strength > 0 else 'SELL'
            
            return {
                'action': action,
                'strength': abs(signal_strength),
                'reason': self._generate_reason(tech_signal, sentiment_signal),
                'technical': tech_signal,
                'sentiment': sentiment_signal,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar sinal: {str(e)}")
            return {'action': 'HOLD', 'strength': 0, 'reason': str(e)} 
    
    def _analyze_technical(self, data: Dict) -> Dict:
        """Analisa indicadores técnicos"""
        try:
            # Pontuação para cada indicador
            scores = {
                'trend': 1 if data['trend'] == 'bullish' else -1,
                'rsi': self._score_rsi(data['rsi']['value']),
                'macd': 1 if data['macd']['value'] > 0 else -1,
                'adx': 1 if data['adx']['trend_strength'] > 25 else 0,
                'bb': self._score_bollinger(data['bb']),
                'stoch': self._score_stochastic(data['stoch']['value'])
            }
            
            # Calcula força do sinal técnico
            strength = sum(scores.values()) / len(scores)
            
            return {
                'signal': 'BUY' if strength > 0 else 'SELL',
                'strength': strength,
                'scores': scores
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise técnica: {str(e)}")
            return {'signal': 'HOLD', 'strength': 0}
    
    def _analyze_sentiment(self, data: Dict) -> Dict:
        """Analisa dados de sentimento"""
        try:
            # Normaliza Fear & Greed
            fear_greed_score = (data['fear_greed_index']['value'] - 50) / 50
            
            # Analisa tendência de volume
            volume_score = 0.5 if data['volume_trend']['trend'] == 'increasing' else -0.5
            
            # Momentum do preço
            price_score = data['price_action']['momentum'] if data['price_action']['trend'] == 'bullish' else -data['price_action']['momentum']
            
            # Combina scores
            strength = (
                fear_greed_score * 0.4 +
                volume_score * 0.3 +
                price_score * 0.3
            )
            
            return {
                'signal': 'BUY' if strength > 0 else 'SELL',
                'strength': strength,
                'fear_greed': fear_greed_score,
                'volume': volume_score,
                'price_action': price_score
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de sentimento: {str(e)}")
            return {'signal': 'HOLD', 'strength': 0}
    
    def _score_rsi(self, value: float) -> float:
        """Pontua RSI"""
        if value < 30:
            return 1  # Sobrevenda
        elif value > 70:
            return -1  # Sobrecompra
        return 0
    
    def _score_bollinger(self, bb_data: Dict) -> float:
        """Pontua Bandas de Bollinger"""
        width = bb_data['width']
        if width > 0.03:  # Alta volatilidade
            return 0
        return 0.5
    
    def _score_stochastic(self, value: float) -> float:
        """Pontua Estocástico"""
        if value < 20:
            return 1
        elif value > 80:
            return -1
        return 0
    
    def _generate_reason(self, tech: Dict, sentiment: Dict) -> str:
        """Gera explicação para o sinal"""
        reasons = []
        
        if tech['strength'] > 0:
            reasons.append("Indicadores técnicos positivos")
        elif tech['strength'] < 0:
            reasons.append("Indicadores técnicos negativos")
            
        if sentiment['strength'] > 0:
            reasons.append("Sentimento de mercado positivo")
        elif sentiment['strength'] < 0:
            reasons.append("Sentimento de mercado negativo")
            
        return " e ".join(reasons)