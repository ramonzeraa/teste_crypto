"""
Testes Unitários para NotificationSystem
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from src.utils.notifications import NotificationSystem

class TestNotificationSystem(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        self.notifier = NotificationSystem()
        
    @patch('twilio.rest.Client')
    def test_whatsapp_notification(self, mock_twilio):
        """Testa envio de notificação WhatsApp"""
        # Configura mock
        mock_message = Mock()
        mock_message.status = 'sent'
        mock_twilio.return_value.messages.create.return_value = mock_message
        
        # Testa envio
        self.notifier.send_whatsapp(
            message="Teste de notificação",
            priority="normal"
        )
        
        # Verifica se foi chamado
        mock_twilio.return_value.messages.create.assert_called_once()
        
        # Verifica histórico
        self.assertEqual(len(self.notifier.notification_history), 1)
        self.assertEqual(
            self.notifier.notification_history[0]['type'],
            'whatsapp'
        ) 
        
    @patch('twilio.rest.Client')
    def test_trade_notification(self, mock_twilio):
        """Testa notificação de trade"""
        # Dados de teste
        trade_data = {
            'type': 'ENTRY',
            'symbol': 'BTCUSDT',
            'price': 50000,
            'stop_loss': 49000,
            'take_profit': 52000
        }
        
        # Testa notificação
        self.notifier.send_trade_notification(trade_data)
        
        # Verifica formatação
        mock_twilio.return_value.messages.create.assert_called_once()
        args = mock_twilio.return_value.messages.create.call_args[1]
        self.assertIn('NOVA POSIÇÃO', args['body'])
        self.assertIn('BTCUSDT', args['body'])
    
    @patch('twilio.rest.Client')
    def test_priority_levels(self, mock_twilio):
        """Testa níveis de prioridade"""
        # Testa alta prioridade
        self.notifier.send_whatsapp("Teste urgente", priority="high")
        args = mock_twilio.return_value.messages.create.call_args[1]
        self.assertIn('🚨 URGENTE', args['body'])
        
        # Testa média prioridade
        self.notifier.send_whatsapp("Teste alerta", priority="medium")
        args = mock_twilio.return_value.messages.create.call_args[1]
        self.assertIn('⚠️ ALERTA', args['body'])
        
        # Testa prioridade normal
        self.notifier.send_whatsapp("Teste info", priority="normal")
        args = mock_twilio.return_value.messages.create.call_args[1]
        self.assertIn('ℹ️ INFO', args['body'])
    
    def test_notification_history(self):
        """Testa histórico de notificações"""
        # Simula algumas notificações
        with patch('twilio.rest.Client'):
            self.notifier.send_whatsapp("Teste 1", "normal")
            self.notifier.send_whatsapp("Teste 2", "high")
            self.notifier.send_whatsapp("Teste 3", "medium")
        
        # Verifica histórico
        history = self.notifier.get_notification_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[-1]['message'], "Teste 3")
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Simula erro no Twilio
        with patch('twilio.rest.Client') as mock_twilio:
            mock_twilio.return_value.messages.create.side_effect = Exception("Erro Twilio")
            
            # Verifica se exceção é lançada
            with self.assertRaises(Exception):
                self.notifier.send_whatsapp("Teste erro")
    
    @patch('twilio.rest.Client')
    def test_alert_formatting(self, mock_twilio):
        """Testa formatação de alertas"""
        # Testa alerta geral
        self.notifier.send_alert(
            title="Teste de Alerta",
            message="Mensagem de teste",
            priority="medium"
        )
        
        # Verifica formatação
        args = mock_twilio.return_value.messages.create.call_args[1]
        self.assertIn('Teste de Alerta', args['body'])
        self.assertIn('Mensagem de teste', args['body'])
        self.assertIn('Hora:', args['body'])
    
    def test_history_limit(self):
        """Testa limite do histórico"""
        # Simula 150 notificações
        with patch('twilio.rest.Client'):
            for i in range(150):
                self.notifier.log_notification({
                    'type': 'test',
                    'message': f'Test {i}',
                    'timestamp': datetime.now()
                })
        
        # Verifica se mantém apenas últimas 100
        history = self.notifier.notification_history
        self.assertLessEqual(len(history), 100)
        self.assertEqual(history[-1]['message'], 'Test 149') 