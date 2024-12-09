"""
Testes para MarketAnalysis
"""
import unittest
import pandas as pd
import numpy as np
from src.analysis.market_analysis import MarketAnalysis

class TestMarketAnalysis(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        self.test_data = pd.DataFrame({
            'open': [100] * 50,
            'high': [110] * 50,
            'low': [90] * 50,
            'close': [105] * 50,
            'volume': [1000] * 50
        })
        
        self.analysis = MarketAnalysis()
        self.analysis.calculate_indicators(self.test_data)
        
    def test_indicator_calculation(self):
        """Testa cálculo de indicadores"""
        indicators = self.analysis.indicators
        
        self.assertIn('sma_20', indicators)
        self.assertIn('rsi', indicators)
        self.assertIsInstance(indicators['sma_20'], pd.Series)
        
    def test_signal_generation(self):
        """Testa geração de sinais"""
        signal = self.analysis.generate_signals()
        
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
        self.assertIsInstance(self.analysis.patterns, dict)