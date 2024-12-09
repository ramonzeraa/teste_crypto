"""
Análise de Mercado
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

class MarketAnalysis:
    def __init__(self):
        """Inicializa análise"""
        self.indicators = {}
        self.patterns = {}
        self.signals = []
        
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analisa dados de mercado"""
        try:
            self.calculate_indicators(data)
            self.identify_patterns()
            signal = self.generate_signals()
            
            return {
                'signal': signal,
                'indicators': self.indicators,
                'patterns': self.patterns,
                'confidence': self.calculate_confidence()
            }
        except Exception as e:
            raise Exception(f"Erro na análise de mercado: {str(e)}")
    
    def calculate_indicators(self, data: pd.DataFrame):
        """Calcula indicadores técnicos"""
        try:
            # Médias Móveis
            sma_20 = SMAIndicator(close=data['close'], window=20)
            sma_50 = SMAIndicator(close=data['close'], window=50)
            
            self.indicators['sma_20'] = sma_20.sma_indicator()
            self.indicators['sma_50'] = sma_50.sma_indicator()
            
            # RSI
            rsi = RSIIndicator(close=data['close'])
            self.indicators['rsi'] = rsi.rsi()
            
            # Bollinger Bands
            bb = BollingerBands(close=data['close'])
            self.indicators['bb_upper'] = bb.bollinger_hband()
            self.indicators['bb_lower'] = bb.bollinger_lband()
            self.indicators['bb_middle'] = bb.bollinger_mavg()
            
        except Exception as e:
            raise Exception(f"Erro ao calcular indicadores: {str(e)}")
    
    def is_uptrend(self) -> bool:
        """Verifica tendência de alta"""
        try:
            sma_20 = self.indicators['sma_20'].iloc[-1]
            sma_50 = self.indicators['sma_50'].iloc[-1]
            return sma_20 > sma_50
        except Exception as e:
            raise Exception(f"Erro ao verificar tendência: {str(e)}")
    
    def is_overbought(self) -> bool:
        """Verifica condição de sobrecompra"""
        return self.indicators['rsi'].iloc[-1] > 70
    
    def is_oversold(self) -> bool:
        """Verifica condição de sobrevenda"""
        return self.indicators['rsi'].iloc[-1] < 30
    
    def generate_signals(self) -> str:
        """Gera sinais de trading"""
        try:
            if self.is_uptrend():
                if self.is_oversold():
                    return "BUY"
                elif self.is_overbought():
                    return "SELL"
            else:
                if self.is_overbought():
                    return "SELL"
                
            return "HOLD"
            
        except Exception as e:
            raise Exception(f"Erro ao gerar sinais: {str(e)}")
    
    def identify_patterns(self):
        """Identifica padrões de mercado"""
        try:
            self.patterns['trend'] = self.identify_trend()
            self.patterns['support_resistance'] = self.identify_support_resistance()
            
        except Exception as e:
            raise Exception(f"Erro ao identificar padrões: {str(e)}")
    
    def identify_trend(self) -> str:
        """Identifica tendência atual"""
        try:
            sma_20 = self.indicators['sma_20'].iloc[-1]
            sma_50 = self.indicators['sma_50'].iloc[-1]
            
            if sma_20 > sma_50:
                return "UPTREND"
            elif sma_20 < sma_50:
                return "DOWNTREND"
            else:
                return "SIDEWAYS"
                
        except Exception as e:
            raise Exception(f"Erro ao identificar tendência: {str(e)}")
    
    def identify_support_resistance(self) -> Dict[str, float]:
        """Identifica suporte e resistência"""
        try:
            return {
                'support': self.indicators['bb_lower'].iloc[-1],
                'resistance': self.indicators['bb_upper'].iloc[-1]
            }
        except Exception as e:
            raise Exception(f"Erro ao identificar suporte/resistência: {str(e)}")
    
    def calculate_confidence(self) -> float:
        """Calcula nível de confiança do sinal"""
        try:
            confidence = 0.5  # Base
            
            # Ajusta baseado no RSI
            rsi = self.indicators['rsi'].iloc[-1]
            if rsi < 30 or rsi > 70:
                confidence += 0.2
                
            # Ajusta baseado na tendência
            if self.is_uptrend():
                confidence += 0.15
                
            # Ajusta baseado nas Bollinger Bands
            price = self.indicators['bb_middle'].iloc[-1]
            if price < self.indicators['bb_lower'].iloc[-1]:
                confidence += 0.15
            elif price > self.indicators['bb_upper'].iloc[-1]:
                confidence += 0.15
                
            return min(confidence, 1.0)
            
        except Exception as e:
            raise Exception(f"Erro ao calcular confiança: {str(e)}")