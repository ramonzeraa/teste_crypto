from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Dict, Optional
import logging
from datetime import datetime
import numpy as np
from decimal import Decimal, ROUND_DOWN

class OrderExecutor:
    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret)
        self.open_orders = {}
        self.positions = {}
        
        # Configurações de risco
        self.max_position_size = 0.02  # 2% do capital
        self.max_slippage = 0.001     # 0.1% máximo de slippage
        self.min_order_interval = 60   # 60 segundos entre ordens
        self.last_order_time = None
    
    def execute_order(self, symbol: str, side: str, signal_strength: float) -> Dict:
        """Executa ordem com gestão de risco"""
        try:
            # Verifica restrições de tempo
            if not self._can_place_order():
                return {'status': 'rejected', 'reason': 'time_restriction'}
            
            # Obtém dados da conta
            account = self.client.get_account()
            balance = self._get_available_balance(account)
            
            # Calcula tamanho da ordem
            order_size = self._calculate_position_size(
                balance=balance,
                signal_strength=signal_strength,
                symbol=symbol
            )
            
            if order_size == 0:
                return {'status': 'rejected', 'reason': 'insufficient_size'}
            
            # Verifica preço atual
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            # Coloca ordem
            order = self._place_order(
                symbol=symbol,
                side=side,
                quantity=order_size,
                price=current_price
            )
            
            if order['status'] == 'FILLED':
                # Coloca ordens de proteção
                self._place_protection_orders(
                    symbol=symbol,
                    entry_price=float(order['fills'][0]['price']),
                    quantity=float(order['executedQty']),
                    side=side
                )
                
                self.last_order_time = datetime.now()
                
            return {
                'status': 'success',
                'order': order,
                'position_size': order_size,
                'entry_price': float(order['fills'][0]['price'])
            }
            
        except Exception as e:
            logging.error(f"Erro na execução da ordem: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _calculate_position_size(self, balance: float, signal_strength: float, 
                               symbol: str) -> float:
        """Calcula tamanho da posição baseado na força do sinal"""
        try:
            # Base size é 1% do capital
            base_size = balance * 0.01
            
            # Ajusta baseado na força do sinal (0.5 a 2.0)
            size_multiplier = 0.5 + abs(signal_strength)
            position_size = base_size * size_multiplier
            
            # Limita ao máximo permitido
            position_size = min(position_size, balance * self.max_position_size)
            
            # Ajusta para precisão do símbolo
            symbol_info = self.client.get_symbol_info(symbol)
            lot_size_filter = next(filter(
                lambda x: x['filterType'] == 'LOT_SIZE', 
                symbol_info['filters']
            ))
            
            step_size = float(lot_size_filter['stepSize'])
            precision = len(str(step_size).split('.')[-1])
            
            return float(
                Decimal(str(position_size))
                .quantize(Decimal(str(step_size)), rounding=ROUND_DOWN)
            )
            
        except Exception as e:
            logging.error(f"Erro no cálculo do tamanho: {e}")
            return 0.0
    
    def _place_protection_orders(self, symbol: str, entry_price: float, 
                               quantity: float, side: str):
        """Coloca ordens de stop loss e take profit"""
        try:
            # Configurações de proteção
            stop_loss_pct = 0.02  # 2%
            take_profit_pct = 0.03  # 3%
            
            if side == 'BUY':
                stop_price = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 + take_profit_pct)
                sl_side = 'SELL'
                tp_side = 'SELL'
            else:
                stop_price = entry_price * (1 + stop_loss_pct)
                take_profit = entry_price * (1 - take_profit_pct)
                sl_side = 'BUY'
                tp_side = 'BUY'
            
            # Coloca stop loss
            stop_loss_order = self.client.create_order(
                symbol=symbol,
                side=sl_side,
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                stopPrice=stop_price,
                price=stop_price
            )
            
            # Coloca take profit
            take_profit_order = self.client.create_order(
                symbol=symbol,
                side=tp_side,
                type='TAKE_PROFIT_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                stopPrice=take_profit,
                price=take_profit
            )
            
            return {
                'stop_loss': stop_loss_order,
                'take_profit': take_profit_order
            }
            
        except Exception as e:
            logging.error(f"Erro ao colocar ordens de proteção: {e}")
            return None
    
    def _can_place_order(self) -> bool:
        """Verifica se pode colocar nova ordem"""
        if not self.last_order_time:
            return True
            
        time_since_last = (datetime.now() - self.last_order_time).total_seconds()
        return time_since_last >= self.min_order_interval
    
    def _get_available_balance(self, account: Dict) -> float:
        """Obtém saldo disponível em USDT"""
        try:
            usdt_balance = next(
                (b for b in account['balances'] if b['asset'] == 'USDT'),
                {'free': '0.0'}
            )
            return float(usdt_balance['free'])
            
        except Exception as e:
            logging.error(f"Erro ao obter saldo: {e}")
            return 0.0 