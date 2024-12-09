import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ta.trend import SMAIndicator, EMAIndicator, IchimokuIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice
import logging

class TechnicalAnalyzer:
    def __init__(self):
        self.indicators: Dict = {}
        self.patterns: Dict = {}
        self.current_analysis: Dict = {}
        
    def analyze_realtime(self, data: pd.DataFrame) -> Dict:
        """Analisa dados em tempo real e retorna indicadores"""
        try:
            # Calcula indicadores
            self._calculate_indicators(data)
            # Identifica padrões
            self._identify_patterns(data)
            # Gera análise atual
            self._generate_analysis()
            
            return self.current_analysis
            
        except Exception as e:
            logging.error(f"Erro na análise técnica: {e}")
            return {}
    
    def _calculate_indicators(self, data: pd.DataFrame):
        """Calcula indicadores técnicos"""
        try:
            # Médias Móveis
            self.indicators['sma_20'] = SMAIndicator(close=data['close'], window=20).sma_indicator()
            self.indicators['sma_50'] = SMAIndicator(close=data['close'], window=50).sma_indicator()
            self.indicators['ema_12'] = EMAIndicator(close=data['close'], window=12).ema_indicator()
            self.indicators['ema_26'] = EMAIndicator(close=data['close'], window=26).ema_indicator()
            
            # MACD
            macd = MACD(close=data['close'])
            self.indicators['macd_line'] = macd.macd()
            self.indicators['macd_signal'] = macd.macd_signal()
            
            # RSI
            self.indicators['rsi'] = RSIIndicator(close=data['close']).rsi()
            
            # Bollinger Bands
            bb = BollingerBands(close=data['close'])
            self.indicators['bb_high'] = bb.bollinger_hband()
            self.indicators['bb_low'] = bb.bollinger_lband()
            self.indicators['bb_mid'] = bb.bollinger_mavg()
            
            # Ichimoku
            ichimoku = IchimokuIndicator(high=data['high'], low=data['low'])
            self.indicators['ichimoku_a'] = ichimoku.ichimoku_a()
            self.indicators['ichimoku_b'] = ichimoku.ichimoku_b()
            
            # VWAP
            self.indicators['vwap'] = VolumeWeightedAveragePrice(
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume']
            ).volume_weighted_average_price()
            
        except Exception as e:
            logging.error(f"Erro ao calcular indicadores: {e}")
    
    def _identify_patterns(self, data: pd.DataFrame):
        """Identifica padrões de candlestick"""
        try:
            # Doji
            self.patterns['doji'] = self._is_doji(data)
            
            # Hammer
            self.patterns['hammer'] = self._is_hammer(data)
            
            # Engulfing
            self.patterns['bullish_engulfing'] = self._is_bullish_engulfing(data)
            self.patterns['bearish_engulfing'] = self._is_bearish_engulfing(data)
            
        except Exception as e:
            logging.error(f"Erro ao identificar padrões: {e}")
    
    def _generate_analysis(self):
        """Gera análise baseada nos indicadores e padrões"""
        try:
            self.current_analysis = {
                'indicators': self._get_latest_indicators(),
                'patterns': self.patterns,
                'signals': self._generate_signals(),
                'trend': self._identify_trend(),
                'strength': self._calculate_trend_strength()
            }
        except Exception as e:
            logging.error(f"Erro ao gerar análise: {e}")
    
    def _get_latest_indicators(self) -> Dict:
        """Retorna os valores mais recentes dos indicadores"""
        return {
            name: float(values.iloc[-1]) if not values.empty else None
            for name, values in self.indicators.items()
        }
    
    def _generate_signals(self) -> Dict:
        """Gera sinais baseados nos indicadores"""
        signals = {
            'macd_cross': self._check_macd_cross(),
            'rsi_signal': self._check_rsi_signal(),
            'bb_signal': self._check_bollinger_signal(),
            'ma_cross': self._check_ma_cross()
        }
        return signals
    
    def _identify_trend(self) -> str:
        """Identifica a tendência atual"""
        try:
            sma20 = self.indicators['sma_20'].iloc[-1]
            sma50 = self.indicators['sma_50'].iloc[-1]
            
            if sma20 > sma50:
                return 'uptrend'
            elif sma20 < sma50:
                return 'downtrend'
            else:
                return 'sideways'
                
        except Exception:
            return 'undefined'
    
    def _calculate_trend_strength(self) -> float:
        """Calcula a força da tendência atual"""
        try:
            rsi = self.indicators['rsi'].iloc[-1]
            macd = abs(self.indicators['macd_line'].iloc[-1])
            
            # Normaliza valores entre 0 e 1
            strength = (rsi / 100 + min(macd, 100) / 100) / 2
            return round(strength, 2)
            
        except Exception:
            return 0.0
