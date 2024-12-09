"""
Módulo de Notificações
"""
from typing import Dict, Optional, List
from datetime import datetime
import os
from twilio.rest import Client
from ..utils.config import Config

class NotificationSystem:
    def __init__(self):
        self.config = Config()
        self.twilio_client = None
        self.setup_twilio()
        self.notification_history = []
        
    def setup_twilio(self):
        """Configura cliente Twilio"""
        try:
            self.twilio_client = Client(
                self.config.notification_config['twilio_sid'],
                self.config.notification_config['twilio_token']
            )
        except Exception as e:
            raise Exception(f"Erro ao configurar Twilio: {str(e)}")
    
    def send_whatsapp(self, message: str, priority: str = 'normal'):
        """Enviar mensagem via WhatsApp"""
        try:
            # Formata mensagem baseado na prioridade
            if priority == 'high':
                message = f"🚨 URGENTE: {message}"
            elif priority == 'medium':
                message = f"⚠️ ALERTA: {message}"
            else:
                message = f"ℹ️ INFO: {message}"
                
            # Envia mensagem
            response = self.twilio_client.messages.create(
                body=message,
                from_=self.config.notification_config['whatsapp_from'],
                to=self.config.notification_config['whatsapp_to']
            )
            
            # Registra notificação
            self.log_notification({
                'type': 'whatsapp',
                'message': message,
                'priority': priority,
                'status': response.status,
                'timestamp': datetime.now()
            })
            
        except Exception as e:
            raise Exception(f"Erro ao enviar WhatsApp: {str(e)}") 
    
    def send_trade_notification(self, trade_data: Dict):
        """Envia notificação específica de trade"""
        try:
            # Formata mensagem de trade
            message = self._format_trade_message(trade_data)
            
            # Define prioridade baseado no tipo
            priority = 'high' if trade_data.get('type') in ['stop_loss', 'error'] else 'normal'
            
            # Envia notificação
            self.send_whatsapp(message, priority)
            
        except Exception as e:
            raise Exception(f"Erro ao enviar notificação de trade: {str(e)}")
    
    def send_alert(self, title: str, message: str, priority: str = 'medium'):
        """Envia alerta geral"""
        try:
            full_message = f"{title}\n\n{message}\n\nHora: {datetime.now().strftime('%H:%M:%S')}"
            self.send_whatsapp(full_message, priority)
            
        except Exception as e:
            raise Exception(f"Erro ao enviar alerta: {str(e)}")
    
    def log_notification(self, notification_data: Dict):
        """Registra notificação no histórico"""
        try:
            self.notification_history.append(notification_data)
            
            # Mantém apenas últimas 100 notificações
            if len(self.notification_history) > 100:
                self.notification_history = self.notification_history[-100:]
                
        except Exception as e:
            raise Exception(f"Erro ao registrar notificação: {str(e)}")
    
    def _format_trade_message(self, trade_data: Dict) -> str:
        """Formata mensagem de trade"""
        try:
            trade_type = trade_data.get('type', 'unknown').upper()
            symbol = trade_data.get('symbol', 'UNKNOWN')
            price = trade_data.get('price', 0)
            
            if trade_type == 'ENTRY':
                return (
                    f"🟢 NOVA POSIÇÃO\n"
                    f"Par: {symbol}\n"
                    f"Preço: {price}\n"
                    f"Stop Loss: {trade_data.get('stop_loss')}\n"
                    f"Take Profit: {trade_data.get('take_profit')}"
                )
            elif trade_type == 'EXIT':
                return (
                    f"🔵 POSIÇÃO FECHADA\n"
                    f"Par: {symbol}\n"
                    f"Preço: {price}\n"
                    f"P&L: {trade_data.get('pnl', 0):.2f}"
                )
            elif trade_type == 'STOP_LOSS':
                return (
                    f"🔴 STOP LOSS\n"
                    f"Par: {symbol}\n"
                    f"Preço: {price}\n"
                    f"Perda: {trade_data.get('pnl', 0):.2f}"
                )
            else:
                return f"Trade Alert: {trade_data}"
                
        except Exception as e:
            raise Exception(f"Erro ao formatar mensagem: {str(e)}")
    
    def get_notification_history(self, limit: int = 10) -> List[Dict]:
        """Retorna histórico de notificações"""
        return self.notification_history[-limit:]