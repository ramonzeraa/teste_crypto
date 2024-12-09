from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Dict, Optional
import logging
from datetime import datetime
import numpy as np
from decimal import Decimal
from src.trading.risk_manager import RiskManager

class OrderExecutor:
    def __init__(self, api_key: str, api_secret: str, risk_manager: RiskManager):
        self.client = Client(api_key, api_secret)
        self.risk_manager = risk_manager
        self.open_orders = {}
        self.positions = {}
    
    def execute_order(self, symbol: str, side: str, signal_strength: float,
                     technical_data: Dict) -> Dict:
        """Executa ordem com gestão de risco"""
        try:
            # Obtém dados da conta
            account = self.client.get_account()
            balance = self._get_available_balance(account)
            
            # Obtém dados técnicos
            volatility = technical_data.get('bb', {}).get('width', 0.02)
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            atr = technical_data.get('atr', volatility * current_price)
            
            # Calcula tamanho da posição
            position_size = self.risk_manager.calculate_position_size(
                capital=balance,
                signal_strength=signal_strength,
                volatility=volatility,
                current_exposure=self.risk_manager.risk_metrics['position_exposure']
            )
            
            if position_size == 0:
                return {'status': 'rejected', 'reason': 'insufficient_size'}
            
            # Verifica se pode abrir posição
            if not self.risk_manager.can_open_position(symbol, float(position_size), balance):
                return {'status': 'rejected', 'reason': 'risk_limit'}
            
            # Calcula stops
            stops = self.risk_manager.calculate_stop_loss(
                entry_price=current_price,
                volatility=volatility,
                atr=atr,
                side=side
            )
            
            # Coloca ordem principal
            order = self._place_order(symbol, side, position_size, current_price)
            
            if order['status'] == 'FILLED':
                # Coloca ordens de proteção
                protection_orders = self._place_protection_orders(
                    symbol=symbol,
                    entry_price=float(order['fills'][0]['price']),
                    quantity=float(order['executedQty']),
                    side=side,
                    stops=stops
                )
                
                return {
                    'status': 'success',
                    'order': order,
                    'protection': protection_orders,
                    'position_size': float(position_size),
                    'entry_price': float(order['fills'][0]['price']),
                    'stops': stops
                }
            
            return {'status': 'error', 'reason': 'order_failed'}
            
        except Exception as e:
            logging.error(f"Erro na execução da ordem: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _place_order(self, symbol: str, side: str, quantity: Decimal, price: float) -> Dict:
        """Coloca ordem principal"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=float(quantity)
            )
            return order
        except Exception as e:
            logging.error(f"Erro ao colocar ordem: {e}")
            raise
    
    def _place_protection_orders(self, symbol: str, entry_price: float, 
                               quantity: float, side: str, stops: Dict) -> Dict:
        """Coloca ordens de proteção"""
        try:
            opposite_side = 'SELL' if side == 'BUY' else 'BUY'
            
            # Stop Loss
            stop_loss = self.client.create_order(
                symbol=symbol,
                side=opposite_side,
                type='STOP_LOSS_LIMIT',
                quantity=quantity,
                price=stops['stop_loss'],
                stopPrice=stops['stop_loss'],
                timeInForce='GTC'
            )
            
            # Take Profit
            take_profit = self.client.create_order(
                symbol=symbol,
                side=opposite_side,
                type='LIMIT',
                quantity=quantity,
                price=stops['take_profit'],
                timeInForce='GTC'
            )
            
            return {
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
            
        except Exception as e:
            logging.error(f"Erro ao colocar ordens de proteção: {e}")
            return {}
    
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