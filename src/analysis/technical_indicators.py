"""
Indicadores Técnicos
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

class TechnicalIndicators:
    def __init__(self, data: pd.DataFrame = None):
        self.data = data
        self.indicators = {}
        
    def calculate_all(self, data: pd.DataFrame = None) -> Dict[str, pd.Series]:
        """Calcula todos os indicadores"""
        if data is not None:
            self.data = data
            
        self.indicators = {
            'sma': self.calculate_sma(),
            'ema': self.calculate_ema(),
            'rsi': self.calculate_rsi(),
            'bb': self.calculate_bollinger_bands()
        }
        
        return self.indicators