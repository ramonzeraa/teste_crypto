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