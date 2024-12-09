import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice

class TechnicalIndicators:
    def __init__(self):
        """Inicializa classe de indicadores técnicos"""
        pass
        
    def add_all_indicators(self, df):
        """Adiciona apenas os indicadores necessários"""
        try:
            # MACD - Corretamente calculado
            macd = MACD(
                close=df['close'],
                window_slow=26,
                window_fast=12,
                window_sign=9
            )
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_hist'] = macd.macd_diff()
            
            # RSI - Período padrão
            rsi = RSIIndicator(
                close=df['close'],
                window=14
            )
            df['rsi'] = rsi.rsi()
            
            # Bollinger Bands
            bb = BollingerBands(
                close=df['close'],
                window=20,
                window_dev=2
            )
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            
            # Médias Móveis
            df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
            df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
            df['ema_9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
            
            # VWAP
            df['vwap'] = VolumeWeightedAveragePrice(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                volume=df['volume']
            ).volume_weighted_average_price()
            
            return df.dropna()  # Remove NaN values
            
        except Exception as e:
            print(f"Erro ao adicionar indicadores: {e}")
            return df