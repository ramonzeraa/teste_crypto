"""
Sistema de Notificações
"""
from typing import Dict, Any, List, Optional
import telegram
import logging
from datetime import datetime
import os
from twilio.rest import Client
from .config import Config

class NotificationSystem:
    def __init__(self):
        config = Config()
        self.client = Client(
            config.twilio_account_sid,
            config.twilio_auth_token
        )
        self.whatsapp_from = config.whatsapp_from
        self.whatsapp_to = config.whatsapp_to
        
    def send_alert(self, message: str, priority: str = "normal"):
        try:
            if priority == "high":
                message = "🚨 URGENTE: " + message
            elif priority == "medium":
                message = "⚠️ ALERTA: " + message
                
            self.client.messages.create(
                from_=self.whatsapp_from,
                body=message,
                to=self.whatsapp_to
            )
            logging.info(f"Notificação enviada: {message}")
        except Exception as e:
            logging.error(f"Erro ao enviar notificação: {e}")