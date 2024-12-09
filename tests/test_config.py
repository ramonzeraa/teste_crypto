"""
Testes Unitários para Config
"""
import unittest
from unittest.mock import patch
import os
from datetime import datetime
from pathlib import Path
from src.utils.config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        self.config = Config()
        
    def test_initialization(self):
        """Testa inicialização das configurações"""
        # Verifica configurações da API
        self.assertIn('api_key', self.config.api_config)
        self.assertIn('api_secret', self.config.api_config)
        
        # Verifica configurações de trading
        self.assertIn('symbol', self.config.trading_config)
        self.assertIn('position_size', self.config.trading_config)
        self.assertIn('stop_loss', self.config.trading_config)
        
        # Verifica configurações do sistema
        self.assertIn('debug_mode', self.config.system_config)
        self.assertIn('log_level', self.config.system_config)
    
    def test_config_validation(self):
        """Testa validação de configurações"""
        # Testa configuração válida
        self.assertTrue(self.config.validate_config())
        
        # Testa configuração inválida
        self.config.trading_config['position_size'] = 2.0  # Valor inválido
        with self.assertRaises(Exception):
            self.config.validate_config()
    
    def test_config_update(self):
        """Testa atualização de configurações"""
        updates = {
            'symbol': 'ETHUSDT',
            'timeframe': '4h',
            'position_size': 0.05
        }
        
        # Atualiza configurações
        self.config.update_config('trading', updates)
        
        # Verifica atualizações
        self.assertEqual(self.config.trading_config['symbol'], 'ETHUSDT')
        self.assertEqual(self.config.trading_config['timeframe'], '4h')
        self.assertEqual(self.config.trading_config['position_size'], 0.05) 