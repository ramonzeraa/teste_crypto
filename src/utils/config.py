import os
from typing import Dict, Any
import yaml
import json
from dotenv import load_dotenv
import logging
from pathlib import Path

class Config:
    def __init__(self, config_path: str = "config/config.yaml"):
        # Carrega variáveis de ambiente
        load_dotenv()
        
        # Configurações padrão
        self.default_config = {
            'trading': {
                'symbol': 'BTCUSDT',
                'timeframe': '1h',
                'max_positions': 3,
                'position_size': 0.01,
                'use_leverage': False,
                'max_leverage': 1
            },
            'risk': {
                'max_daily_loss': -0.03,
                'max_position_size': 0.05,
                'stop_loss': 0.02,
                'take_profit': 0.03
            },
            'analysis': {
                'indicators': {
                    'rsi_period': 14,
                    'macd_fast': 12,
                    'macd_slow': 26,
                    'macd_signal': 9,
                    'bb_period': 20,
                    'bb_std': 2
                },
                'ml': {
                    'confidence_threshold': 0.8,
                    'training_period': 60,
                    'retraining_interval': 24
                }
            },
            'monitoring': {
                'alert_interval': 3600,
                'report_interval': 86400,
                'metrics_history_size': 1000
            }
        }
        
        # Carrega configurações do arquivo
        self.config_path = config_path
        self.config = self._load_config()
        
        # Credenciais
        self.binance_api_key = os.getenv('BINANCE_API_KEY')
        self.binance_api_secret = os.getenv('BINANCE_API_SECRET')
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_from = os.getenv('WHATSAPP_FROM')
        self.whatsapp_to = os.getenv('WHATSAPP_TO')
        
    def _load_config(self) -> Dict:
        """Carrega configurações do arquivo YAML"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as file:
                    user_config = yaml.safe_load(file)
                    return self._merge_configs(self.default_config, user_config)
            return self.default_config
            
        except Exception as e:
            logging.error(f"Erro ao carregar configurações: {e}")
            return self.default_config
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Mescla configurações padrão com as do usuário"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged
    
    def save_config(self):
        """Salva configurações atuais no arquivo"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file)
                
        except Exception as e:
            logging.error(f"Erro ao salvar configurações: {e}")
    
    def update_config(self, updates: Dict):
        """Atualiza configurações"""
        try:
            self.config = self._merge_configs(self.config, updates)
            self.save_config()
            
        except Exception as e:
            logging.error(f"Erro ao atualizar configurações: {e}")