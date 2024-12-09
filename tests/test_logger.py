"""
Testes para Logger
"""
import unittest
from unittest.mock import patch
import os
from pathlib import Path
from src.utils.logger import TradingLogger

class TestTradingLogger(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        # Usa diretório de teste
        self.test_log_dir = Path('test_logs')
        with patch('src.utils.logger.Path') as mock_path:
            mock_path.return_value = self.test_log_dir
            self.logger = TradingLogger()
    
    def test_log_initialization(self):
        """Testa inicialização do logger"""
        self.assertIsNotNone(self.logger.logger)
        self.assertEqual(self.logger.logger.name, 'TradingBot')
    
    def test_log_trade(self):
        """Testa logging de trade"""
        trade_data = {
            'type': 'ENTRY',
            'symbol': 'BTCUSDT',
            'price': 50000
        }
        self.logger.log_trade(trade_data)
        
        # Verifica se arquivo existe
        log_files = list(self.test_log_dir.glob('*.log'))
        self.assertTrue(len(log_files) > 0)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        # Fecha handlers
        if hasattr(self, 'logger'):
            for handler in self.logger.logger.handlers[:]:
                handler.close()
                self.logger.logger.removeHandler(handler)
        
        # Remove diretório de teste
        if self.test_log_dir.exists():
            for file in self.test_log_dir.glob('*'):
                try:
                    file.unlink()
                except PermissionError:
                    pass
            try:
                self.test_log_dir.rmdir()
            except PermissionError:
                pass 