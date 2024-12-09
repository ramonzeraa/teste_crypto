"""
Módulo de Carregamento de Dados
"""
from typing import Dict, List, Optional
import pandas as pd
from binance.client import Client
from datetime import datetime, timedelta
import os

class DataLoader:
    def __init__(self):
        self.client = None
        self.connected = False
        self.last_update = None
        self.cache = {}
        
    def connect(self, BINANCE_API_KEY: str, BINANCE_API_SECRET: str):
        """Conecta com a API da Binance"""
        try:
            self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
            self.connected = True
            self.last_update = datetime.now()
            
        except Exception as e:
            raise Exception(f"Erro ao conectar com Binance: {str(e)}")
    
    def get_latest_data(self, symbol: str = 'BTCUSDT', 
                       interval: str = '1h',
                       limit: int = 100) -> pd.DataFrame:
        """Obtém dados mais recentes do mercado"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 
                'volume', 'close_time', 'quote_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            # Processamento dos dados
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            df.set_index('timestamp', inplace=True)
            
            # Atualiza cache
            cache_key = f"{symbol}_{interval}"
            self.cache[cache_key] = {
                'data': df,
                'last_update': datetime.now()
            }
            
            return df
            
        except Exception as e:
            raise Exception(f"Erro ao obter dados: {str(e)}")
    def get_historical_data(self, symbol: str = 'BTCUSDT',
                          interval: str = '1h',
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Obtém dados históricos do mercado"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
                
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=str(int(start_date.timestamp() * 1000)),
                end_str=str(int(end_date.timestamp() * 1000))
            )
            
            return self._process_klines(klines)
            
        except Exception as e:
            raise Exception(f"Erro ao obter dados históricos: {str(e)}")
    
    def check_connection(self) -> bool:
        """Verifica status da conexão"""
        try:
            if not self.connected or not self.client:
                return False
                
            # Testa conexão
            self.client.get_system_status()
            return True
            
        except Exception:
            self.connected = False
            return False
    
    def get_account_balance(self, asset: str = 'USDT') -> float:
        """Obtém saldo da conta"""
        try:
            balance = self.client.get_asset_balance(asset=asset)
            return float(balance['free'])
            
        except Exception as e:
            raise Exception(f"Erro ao obter saldo: {str(e)}")
    
    def _process_klines(self, klines: List) -> pd.DataFrame:
        """Processa dados de klines"""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 
            'volume', 'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        # Processamento
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        df.set_index('timestamp', inplace=True)
        return df
    
    def send_notification(self, message: str):
        """Envia notificação via WhatsApp usando Twilio"""
        try:
            from twilio.rest import Client
            
            twilio_client = Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            
            twilio_client.messages.create(
                body=message,
                from_=os.getenv('WHATSAPP_FROM'),
                to=os.getenv('WHATSAPP_TO')
            )
            
        except Exception as e:
            raise Exception(f"Erro ao enviar notificação: {str(e)}")