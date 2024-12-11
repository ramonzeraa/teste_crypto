from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Dict, Optional
import logging
from datetime import datetime
import time
import numpy as np
from decimal import Decimal
from src.trading.risk_manager import RiskManager

class OrderExecutor:
    def __init__(self, api_key: str, api_secret: str, risk_manager: RiskManager):
        self.logger = logging.getLogger('order_executor')
        
        try:
            # Configuração do cliente com recvWindow explícito
            self.client = Client(
                api_key, 
                api_secret,
                {"verify": True, "timeout": 20}
            )
            self.risk_manager = risk_manager
            self.open_orders = {}
            self.positions = {}
            self.logger.info("OrderExecutor inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar OrderExecutor: {e}")
            raise

    def execute_order(self, symbol: str, side: str, signal_strength: float,
                     technical_data: Dict) -> Dict:
        """Executa ordem com gestão de risco"""
        try:
            self.logger.info(f"Executando ordem: {symbol} {side}")
            
            # Obtém tempo do servidor
            server_time = self.client.get_server_time()
            
            # Parâmetros base para todas as chamadas
            params = {
                'timestamp': server_time['serverTime'],
                'recvWindow': 5000
            }
            
            # Obtém dados da conta
            account = self.client.get_account(**params)
            balance = self._get_available_balance(account)
            self.logger.info(f"Saldo disponível: {balance}")
            
            # Calcula tamanho da posição
            position_size = self.risk_manager.calculate_position_size(
                capital=balance,
                signal_strength=signal_strength,
                volatility=technical_data.get('bb', {}).get('width', 0.02),
                current_exposure=self.risk_manager.risk_metrics['position_exposure']
            )
            
            if position_size == 0:
                self.logger.warning("Tamanho de posição insuficiente")
                return {'status': 'rejected', 'reason': 'insufficient_size'}
            
            # Verifica se pode abrir posição
            if not self.risk_manager.can_open_position(symbol, float(position_size), balance):
                self.logger.warning("Limite de risco atingido")
                return {'status': 'rejected', 'reason': 'risk_limit'}
            
            # Prepara ordem
            order_params = params.copy()
            order_params.update({
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': float(position_size)
            })
            
            # Executa ordem
            self.logger.info(f"Enviando ordem: {order_params}")
            order = self.client.create_order(**order_params)
            
            if order['status'] == 'FILLED':
                self.logger.info(f"Ordem executada com sucesso: {order['orderId']}")
                return {
                    'status': 'success',
                    'order': order,
                    'position_size': float(position_size),
                    'entry_price': float(order['fills'][0]['price'])
                }
            
            self.logger.warning(f"Ordem não preenchida: {order['status']}")
            return {'status': 'error', 'reason': 'order_failed'}
            
        except BinanceAPIException as e:
            self.logger.error(f"Erro na API Binance: {e}")
            return {'status': 'rejected', 'reason': str(e)}
        except Exception as e:
            self.logger.error(f"Erro na execução da ordem: {e}")
            return {'status': 'error', 'reason': str(e)}

    def _get_available_balance(self, account: Dict) -> float:
        """Obtém saldo disponível em USDT"""
        try:
            usdt_balance = next(
                (b for b in account['balances'] if b['asset'] == 'USDT'),
                {'free': '0.0'}
            )
            return float(usdt_balance['free'])
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo: {e}")
            return 0.0