"""
Testes para NotificationSystem
"""
import unittest
from unittest.mock import patch, MagicMock
from src.utils.notifications import NotificationSystem

class TestNotificationSystem(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        with patch('src.utils.notifications.Client'):
            self.notifier = NotificationSystem()
    
    def test_notification_sending(self):
        """Testa envio de notificação"""
        with patch('twilio.rest.Client') as mock_twilio:
            mock_messages = MagicMock()
            mock_twilio.return_value.messages = mock_messages
            
            self.notifier.send_notification(
                title="Teste",
                message="Mensagem de teste",
                priority="normal"
            )
            
            mock_messages.create.assert_called_once()
            
    def test_notification_history(self):
        """Testa histórico de notificações"""
        self.notifier.send_notification("Teste 1", "Mensagem 1")
        self.notifier.send_notification("Teste 2", "Mensagem 2")
        
        self.assertEqual(len(self.notifier.history), 2)
        self.assertEqual(
            self.notifier.history[-1]['title'],
            "Teste 2"
        ) 