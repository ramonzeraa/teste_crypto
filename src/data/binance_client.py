import websocket
from typing import Callable, Dict
from datetime import datetime
import json
import numpy as np
import logging
from threading import Thread

class BinanceDataLoader:
    def __init__(self, api_key: str, api_secret: str):
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
