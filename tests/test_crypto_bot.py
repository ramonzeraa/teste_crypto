"""
Testes Unitários para CryptoBot
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from src.core.crypto_bot import CryptoBot

class TestCryptoBot(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        self.bot = CryptoBot()
        
    def test_initialization(self):
        """Testa inicialização do bot"""
        self.assertFalse(self.bot.is_active)
        self.assertIsNone(self.bot.current_position)
        self.assertIsNone(self.bot.last_analysis)
        
    @patch('src.core.crypto_bot.DataLoader')
    def test_start_bot(self, mock_loader):
        """Testa início do bot"""
        # Configura mock
        mock_loader.return_value.check_connection.return_value = True
        
        # Testa início
        self.bot.start()
        self.assertTrue(self.bot.is_active)
        
    def test_risk_validation(self):
        """Testa validação de risco"""
        # Simula posição
        self.bot.current_position = {
            'side': 'BUY',
            'entry_price': 50000,
            'size': 0.1,
            'stop_loss': 49000,
            'take_profit': 52000
        }
        
        # Testa validação
        result = self.bot.validate_state()
        self.assertTrue(result) 
        
    def test_position_management(self):
        """Testa gestão de posições"""
        # Testa abertura de posição
        self.bot.open_position('BUY', 50000)
        self.assertIsNotNone(self.bot.current_position)
        self.assertEqual(self.bot.current_position['side'], 'BUY')
        
        # Testa fechamento de posição
        result = self.bot.close_position(51000)
        self.assertIsNone(self.bot.current_position)
        self.assertGreater(result['pnl'], 0)
        
    @patch('src.core.crypto_bot.MarketAnalysis')
    def test_strategy_execution(self, mock_analysis):
        """Testa execução de estratégia"""
        # Configura mock de análise
        mock_analysis.return_value.analyze.return_value = {
            'signal': 'BUY',
            'price': 50000,
            'confidence': 0.8
        }
        
        # Executa estratégia
        self.bot.execute_strategy(mock_analysis.return_value.analyze())
        self.assertIsNotNone(self.bot.current_position)
        
    def test_risk_management(self):
        """Testa gestão de risco"""
        # Simula posição com stop loss
        self.bot.open_position('BUY', 50000)
        self.bot.current_position['stop_loss'] = 49000
        
        # Testa stop loss
        self.bot.monitor_positions()
        self.assertTrue(self.bot.risk_manager.check_position(
            self.bot.current_position
        )['should_close'])
        
    @patch('src.core.crypto_bot.DataLoader')
    def test_market_data(self, mock_loader):
        """Testa atualização de dados de mercado"""
        import pandas as pd
        
        # Mock de dados de mercado
        mock_data = pd.DataFrame({
            'open': [49000, 50000],
            'high': [51000, 52000],
            'low': [48000, 49000],
            'close': [50000, 51000],
            'volume': [100, 200]
        })
        mock_loader.return_value.get_latest_data.return_value = mock_data
        
        # Testa atualização
        self.bot.data_loader = mock_loader.return_value
        data = self.bot.data_loader.get_latest_data()
        self.assertIsNotNone(data)
        self.assertEqual(len(data), 2)
        
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Força erro na análise
        with patch('src.core.crypto_bot.MarketAnalysis') as mock_analysis:
            mock_analysis.return_value.analyze.side_effect = Exception("Erro de teste")
            
            # Verifica se bot para em caso de erro
            self.bot.start()
            self.assertFalse(self.bot.is_active)
            
    def test_bot_status(self):
        """Testa status do bot"""
        # Configura estado
        self.bot.is_active = True
        self.bot.open_position('BUY', 50000)
        
        # Verifica status
        status = self.bot.get_bot_status()
        self.assertTrue(status['is_active'])
        self.assertIsNotNone(status['current_position']) 
    
    def test_config_validation(self):
        """Testa validação de configurações"""
        with patch('src.core.crypto_bot.Config') as mock_config:
            # Testa configurações válidas
            mock_config.return_value.validate_config.return_value = True
            self.assertTrue(self.bot.validate_state())
            
            # Testa configurações inválidas
            mock_config.return_value.validate_config.return_value = False
            self.assertFalse(self.bot.validate_state())
    
    def test_pnl_calculation(self):
        """Testa cálculo de P&L"""
        # Teste posição long
        self.bot.open_position('BUY', 50000)
        pnl_long = self.bot.calculate_pnl(51000)
        self.assertGreater(pnl_long, 0)
        
        # Teste posição short
        self.bot.open_position('SELL', 50000)
        pnl_short = self.bot.calculate_pnl(49000)
        self.assertGreater(pnl_short, 0)
    
    def test_notification_system(self):
        """Testa sistema de notificações"""
        with patch('src.utils.notifications.NotificationSystem') as mock_notif:
            # Simula trade para notificação
            self.bot.open_position('BUY', 50000)
            mock_notif.return_value.send_trade_notification.assert_called_once()
    
    def test_logging_system(self):
        """Testa sistema de logging"""
        with patch('src.utils.logger.TradingLogger') as mock_logger:
            # Simula operação para log
            self.bot.start()
            mock_logger.return_value.log_trade.assert_called()
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        import shutil
        import os
        
        # Limpa arquivos de teste
        if os.path.exists('logs'):
            shutil.rmtree('logs')
        if os.path.exists('data'):
            shutil.rmtree('data')

if __name__ == '__main__':
    unittest.main() 