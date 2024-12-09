"""
Sistema de Notificações
"""
from typing import Dict, Any, List
from twilio.rest import Client
from datetime import datetime

class NotificationSystem:
    def __init__(self):
        """Inicializa sistema de notificações"""
        self.history = []
        self.twilio_client = None
        self.setup_twilio()
        
    def send_notification(self, title: str, message: str, priority: str = 'normal'):
        """Envia notificação"""
        try:
            formatted_message = self._format_message(title, message, priority)
            
            if self.twilio_client:
                self.twilio_client.messages.create(
                    body=formatted_message,
                    from_=self.whatsapp_from,
                    to=self.whatsapp_to
                )
                
            self.history.append({
                'timestamp': datetime.now(),
                'title': title,
                'message': message,
                'priority': priority
            })
            
        except Exception as e:
            raise Exception(f"Erro ao enviar notificação: {str(e)}")
            
    def _format_message(self, title: str, message: str, priority: str) -> str:
        """Formata mensagem"""
        priority_icons = {
            'high': '🚨',
            'normal': '⚠️',
            'low': 'ℹ️'
        }
        
        icon = priority_icons.get(priority, '⚠️')
        return f"{icon} {title}: {message}"