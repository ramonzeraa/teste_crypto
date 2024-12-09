"""
Testes para CryptoBot
"""
import unittest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime
from src.core.crypto_bot import CryptoTradingBot

class TestCryptoBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup inicial"""
        cls.test_data = pd.DataFrame({
            'open': [1,2,3],
            'high': [2,3,4],
            'low': [0.5,1,2],
            'close': [1.5,2.5,3.5],
            'volume': [100,200,300]
        })
    
    def setUp(self):
        """Setup para cada teste"""
        # Mock todas as dependências
        with patch('src.core.crypto_bot.DataLoader'), \
             patch('src.core.crypto_bot.MarketAnalysis'), \
             patch('src.core.crypto_bot.NotificationSystem'), \
             patch('src.core.crypto_bot.TradingLogger'):
            self.bot = CryptoTradingBot()
            
            # Configura mocks
            self.bot.data_loader.get_latest_data.return_value = self.test_data
            self.bot.market_analysis.analyze.return_value = {
                'signal': 'BUY',
                'indicators': {'rsi': 30},
                'patterns': {'trend': 'UPTREND'},
                'confidence': 0.85
            }
    
    def test_initialization(self):
        """Testa inicialização do bot"""
        self.assertIsNotNone(self.bot)
        self.assertFalse(self.bot.is_running)
        self.assertIsNone(self.bot.current_position)
    
    def test_start_stop(self):
        """Testa início e parada do bot"""
        self.bot.start()
        self.assertTrue(self.bot.is_running)
        
        self.bot.stop()
        self.assertFalse(self.bot.is_running)
    
    def test_update(self):
        """Testa atualização do bot"""
        self.bot.start()
        self.bot.update()
        
        self.bot.data_loader.get_latest_data.assert_called_once()
        self.bot.market_analysis.analyze.assert_called_once()
        self.assertIsNotNone(self.bot.last_update)
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        self.bot.data_loader.get_latest_data.side_effect = Exception("Teste erro")
        
        with self.assertRaises(Exception):
            self.bot.update()
            
        self.bot.logger.log_error.assert_called_once()
    
    def tearDown(self):
        """Limpeza após cada teste"""
        self.bot.stop()
        # Fecha todos os mocks
        self.bot.logger.close()

if __name__ == '__main__':
    unittest.main() 