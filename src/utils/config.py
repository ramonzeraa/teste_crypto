"""
Módulo de Configuração do Sistema
"""
from typing import Dict, Any
import os
from datetime import datetime
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Carrega variáveis de ambiente
        load_dotenv()
        
        # Configurações da API
        self.api_config = {
            'api_key': os.getenv('BINANCE_API_KEY'),
            'api_secret': os.getenv('BINANCE_API_SECRET'),
            'twilio_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'twilio_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'whatsapp_to': os.getenv('WHATSAPP_TO'),
            'whatsapp_from': os.getenv('WHATSAPP_FROM')
        }
        
        # Configurações de Trading
        self.trading_config = {
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'strategy': 'default',
            'max_trades': 5,
            'position_size': 0.02,  # 2% do capital
            'stop_loss': 0.02,      # 2% stop loss
            'take_profit': 0.04     # 4% take profit
        }
        
        # Configurações do Sistema
        self.system_config = {
            'debug_mode': False,
            'log_level': 'INFO',
            'data_dir': 'data/',
            'cache_duration': 300,  # 5 minutos
            'retry_attempts': 3
        }
        
        # Adicionando configuração de notificações
        self.notification_config = {
            'twilio_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'twilio_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'whatsapp_from': os.getenv('WHATSAPP_FROM'),
            'whatsapp_to': os.getenv('WHATSAPP_TO')
        }
    
    def validate_config(self) -> bool:
        """Valida todas as configurações necessárias"""
        try:
            # Valida API keys
            if not all([
                self.api_config['api_key'],
                self.api_config['api_secret']
            ]):
                raise ValueError("Credenciais da Binance não configuradas")
                
            # Valida Twilio
            if not all([
                self.api_config['twilio_sid'],
                self.api_config['twilio_token'],
                self.api_config['whatsapp_to'],
                self.api_config['whatsapp_from']
            ]):
                raise ValueError("Credenciais do Twilio não configuradas")
                
            # Valida configurações de trading
            if not all([
                0 < self.trading_config['position_size'] < 1,
                0 < self.trading_config['stop_loss'] < 1,
                0 < self.trading_config['take_profit'] < 1
            ]):
                raise ValueError("Configurações de trading inválidas")
                
            return True
            
        except Exception as e:
            raise Exception(f"Erro na validação de configurações: {str(e)}")
    
    def update_config(self, section: str, updates: Dict[str, Any]):
        """Atualiza configurações específicas"""
        try:
            if section == 'trading':
                self.trading_config.update(updates)
            elif section == 'system':
                self.system_config.update(updates)
            elif section == 'api':
                self.api_config.update(updates)
            else:
                raise ValueError(f"Seção de configuração inválida: {section}")
                
            # Valida após atualização
            self.validate_config()
            
        except Exception as e:
            raise Exception(f"Erro ao atualizar configurações: {str(e)}")
    
    def save_config(self, filepath: str = 'config/settings.json'):
        """Salva configurações em arquivo"""
        try:
            import json
            
            config_data = {
                'trading': self.trading_config,
                'system': self.system_config,
                'last_update': datetime.now().isoformat()
            }
            
            # Não salva dados sensíveis
            safe_api_config = {
                k: v for k, v in self.api_config.items()
                if not any(s in k for s in ['key', 'secret', 'token', 'sid'])
            }
            config_data['api'] = safe_api_config
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=4)
                
        except Exception as e:
            raise Exception(f"Erro ao salvar configurações: {str(e)}")
    
    def load_config(self, filepath: str = 'config/settings.json'):
        """Carrega configurações de arquivo"""
        try:
            import json
            
            if not os.path.exists(filepath):
                return
                
            with open(filepath, 'r') as f:
                config_data = json.load(f)
            
            # Atualiza configurações não sensíveis
            self.trading_config.update(config_data.get('trading', {}))
            self.system_config.update(config_data.get('system', {}))
            
            # Valida após carregamento
            self.validate_config()
            
        except Exception as e:
            raise Exception(f"Erro ao carregar configurações: {str(e)}")
    
    def get_config(self, section: str = None) -> Dict:
        """Retorna configurações atuais"""
        if section == 'trading':
            return self.trading_config.copy()
        elif section == 'system':
            return self.system_config.copy()
        elif section == 'api':
            return {k: '***' if any(s in k for s in ['key', 'secret', 'token', 'sid'])
                   else v for k, v in self.api_config.items()}
        else:
            return {
                'trading': self.trading_config,
                'system': self.system_config,
                'api': self.get_config('api')
            }