"""
Testes Unitários para TradingLogger
"""
import unittest
from unittest.mock import Mock, patch
import os
from pathlib import Path
from datetime import datetime
from src.utils.logger import TradingLogger

class TestTradingLogger(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        self.logger = TradingLogger()
        self.test_log_dir = Path('test_logs')
        
    def test_log_initialization(self):
        """Testa inicialização do logger"""
        # Verifica se logger foi configurado
        self.assertIsNotNone(self.logger.logger)
        self.assertEqual(self.logger.logger.name, 'TradingBot')
        
        # Verifica handlers
        handlers = self.logger.logger.handlers
        self.assertTrue(any(h.__class__.__name__ == 'FileHandler' 
                          for h in handlers))
        self.assertTrue(any(h.__class__.__name__ == 'StreamHandler' 
                          for h in handlers)) 
    
    def test_trade_logging(self):
        """Testa logging de trades"""
        trade_data = {
            'type': 'ENTRY',
            'symbol': 'BTCUSDT',
            'price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000,
            'pnl': 0
        }
        
        # Testa log de trade
        self.logger.log_trade(trade_data)
        
        # Verifica arquivo de trades
        trade_log_path = Path('logs/trades') / f"trades_{datetime.now().strftime('%Y%m')}.log"
        self.assertTrue(trade_log_path.exists())
        
        # Verifica conteúdo
        with open(trade_log_path, 'r') as f:
            content = f.read()
            self.assertIn('BTCUSDT', content)
            self.assertIn('50000', content)
    
    def test_error_logging(self):
        """Testa logging de erros"""
        test_error = Exception("Teste de erro")
        test_context = "Contexto do erro"
        
        # Log do erro
        self.logger.log_error(test_error, test_context)
        
        # Verifica arquivo de log
        log_file = Path('logs') / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn('ERROR', content)
            self.assertIn('Teste de erro', content)
            self.assertIn('Contexto do erro', content)
    
    def test_strategy_logging(self):
        """Testa logging de estratégia"""
        strategy_data = {
            'signal': 'BUY',
            'indicators': {
                'rsi': 30,
                'macd': 'positive'
            },
            'confidence': 0.85
        }
        
        # Log da estratégia
        self.logger.log_strategy(strategy_data)
        
        # Verifica log
        log_file = Path('logs') / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn('STRATEGY', content)
            self.assertIn('BUY', content)
    
    def test_log_rotation(self):
        """Testa rotação de logs"""
        # Cria alguns logs antigos
        old_log_dir = Path('logs')
        old_log_dir.mkdir(exist_ok=True)
        
        old_dates = ['20230101', '20230102', '20230103']
        for date in old_dates:
            (old_log_dir / f'trading_{date}.log').touch()
        
        # Executa rotação
        self.logger.rotate_logs(max_days=30)
        
        # Verifica se logs antigos foram removidos
        current_logs = list(old_log_dir.glob('*.log'))
        self.assertLess(len(current_logs), len(old_dates) + 1)
    
    def test_trade_details_logging(self):
        """Testa logging detalhado de trades"""
        trade_data = {
            'type': 'EXIT',
            'symbol': 'BTCUSDT',
            'price': 51000,
            'size': 0.1,
            'pnl': 500,
            'strategy': 'RSI_MACD'
        }
        
        # Log detalhado
        self.logger._log_trade_details(trade_data)
        
        # Verifica arquivo específico
        trade_log = Path('logs/trades') / f"trades_{datetime.now().strftime('%Y%m')}.log"
        with open(trade_log, 'r') as f:
            content = f.read()
            self.assertIn('Type: EXIT', content)
            self.assertIn('PnL: 500', content)
            self.assertIn('Strategy: RSI_MACD', content)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        # Remove arquivos de teste
        import shutil
        if Path('logs').exists():
            shutil.rmtree('logs')
        if self.test_log_dir.exists():
            shutil.rmtree(self.test_log_dir) 