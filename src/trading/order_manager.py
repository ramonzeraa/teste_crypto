from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Dict, Optional
import logging
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

class OrderManager:
    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret)
        self.open_orders = {}
        self.position = None
        self.last_order_time = None
        
        # Configurações de trading
        self.min_order_interval = 3600  # 1 hora em segundos
        self.max_position_size = 0.01  # 1% do capital
        self.stop_loss_percent = 0.02  # 2%
        self.take_profit_percent = 0.03  # 3%
    
    def execute_order(self, symbol: str, side: str, confidence: float) -> Dict:
        """Executa uma ordem com base nos sinais"""
        try:
            # Verifica restrições de tempo
            if not self._can_place_order():
                return {'status': 'rejected', 'reason': 'time_restriction'}
            
            # Obtém informações da conta
            account_info = self.client.get_account()
            balance = self._get_available_balance(account_info)
            
            # Calcula tamanho da posição
            position_size = self._calculate_position_size(
                balance,
                confidence,
                symbol
            )
            
            if position_size == 0:
                return {'status': 'rejected', 'reason': 'insufficient_funds'}
            
            # Executa a ordem
            order = self._place_order(symbol, side, position_size)
            
            if order:
                # Coloca ordens de proteção
                self._place_protection_orders(symbol, order, side)
                
                self.last_order_time = datetime.now()
                self.position = {
                    'symbol': symbol,
                    'side': side,
                    'size': position_size,
                    'entry_price': float(order['price']),
                    'order_id': order['orderId']
                }
                
                return {
                    'status': 'success',
                    'order': order,
                    'position': self.position
                }
            
            return {'status': 'failed', 'reason': 'order_placement_failed'}
            
        except BinanceAPIException as e:
            logging.error(f"Erro Binance API: {e}")
            return {'status': 'error', 'reason': str(e)}
        except Exception as e:
            logging.error(f"Erro ao executar ordem: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _can_place_order(self) -> bool:
        """Verifica se pode executar nova ordem"""
        if not self.last_order_time:
            return True
            
        time_passed = (datetime.now() - self.last_order_time).total_seconds()
        return time_passed >= self.min_order_interval
    
    def _get_available_balance(self, account_info: Dict) -> float:
        """Obtém saldo disponível"""
        for balance in account_info['balances']:
            if balance['asset'] == 'USDT':
                return float(balance['free'])
        return 0.0
    
    def _calculate_position_size(self, balance: float, confidence: float, symbol: str) -> float:
        """Calcula tamanho da posição baseado na confiança"""
        try:
            # Obtém preço atual
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            # Calcula tamanho base da posição
            position_size = balance * self.max_position_size
            
            # Ajusta baseado na confiança (0.5 a 1.0)
            adjusted_size = position_size * (confidence - 0.5) * 2
            
            # Converte para quantidade de cripto
            quantity = adjusted_size / price
            
            # Arredonda para precisão adequada
            info = self.client.get_symbol_info(symbol)
            precision = info['quotePrecision']
            quantity = Decimal(str(quantity)).quantize(
                Decimal('0.{}'.format('0' * precision)),
                rounding=ROUND_DOWN
            )
            
            return float(quantity)
            
        except Exception as e:
            logging.error(f"Erro ao calcular tamanho da posição: {e}")
            return 0.0
    
    def _place_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict]:
        """Coloca ordem no mercado"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            logging.info(f"Ordem executada: {order}")
            return order
            
        except Exception as e:
            logging.error(f"Erro ao colocar ordem: {e}")
            return None
    
    def _place_protection_orders(self, symbol: str, entry_order: Dict, side: str):
        """Coloca ordens de stop loss e take profit"""
        try:
            entry_price = float(entry_order['fills'][0]['price'])
            quantity = float(entry_order['executedQty'])
            
            # Calcula preços de proteção
            if side == 'BUY':
                stop_loss = entry_price * (1 - self.stop_loss_percent)
                take_profit = entry_price * (1 + self.take_profit_percent)
                sl_side = 'SELL'
                tp_side = 'SELL'
            else:
                stop_loss = entry_price * (1 + self.stop_loss_percent)
                take_profit = entry_price * (1 - self.take_profit_percent)
                sl_side = 'BUY'
                tp_side = 'BUY'
            
            # Coloca ordens de proteção
            stop_loss_order = self.client.create_order(
                symbol=symbol,
                side=sl_side,
                type='STOP_LOSS_LIMIT',
                quantity=quantity,
                price=stop_loss,
                stopPrice=stop_loss
            )
            
            take_profit_order = self.client.create_order(
                symbol=symbol,
                side=tp_side,
                type='TAKE_PROFIT_LIMIT',
                quantity=quantity,
                price=take_profit,
                stopPrice=take_profit
            )
            
            logging.info(f"Ordens de proteção colocadas: SL={stop_loss}, TP={take_profit}")
            
        except Exception as e:
            logging.error(f"Erro ao colocar ordens de proteção: {e}") 