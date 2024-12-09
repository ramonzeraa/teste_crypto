import pandas as pd
import numpy as np
from typing import Dict
import logging
from datetime import datetime

class TechnicalAnalyzer:
    def __init__(self):
        self.indicators = {}
        self.signals = {}

    def analyze(self, data: pd.DataFrame) -> Dict:
        """Analisa dados técnicos"""
        try:
            if data.empty:
                return {}

            # Calcula indicadores
            self.calculate_rsi(data)
            self.calculate_macd(data)
            self.calculate_bollinger_bands(data)
            
            # Gera sinais
            signals = {
                'rsi': self._analyze_rsi(),
                'macd': self._analyze_macd(),
                'bb': self._analyze_bb(),
                'trend': self._analyze_trend(data),
                'timestamp': datetime.now()
            }
            
            # Calcula força geral do sinal
            signals['trend_strength'] = self._calculate_trend_strength(signals)
            
            return signals
            
        except Exception as e:
            logging.error(f"Erro na análise técnica: {e}")
            return {}

    def calculate_rsi(self, data: pd.DataFrame, period: int = 14):
        """Calcula RSI"""
        try:
            close_delta = data['close'].diff()
            
            # Calcula ganhos e perdas
            gain = (close_delta.where(close_delta > 0, 0)).rolling(window=period).mean()
            loss = (-close_delta.where(close_delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            self.indicators['rsi'] = 100 - (100 / (1 + rs))
            
        except Exception as e:
            logging.error(f"Erro no cálculo do RSI: {e}")

    def calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calcula MACD"""
        try:
            exp1 = data['close'].ewm(span=fast, adjust=False).mean()
            exp2 = data['close'].ewm(span=slow, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            
            self.indicators['macd'] = macd
            self.indicators['macd_signal'] = signal_line
            self.indicators['macd_hist'] = macd - signal_line
            
        except Exception as e:
            logging.error(f"Erro no cálculo do MACD: {e}")

    def calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std: int = 2):
        """Calcula Bandas de Bollinger"""
        try:
            sma = data['close'].rolling(window=period).mean()
            rolling_std = data['close'].rolling(window=period).std()
            
            self.indicators['bb_upper'] = sma + (rolling_std * std)
            self.indicators['bb_middle'] = sma
            self.indicators['bb_lower'] = sma - (rolling_std * std)
            
        except Exception as e:
            logging.error(f"Erro no cálculo das Bandas de Bollinger: {e}")

    def _analyze_rsi(self) -> Dict:
        """Analisa sinais do RSI"""
        try:
            rsi = self.indicators.get('rsi', pd.Series())
            if rsi.empty:
                return {}
                
            last_rsi = rsi.iloc[-1]
            return {
                'value': last_rsi,
                'oversold': last_rsi < 30,
                'overbought': last_rsi > 70
            }
            
        except Exception as e:
            logging.error(f"Erro na análise do RSI: {e}")
            return {}

    def _analyze_macd(self) -> Dict:
        """Analisa sinais do MACD"""
        try:
            hist = self.indicators.get('macd_hist', pd.Series())
            if hist.empty:
                return {}
                
            last_hist = hist.iloc[-1]
            prev_hist = hist.iloc[-2]
            
            return {
                'value': last_hist,
                'crossover': prev_hist < 0 and last_hist > 0,
                'crossunder': prev_hist > 0 and last_hist < 0
            }
            
        except Exception as e:
            logging.error(f"Erro na análise do MACD: {e}")
            return {}

    def _analyze_bb(self) -> Dict:
        """Analisa sinais das Bandas de Bollinger"""
        try:
            if not all(k in self.indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
                return {}
                
            last_close = self.indicators['bb_middle'].index[-1]
            
            return {
                'upper': self.indicators['bb_upper'].iloc[-1],
                'lower': self.indicators['bb_lower'].iloc[-1],
                'middle': self.indicators['bb_middle'].iloc[-1],
                'width': (self.indicators['bb_upper'].iloc[-1] - 
                         self.indicators['bb_lower'].iloc[-1]) / 
                        self.indicators['bb_middle'].iloc[-1]
            }
            
        except Exception as e:
            logging.error(f"Erro na análise das BBs: {e}")
            return {}

    def _analyze_trend(self, data: pd.DataFrame) -> str:
        """Analisa tendência geral"""
        try:
            sma_20 = data['close'].rolling(window=20).mean()
            sma_50 = data['close'].rolling(window=50).mean()
            
            if sma_20.iloc[-1] > sma_50.iloc[-1]:
                return 'bullish'
            elif sma_20.iloc[-1] < sma_50.iloc[-1]:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logging.error(f"Erro na análise de tendência: {e}")
            return 'neutral'

    def _calculate_trend_strength(self, signals: Dict) -> float:
        """Calcula força da tendência"""
        try:
            strength = 0.0
            
            # RSI
            if 'rsi' in signals:
                rsi = signals['rsi']['value']
                if rsi > 70:
                    strength += 0.3
                elif rsi < 30:
                    strength -= 0.3
            
            # MACD
            if 'macd' in signals:
                if signals['macd']['crossover']:
                    strength += 0.3
                elif signals['macd']['crossunder']:
                    strength -= 0.3
            
            # Tendência
            if signals.get('trend') == 'bullish':
                strength += 0.4
            elif signals.get('trend') == 'bearish':
                strength -= 0.4
            
            return np.clip(strength, -1, 1)
            
        except Exception as e:
            logging.error(f"Erro no cálculo da força da tendência: {e}")
            return 0.0
