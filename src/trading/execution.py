from typing import Dict, Optional
from datetime import datetime
import logging
from decimal import Decimal, ROUND_DOWN
from src.data.binance_client import BinanceClient

class OrderExecutor:
    def __init__(self, api_key: str, api_secret: str, risk_manager):
        self.logger = logging.getLogger('order_executor')
        self.client = BinanceClient(api_key, api_secret)
        self.risk_manager = risk_manager
        self.min_order_value = 10  # Valor mínimo em USDT
        
    def validate_order(self, symbol: str, quantity: float, side: str) -> Dict:
        """Valida parâmetros da ordem antes da execução"""
        try:
            # Obtém informações do símbolo
            symbol_info = self.client.get_symbol_info(symbol)
            current_price = self.client.get_current_price(symbol)
            
            # Valida quantidade mínima
            min_qty = float(symbol_info['filters'][2]['minQty'])
            if quantity < min_qty:
                return {
                    'valid': False,
                    'reason': f'Quantidade menor que o mínimo permitido ({min_qty})'
                }
            
            # Valida valor mínimo da ordem
            order_value = quantity * current_price
            if order_value < self.min_order_value:
                return {
                    'valid': False,
                    'reason': f'Valor da ordem menor que o mínimo ({self.min_order_value} USDT)'
                }
            
            # Valida saldo disponível
            if side == 'BUY':
                balance = self.client.get_asset_balance('USDT')
                if float(balance['free']) < order_value:
                    return {
                        'valid': False,
                        'reason': 'Saldo insuficiente'
                    }
            else:
                balance = self.client.get_asset_balance(symbol.replace('USDT', ''))
                if float(balance['free']) < quantity:
                    return {
                        'valid': False,
                        'reason': 'Saldo insuficiente para venda'
                    }
            
            return {'valid': True}
            
        except Exception as e:
            self.logger.error(f"Erro na validação da ordem: {str(e)}")
            return {'valid': False, 'reason': str(e)}

    def normalize_quantity(self, symbol: str, quantity: float) -> float:
        """Normaliza quantidade de acordo com regras do símbolo"""
        try:
            symbol_info = self.client.get_symbol_info(symbol)
            step_size = float(symbol_info['filters'][2]['stepSize'])
            
            # Arredonda para baixo no stepSize correto
            normalized = Decimal(str(quantity))
            normalized = normalized.quantize(Decimal(str(step_size)), rounding=ROUND_DOWN)
            
            return float(normalized)
            
        except Exception as e:
            self.logger.error(f"Erro na normalização da quantidade: {str(e)}")
            return quantity

    def execute_order(self, symbol: str, side: str, signal_strength: float, 
                     technical_data: Dict) -> Dict:
        """Executa uma ordem com validações"""
        try:
            # Verifica condições de risco
            if not self.risk_manager.can_trade():
                return {
                    'status': 'rejected',
                    'reason': 'risk_limit',
                    'details': 'Limites de risco excedidos'
                }

            # Calcula tamanho da posição
            position_size = self.risk_manager.calculate_position_size(symbol)
            position_size = self.normalize_quantity(symbol, position_size)
            
            # Valida ordem
            validation = self.validate_order(symbol, position_size, side)
            if not validation['valid']:
                return {
                    'status': 'rejected',
                    'reason': 'validation_failed',
                    'details': validation['reason']
                }

            # Calcula preços
            entry_price = self.client.get_current_price(symbol)
            stops = self.calculate_stop_levels(entry_price, technical_data)
            
            # Prepara ordem principal
            order = {
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'quantity': position_size,
                'price': entry_price,
                'timeInForce': 'GTC'
            }

            # Executa ordem
            result = self.client.create_order(**order)
            
            # Coloca stops se ordem principal foi bem sucedida
            if result['status'] == 'FILLED':
                self._place_stop_orders(symbol, side, position_size, stops)
            
            return {
                'status': 'success',
                'order': result,
                'position_size': position_size,
                'entry_price': entry_price,
                'stops': stops,
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Erro na execução da ordem: {str(e)}")
            return {
                'status': 'error',
                'reason': str(e)
            }

    def _place_stop_orders(self, symbol: str, side: str, quantity: float, 
                          stops: Dict) -> None:
        """Coloca ordens de stop loss e take profit"""
        try:
            opposite_side = 'SELL' if side == 'BUY' else 'BUY'
            
            # Stop Loss
            self.client.create_order(
                symbol=symbol,
                side=opposite_side,
                type='STOP_LOSS_LIMIT',
                quantity=quantity,
                price=stops['stop_loss'],
                stopPrice=stops['stop_loss'],
                timeInForce='GTC'
            )
            
            # Take Profit
            self.client.create_order(
                symbol=symbol,
                side=opposite_side,
                type='TAKE_PROFIT_LIMIT',
                quantity=quantity,
                price=stops['take_profit'],
                stopPrice=stops['take_profit'],
                timeInForce='GTC'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao colocar stops: {str(e)}")