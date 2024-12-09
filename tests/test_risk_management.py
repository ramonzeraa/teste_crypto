"""
Testes Unitários para RiskManagement
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from src.trading.risk_management import RiskManagement

class TestRiskManagement(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        self.risk_manager = RiskManagement()
        
        # Posição de teste
        self.test_position = {
            'side': 'BUY',
            'entry_price': 50000,
            'size': 0.1,
            'timestamp': datetime.now(),
            'stop_loss': 49000,
            'take_profit': 52000
        }
    
    def test_position_size_calculation(self):
        """Testa cálculo de tamanho da posição"""
        capital = 100000  # $100k
        price = 50000     # $50k
        
        position_size = self.risk_manager.calculate_position_size(capital, price)
        
        # Verifica se tamanho está dentro do limite de risco (2%)
        max_risk = capital * self.risk_manager.config['max_position_size']
        self.assertLessEqual(position_size * price, max_risk)
    
    def test_stop_loss_calculation(self):
        """Testa cálculo de stop loss"""
        entry_price = 50000
        
        # Testa long
        sl_long = self.risk_manager.calculate_stop_loss('BUY', entry_price)
        self.assertLess(sl_long, entry_price)
        
        # Testa short
        sl_short = self.risk_manager.calculate_stop_loss('SELL', entry_price)
        self.assertGreater(sl_short, entry_price) 
    
    def test_take_profit_calculation(self):
        """Testa cálculo de take profit"""
        entry_price = 50000
        
        # Testa long
        tp_long = self.risk_manager.calculate_take_profit('BUY', entry_price)
        self.assertGreater(tp_long, entry_price)
        
        # Testa short
        tp_short = self.risk_manager.calculate_take_profit('SELL', entry_price)
        self.assertLess(tp_short, entry_price)
    
    def test_risk_levels(self):
        """Testa verificação de níveis de risco"""
        risk_status = self.risk_manager.check_risk_levels()
        
        # Verifica estrutura
        self.assertIn('can_trade', risk_status)
        self.assertIn('reasons', risk_status)
        self.assertIn('daily_stats', risk_status)
        
        # Testa limite de trades
        self.risk_manager.daily_stats['trades_count'] = \
            self.risk_manager.config['max_trades_day']
        risk_status = self.risk_manager.check_risk_levels()
        self.assertFalse(risk_status['can_trade'])
    
    def test_position_monitoring(self):
        """Testa monitoramento de posição"""
        # Testa Stop Loss
        position = self.test_position.copy()
        position['current_price'] = position['stop_loss'] - 100
        
        check = self.risk_manager.check_position(position)
        self.assertTrue(check['should_close'])
        self.assertEqual(check['reason'], "Stop Loss atingido")
        
        # Testa Take Profit
        position['current_price'] = position['take_profit'] + 100
        check = self.risk_manager.check_position(position)
        self.assertTrue(check['should_close'])
        self.assertEqual(check['reason'], "Take Profit atingido")
    
    def test_daily_reset(self):
        """Testa reset diário de estatísticas"""
        # Simula dados antigos
        old_stats = {
            'trades_count': 5,
            'daily_pnl': 1000,
            'last_reset': datetime.now()
        }
        self.risk_manager.daily_stats = old_stats
        
        # Força reset
        self.risk_manager._check_daily_reset()
        
        # Verifica se manteve os dados (mesmo dia)
        self.assertEqual(self.risk_manager.daily_stats['trades_count'], 5)
        
        # Simula dia seguinte
        from datetime import timedelta
        self.risk_manager.daily_stats['last_reset'] -= timedelta(days=1)
        self.risk_manager._check_daily_reset()
        
        # Verifica reset
        self.assertEqual(self.risk_manager.daily_stats['trades_count'], 0)
        self.assertEqual(self.risk_manager.daily_stats['daily_pnl'], 0.0)
    
    def test_update_stats(self):
        """Testa atualização de estatísticas"""
        trade_result = {
            'type': 'EXIT',
            'pnl': 500,
            'side': 'BUY',
            'entry_price': 50000,
            'exit_price': 51000
        }
        
        initial_trades = self.risk_manager.daily_stats['trades_count']
        initial_pnl = self.risk_manager.daily_stats['daily_pnl']
        
        self.risk_manager.update_stats(trade_result)
        
        # Verifica atualização
        self.assertEqual(
            self.risk_manager.daily_stats['trades_count'],
            initial_trades + 1
        )
        self.assertEqual(
            self.risk_manager.daily_stats['daily_pnl'],
            initial_pnl + trade_result['pnl']
        )
    
    def test_system_health(self):
        """Testa verificação de saúde do sistema"""
        # Sistema saudável
        self.assertTrue(self.risk_manager.is_healthy())
        
        # Simula perda máxima
        self.risk_manager.daily_stats['daily_pnl'] = \
            -self.risk_manager.config['max_daily_loss'] * 100000
        self.assertFalse(self.risk_manager.is_healthy())