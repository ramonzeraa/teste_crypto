from binance import Client, ThreadedWebsocketManager
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional

class RealTimeCollector:
    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret)
        self.twm = ThreadedWebsocketManager(api_key, api_secret)
        self.current_data: Dict = {
            'price': None,
            'volume': None,
            'trades': [],
            'book': {'bids': [], 'asks': []}
        }
        self.is_collecting = False
        
    def start_collection(self, symbol: str = 'BTCUSDT'):
        """Inicia a coleta de dados em tempo real"""
        try:
            self.is_collecting = True
            self.twm.start()
            
            # Stream de Kline/Candlestick
            self.twm.start_kline_socket(
                callback=self._handle_kline_message,
                symbol=symbol
            )
            
            # Stream do Book de Ofertas
            self.twm.start_depth_socket(
                callback=self._handle_depth_message,
                symbol=symbol
            )
            
            # Stream de Trades
            self.twm.start_trade_socket(
                callback=self._handle_trade_message,
                symbol=symbol
            )
            
            logging.info(f"Coleta de dados iniciada para {symbol}")
            
        except Exception as e:
            logging.error(f"Erro ao iniciar coleta: {e}")
            self.stop_collection()
    
    def _handle_kline_message(self, msg):
        """Processa mensagens de candlestick"""
        try:
            if msg['e'] == 'kline':
                kline = msg['k']
                self.current_data['price'] = float(kline['c'])  # Preço atual
                self.current_data['volume'] = float(kline['v'])  # Volume
                self._log_data_update('kline')
        except Exception as e:
            logging.error(f"Erro ao processar kline: {e}")
    
    def _handle_depth_message(self, msg):
        """Processa mensagens do book de ofertas"""
        try:
            if msg['e'] == 'depthUpdate':
                self.current_data['book']['bids'] = msg['b'][:5]  # Top 5 bids
                self.current_data['book']['asks'] = msg['a'][:5]  # Top 5 asks
                self._log_data_update('depth')
        except Exception as e:
            logging.error(f"Erro ao processar book: {e}")
    
    def _handle_trade_message(self, msg):
        """Processa mensagens de trades"""
        try:
            if msg['e'] == 'trade':
                trade = {
                    'price': float(msg['p']),
                    'quantity': float(msg['q']),
                    'time': datetime.fromtimestamp(msg['T'] / 1000),
                    'buyer_maker': msg['m']
                }
                self.current_data['trades'].append(trade)
                # Mantém apenas os últimos 100 trades
                self.current_data['trades'] = self.current_data['trades'][-100:]
                self._log_data_update('trade')
        except Exception as e:
            logging.error(f"Erro ao processar trade: {e}")
    
    def _log_data_update(self, data_type: str):
        """Registra atualizações de dados"""
        logging.debug(f"Dados atualizados: {data_type} - {datetime.now()}")
    
    def get_current_data(self) -> Dict:
        """Retorna os dados mais recentes"""
        return self.current_data
    
    def stop_collection(self):
        """Para a coleta de dados"""
        self.is_collecting = False
        self.twm.stop()
        logging.info("Coleta de dados finalizada") 