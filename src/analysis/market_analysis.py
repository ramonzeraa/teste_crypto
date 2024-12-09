"""
Módulo de Análise de Mercado
"""
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

class MarketAnalysis:
    def __init__(self):
        self.data = None
        self.last_analysis = None
        self.indicators = {}
        self.patterns = {}
        
    def analyze(self, market_data: pd.DataFrame) -> Dict:
        """Realiza análise completa do mercado"""
        try:
            self.data = market_data
            
            # Calcula indicadores
            self.calculate_indicators()
            
            # Identifica padrões
            self.identify_patterns()
            
            # Gera sinais
            signal = self.generate_signals()
            
            self.last_analysis = {
                'timestamp': datetime.now(),
                'indicators': self.indicators,
                'patterns': self.patterns,
                'signal': signal,
                'price': self.data['close'].iloc[-1]
            }
            
            return self.last_analysis
            
        except Exception as e:
            raise Exception(f"Erro na análise de mercado: {str(e)}")
    def calculate_indicators(self):
        """Calcula indicadores técnicos"""
        try:
            # Moving Averages
            self.indicators['sma_20'] = self.calculate_sma(period=20)
            self.indicators['sma_50'] = self.calculate_sma(period=50)
            self.indicators['ema_20'] = self.calculate_ema(period=20)
            
            # RSI
            self.indicators['rsi'] = self.calculate_rsi()
            
            # MACD
            macd_data = self.calculate_macd()
            self.indicators['macd'] = macd_data['macd']
            self.indicators['signal'] = macd_data['signal']
            
            # Bollinger Bands
            bb_data = self.calculate_bollinger_bands()
            self.indicators['bb_upper'] = bb_data['upper']
            self.indicators['bb_middle'] = bb_data['middle']
            self.indicators['bb_lower'] = bb_data['lower']
            
        except Exception as e:
            raise Exception(f"Erro ao calcular indicadores: {str(e)}")
    
    def identify_patterns(self):
        """Identifica padrões de mercado"""
        try:
            # Tendência
            self.patterns['trend'] = self.identify_trend()
            
            # Suporte/Resistência
            levels = self.find_support_resistance()
            self.patterns['support'] = levels['support']
            self.patterns['resistance'] = levels['resistance']
            
            # Candle Patterns
            self.patterns['candle_patterns'] = self.identify_candle_patterns()
            
        except Exception as e:
            raise Exception(f"Erro ao identificar padrões: {str(e)}")
    
    def generate_signals(self) -> str:
        """Gera sinais de trading baseados na análise"""
        try:
            signals = []
            
            # Análise de Tendência
            if self.is_uptrend():
                signals.append('TREND_UP')
            elif self.is_downtrend():
                signals.append('TREND_DOWN')
            
            # Análise de RSI
            rsi = self.indicators['rsi'].iloc[-1]
            if rsi < 30:
                signals.append('RSI_OVERSOLD')
            elif rsi > 70:
                signals.append('RSI_OVERBOUGHT')
            
            # Análise de MACD
            if self.is_macd_crossover():
                signals.append('MACD_CROSS_UP')
            elif self.is_macd_crossunder():
                signals.append('MACD_CROSS_DOWN')
            
            # Decisão Final
            return self.consolidate_signals(signals)
            
        except Exception as e:
            raise Exception(f"Erro ao gerar sinais: {str(e)}")
    def calculate_sma(self, period: int) -> pd.Series:
        """Calcula Simple Moving Average"""
        try:
            return self.data['close'].rolling(window=period).mean()
        except Exception as e:
            raise Exception(f"Erro ao calcular SMA: {str(e)}")
    
    def calculate_ema(self, period: int) -> pd.Series:
        """Calcula Exponential Moving Average"""
        try:
            return self.data['close'].ewm(span=period, adjust=False).mean()
        except Exception as e:
            raise Exception(f"Erro ao calcular EMA: {str(e)}")
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """Calcula Relative Strength Index"""
        try:
            delta = self.data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception as e:
            raise Exception(f"Erro ao calcular RSI: {str(e)}")
    
    def calculate_macd(self) -> Dict[str, pd.Series]:
        """Calcula MACD (Moving Average Convergence Divergence)"""
        try:
            exp1 = self.data['close'].ewm(span=12, adjust=False).mean()
            exp2 = self.data['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            return {
                'macd': macd,
                'signal': signal,
                'histogram': macd - signal
            }
        except Exception as e:
            raise Exception(f"Erro ao calcular MACD: {str(e)}")
    def calculate_bollinger_bands(self, period: int = 20, std: int = 2) -> Dict[str, pd.Series]:
        """Calcula Bollinger Bands"""
        try:
            middle = self.data['close'].rolling(window=period).mean()
            std_dev = self.data['close'].rolling(window=period).std()
            
            return {
                'upper': middle + (std_dev * std),
                'middle': middle,
                'lower': middle - (std_dev * std)
            }
        except Exception as e:
            raise Exception(f"Erro ao calcular Bollinger Bands: {str(e)}")
    
    def identify_trend(self) -> str:
        """Identifica a tendência atual"""
        try:
            sma_20 = self.indicators['sma_20'].iloc[-1]
            sma_50 = self.indicators['sma_50'].iloc[-1]
            current_price = self.data['close'].iloc[-1]
            
            if current_price > sma_20 and sma_20 > sma_50:
                return 'UPTREND'
            elif current_price < sma_20 and sma_20 < sma_50:
                return 'DOWNTREND'
            return 'SIDEWAYS'
            
        except Exception as e:
            raise Exception(f"Erro ao identificar tendência: {str(e)}")
    
    def find_support_resistance(self) -> Dict[str, List[float]]:
        """Encontra níveis de suporte e resistência"""
        try:
            highs = self.data['high'].values
            lows = self.data['low'].values
            
            resistance_levels = []
            support_levels = []
            
            # Identifica pontos de reversão
            for i in range(2, len(highs)-2):
                # Resistência
                if highs[i] > highs[i-1] and highs[i] > highs[i+1] and \
                   highs[i] > highs[i-2] and highs[i] > highs[i+2]:
                    resistance_levels.append(highs[i])
                
                # Suporte
                if lows[i] < lows[i-1] and lows[i] < lows[i+1] and \
                   lows[i] < lows[i-2] and lows[i] < lows[i+2]:
                    support_levels.append(lows[i])
            
            return {
                'support': sorted(set(support_levels)),
                'resistance': sorted(set(resistance_levels))
            }
            
        except Exception as e:
            raise Exception(f"Erro ao encontrar suporte/resistência: {str(e)}")
    
    def identify_candle_patterns(self) -> List[str]:
        """Identifica padrões de candlestick"""
        try:
            patterns = []
            
            # Doji
            if self.is_doji(-1):
                patterns.append('DOJI')
            
            # Hammer
            if self.is_hammer(-1):
                patterns.append('HAMMER')
            
            # Engulfing
            if self.is_engulfing(-1):
                patterns.append('ENGULFING')
            
            return patterns
            
        except Exception as e:
            raise Exception(f"Erro ao identificar padrões de candle: {str(e)}")
    
    def consolidate_signals(self, signals: List[str]) -> str:
        """Consolida sinais em uma única recomendação"""
        try:
            bullish_signals = len([s for s in signals if 'UP' in s or 'OVERSOLD' in s])
            bearish_signals = len([s for s in signals if 'DOWN' in s or 'OVERBOUGHT' in s])
            
            if bullish_signals > bearish_signals:
                return 'BUY'
            elif bearish_signals > bullish_signals:
                return 'SELL'
            return 'NEUTRAL'
            
        except Exception as e:
            raise Exception(f"Erro ao consolidar sinais: {str(e)}")
    
    # Métodos auxiliares para padrões de candle
    def is_doji(self, index: int) -> bool:
        """Verifica se o candle é um Doji"""
        candle = self.data.iloc[index]
        body = abs(candle['open'] - candle['close'])
        wick = candle['high'] - candle['low']
        return body <= (wick * 0.1)
    
    def is_hammer(self, index: int) -> bool:
        """Verifica se o candle é um Hammer"""
        candle = self.data.iloc[index]
        body = abs(candle['open'] - candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        return lower_wick > (body * 2)
    
    def is_engulfing(self, index: int) -> bool:
        """Verifica se há padrão Engulfing"""
        current = self.data.iloc[index]
        previous = self.data.iloc[index-1]
        
        bullish = (previous['close'] < previous['open'] and  # Previous red
                  current['close'] > current['open'] and    # Current green
                  current['close'] > previous['open'] and   # Current closes above previous open
                  current['open'] < previous['close'])      # Current opens below previous close
                  
        bearish = (previous['close'] > previous['open'] and  # Previous green
                  current['close'] < current['open'] and    # Current red
                  current['close'] < previous['open'] and   # Current closes below previous open
                  current['open'] > previous['close'])      # Current opens above previous close
                  
        return bullish or bearish