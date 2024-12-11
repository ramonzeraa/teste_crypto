import websocket
from typing import Callable, Dict, Optional
from datetime import datetime
import json
import numpy as np
import logging
from threading import Thread
import pandas as pd
from binance.client import Client

class BinanceDataLoader:
    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret)
        self.ws_client = None
        self.orderbook_cache = {}
        self.trade_cache = []
        self.callbacks = []
    
    def add_realtime_callback(self, callback: Callable):
        """Adiciona callback para dados em tempo real"""
        self.callbacks.append(callback)
    
    def start_market_stream(self, symbol: str):
        """Inicia stream de mercado"""
        try:
            # Inicia WebSocket
            stream_name = f"{symbol.lower()}@trade/{symbol.lower()}@depth@100ms/{symbol.lower()}@kline_1m"
            self.ws_client = websocket.WebSocketApp(
                f"wss://stream.binance.com:9443/ws/{stream_name}",
                on_message=self._handle_socket_message,
                on_error=self._handle_socket_error,
                on_close=self._handle_socket_close
            )
            
            # Inicia em thread separada
            ws_thread = Thread(target=self.ws_client.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            logging.info(f"Stream iniciado para {symbol}")
            
        except Exception as e:
            logging.error(f"Erro ao iniciar stream: {e}")
    
    def get_market_depth(self, symbol: str) -> Dict:
        """Analisa profundidade do mercado"""
        try:
            depth = self.client.get_order_book(symbol=symbol, limit=100)
            bids = np.array(depth['bids'], dtype=float)
            asks = np.array(depth['asks'], dtype=float)
            
            return {
                'bid_volume': np.sum(bids[:, 1]),
                'ask_volume': np.sum(asks[:, 1]),
                'spread': float(asks[0][0]) - float(bids[0][0]),
                'walls': self._find_order_walls(bids, asks),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logging.error(f"Erro ao analisar profundidade: {e}")
            return {}
    
    def _handle_socket_message(self, ws, message):
        """Processa mensagens do WebSocket"""
        try:
            data = json.loads(message)
            
            # Atualiza caches internos
            if 'e' in data:
                if data['e'] == 'trade':
                    self._update_trade_cache(data)
                elif data['e'] == 'depth':
                    self._update_orderbook_cache(data)
            
            # Notifica callbacks
            for callback in self.callbacks:
                callback(data)
                
        except Exception as e:
            logging.error(f"Erro ao processar mensagem: {e}")
    
    def _find_order_walls(self, bids: np.ndarray, asks: np.ndarray, 
                         threshold: float = 1.5) -> Dict:
        """Identifica paredes de ordens significativas"""
        walls = {
            'bids': [],
            'asks': []
        }
        
        for side, orders in [('bids', bids), ('asks', asks)]:
            volumes = orders[:, 1]
            mean_vol = np.mean(volumes)
            
            for price, vol in orders:
                if vol > mean_vol * threshold:
                    walls[side].append({
                        'price': float(price),
                        'volume': float(vol)
                    })
        
        return walls
    
    def _handle_socket_error(self, ws, error):
        """Trata erros do WebSocket"""
        logging.error(f"Erro no WebSocket: {error}")
        
    def _handle_socket_close(self, ws, close_status_code, close_msg):
        """Trata fechamento do WebSocket"""
        logging.info("WebSocket fechado")
        
    def get_historical_klines(self, symbol: str, interval: str, 
                            start_time: Optional[datetime] = None,
                            limit: int = 1000) -> pd.DataFrame:
        """Obtém dados históricos"""
        try:
            # Se não especificado, pega últimas 1000 velas
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=int(start_time.timestamp() * 1000) if start_time else None
            )
            
            # Converte para DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Converte tipos
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            return df
            
        except Exception as e:
            logging.error(f"Erro ao obter dados históricos: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol: str) -> float:
        """Obtém preço atual"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logging.error(f"Erro ao obter preço: {e}")
            return 0.0
    
    def _update_trade_cache(self, trade_data: Dict):
        """Atualiza cache de trades"""
        try:
            if hasattr(self, 'trade_cache'):
                self.trade_cache.append({
                    'price': float(trade_data['p']),
                    'quantity': float(trade_data['q']),
                    'time': datetime.fromtimestamp(trade_data['T'] / 1000),
                    'buyer_maker': trade_data['m']
                })
                
                # Mantém apenas últimos 1000 trades
                if len(self.trade_cache) > 1000:
                    self.trade_cache.pop(0)
        except Exception as e:
            logging.error(f"Erro ao atualizar cache de trades: {e}")

class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret)
        self.logger = logging.getLogger('binance_client')

    def get_symbol_info(self, symbol: str) -> Dict:
        """Obtém informações do símbolo"""
        try:
            return self.client.get_symbol_info(symbol)
        except Exception as e:
            self.logger.error(f"Erro ao obter info do símbolo: {str(e)}")
            return {}

    def get_current_price(self, symbol: str) -> float:
        """Obtém preço atual do símbolo"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            self.logger.error(f"Erro ao obter preço: {str(e)}")
            return 0.0

    def get_asset_balance(self, asset: str) -> Dict:
        """Obtém saldo de um ativo"""
        try:
            return self.client.get_asset_balance(asset=asset)
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo: {str(e)}")
            return {'free': '0.0', 'locked': '0.0'}

    def create_order(self, **params) -> Dict:
        """Cria uma ordem"""
        try:
            return self.client.create_order(**params)
        except Exception as e:
            self.logger.error(f"Erro ao criar ordem: {str(e)}")
            raise

    def get_open_orders(self, symbol: str = None) -> list:
        """Obtém ordens abertas"""
        try:
            return self.client.get_open_orders(symbol=symbol)
        except Exception as e:
            self.logger.error(f"Erro ao obter ordens abertas: {str(e)}")
            return []

    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancela uma ordem"""
        try:
            return self.client.cancel_order(
                symbol=symbol,
                orderId=order_id
            )
        except Exception as e:
            self.logger.error(f"Erro ao cancelar ordem: {str(e)}")
            raise

    def get_order_status(self, symbol: str, order_id: str) -> Dict:
        """Obtém status de uma ordem"""
        try:
            return self.client.get_order(
                symbol=symbol,
                orderId=order_id
            )
        except Exception as e:
            self.logger.error(f"Erro ao obter status da ordem: {str(e)}")
            return {}

    def get_all_orders(self, symbol: str, limit: int = 100) -> list:
        """Obtém histórico de ordens"""
        try:
            return self.client.get_all_orders(
                symbol=symbol,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de ordens: {str(e)}")
            return []