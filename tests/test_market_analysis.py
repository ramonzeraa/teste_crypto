"""
Testes Unitários para MarketAnalysis
"""
import unittest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime
from src.analysis.market_analysis import MarketAnalysis

class TestMarketAnalysis(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        self.analysis = MarketAnalysis()
        
        # Cria dados de teste
        self.test_data = pd.DataFrame({
            'open': [45000, 46000, 47000, 48000, 49000],
            'high': [46000, 47000, 48000, 49000, 50000],
            'low': [44000, 45000, 46000, 47000, 48000],
            'close': [45500, 46500, 47500, 48500, 49500],
            'volume': [100, 150, 200, 250, 300]
        })
        
    def test_indicator_calculation(self):
        """Testa cálculo de indicadores"""
        # Calcula indicadores
        self.analysis.data = self.test_data
        self.analysis.calculate_indicators()
        
        # Verifica SMA
        self.assertIn('sma_20', self.analysis.indicators)
        self.assertIn('sma_50', self.analysis.indicators)
        
        # Verifica RSI
        self.assertIn('rsi', self.analysis.indicators)
        
        # Verifica MACD
        macd_data = self.analysis.calculate_macd()
        self.assertIn('macd', macd_data)
        self.assertIn('signal', macd_data)
    
    def test_pattern_identification(self):
        """Testa identificação de padrões"""
        self.analysis.data = self.test_data
        self.analysis.identify_patterns()
        
        # Verifica tendência
        self.assertIn('trend', self.analysis.patterns)
        
        # Verifica suporte/resistência
        levels = self.analysis.find_support_resistance()
        self.assertIn('support', levels)
        self.assertIn('resistance', levels) 
    
    def test_signal_generation(self):
        """Testa geração de sinais"""
        self.analysis.data = self.test_data
        self.analysis.calculate_indicators()
        
        # Gera sinais
        signal = self.analysis.generate_signals()
        
        # Verifica formato do sinal
        self.assertIn(signal, ['BUY', 'SELL', 'NEUTRAL'])
        
        # Verifica consistência
        self.assertIsNotNone(self.analysis.last_analysis)
        self.assertEqual(self.analysis.last_analysis['signal'], signal)
    
    def test_bollinger_bands(self):
        """Testa cálculo das Bollinger Bands"""
        self.analysis.data = self.test_data
        bb_data = self.analysis.calculate_bollinger_bands()
        
        # Verifica componentes
        self.assertIn('upper', bb_data)
        self.assertIn('middle', bb_data)
        self.assertIn('lower', bb_data)
        
        # Verifica lógica
        self.assertTrue(all(bb_data['upper'] > bb_data['middle']))
        self.assertTrue(all(bb_data['middle'] > bb_data['lower']))
    
    def test_trend_analysis(self):
        """Testa análise de tendência"""
        self.analysis.data = self.test_data
        trend = self.analysis.identify_trend()
        
        # Verifica resultado
        self.assertIn(trend, ['UPTREND', 'DOWNTREND', 'SIDEWAYS'])
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Testa com dados vazios
        with self.assertRaises(Exception):
            self.analysis.analyze(pd.DataFrame())
        
        # Testa com dados inválidos
        with self.assertRaises(Exception):
            self.analysis.analyze(None)
    
    def test_analysis_consistency(self):
        """Testa consistência da análise"""
        # Executa análise completa
        result = self.analysis.analyze(self.test_data)
        
        # Verifica componentes necessários
        self.assertIn('timestamp', result)
        self.assertIn('indicators', result)
        self.assertIn('patterns', result)
        self.assertIn('signal', result)
        self.assertIn('price', result)
        
        # Verifica tipos de dados
        self.assertIsInstance(result['timestamp'], datetime)
        self.assertIsInstance(result['indicators'], dict)
        self.assertIsInstance(result['patterns'], dict)
        self.assertIsInstance(result['signal'], str)
        self.assertIsInstance(result['price'], float)
    
    def test_performance(self):
        """Testa performance da análise"""
        import time
        
        # Cria dataset maior
        large_data = pd.concat([self.test_data] * 100)
        
        # Mede tempo de execução
        start_time = time.time()
        self.analysis.analyze(large_data)
        execution_time = time.time() - start_time
        
        # Verifica se execução é rápida o suficiente
        self.assertLess(execution_time, 1.0)  # deve executar em menos de 1 segundo