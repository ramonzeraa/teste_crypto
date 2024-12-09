import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
import logging
from ..utils.config import config

class TechnicalIndicators:
    def __init__(self):
        pass
        
    def add_all_indicators(self, df):
        """Adiciona todos os indicadores técnicos ao DataFrame"""
        try:
            # Médias Móveis
            df['sma_9'] = df['close'].rolling(window=9).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
            df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
            
            # MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp1 - exp2
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_upper'] = df['bb_middle'] + 2 * df['close'].rolling(window=20).std()
            df['bb_lower'] = df['bb_middle'] - 2 * df['close'].rolling(window=20).std()
            
            # Volume
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            
            # Adicionar novos indicadores
            df['atr'] = self.calculate_atr(df)  # Volatilidade
            df['obv'] = self.calculate_obv(df)  # Volume acumulado
            df['momentum'] = self.calculate_momentum(df)  # Momentum
            df['vwap'] = self.calculate_vwap(df)  # Volume-Weighted Average Price
            
            return df
            
        except Exception as e:
            print(f"Erro ao adicionar indicadores: {e}")
            return df

    def get_signals(self, df):
        """Retorna lista de sinais baseados nos indicadores"""
        signals = []
        
        try:
            last_row = df.iloc[-1]
            
            # Tendência
            if last_row['ema_20'] > last_row['ema_50']:
                signals.append('TENDENCIA_ALTA')
            elif last_row['ema_20'] < last_row['ema_50']:
                signals.append('TENDENCIA_BAIXA')
                
            # MACD
            if last_row['macd'] > last_row['signal']:
                signals.append('MACD_POSITIVO')
            else:
                signals.append('MACD_NEGATIVO')
                
            # RSI
            if last_row['rsi'] > 70:
                signals.append('RSI_SOBRECOMPRA')
            elif last_row['rsi'] < 30:
                signals.append('RSI_SOBREVENDA')
                
            # Bollinger Bands
            if last_row['close'] > last_row['bb_upper']:
                signals.append('BB_ALTO')
            elif last_row['close'] < last_row['bb_lower']:
                signals.append('BB_BAIXO')
                
            # Volume
            if last_row['volume'] > last_row['volume_sma'] * 1.5:
                signals.append('VOLUME_ALTO')
                
        except Exception as e:
            print(f"Erro ao gerar sinais: {e}")
            
        return signals

    def generate_signals(self, df):
        """Gera sinais mais robustos"""
        signals = []
        
        # Análise Multi-timeframe
        timeframes = ['1m', '5m', '15m', '1h']
        confirmations = 0
        
        for tf in timeframes:
            tf_data = self.resample_data(df, tf)
            if self.check_trend(tf_data) == 'BAIXA':
                confirmations += 1
                
        # Só considera tendência com confirmação em múltiplos timeframes
        if confirmations >= 3:
            signals.append('TENDENCIA_CONFIRMADA')

    def generate_advanced_signals(self, df):
        """Gera sinais mais robustos com confirmações múltiplas"""
        signals = []
        
        # Análise Multi-timeframe
        timeframes = ['1m', '5m', '15m', '1h']
        trend_confirmations = 0
        
        for tf in timeframes:
            tf_data = self.resample_data(df, tf)
            
            # Confirma tendência em múltiplos timeframes
            if self.confirm_trend_direction(tf_data):
                trend_confirmations += 1
                
            # Analisa padrões de preço
            if self.identify_price_patterns(tf_data):
                signals.append('PRICE_PATTERN')
                
            # Volume anormal
            if self.check_volume_anomaly(tf_data):
                signals.append('VOLUME_ANOMALY')
        
        # Adiciona sinais apenas com confirmação múltipla
        if trend_confirmations >= 3:
            signals.append('TREND_CONFIRMED')
        
        return signals