from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Position:
    symbol: str
    side: str
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

class PortfolioManager:
    def __init__(self):
        self.logger = logging.getLogger('portfolio_manager')
        self.positions = {}
        self.balance = 0.0
        self.total_pnl = 0.0
        self.trade_history = []
        self.metrics = {
            'total_value': 0.0,
            'total_unrealized_pnl': 0.0,
            'total_pnl': 0.0,
            'position_count': 0,
            'last_update': datetime.now()
        }
        self.position_limits = {
            'max_positions': 3,
            'max_position_size': 0.1,  # 10% do portfolio
            'max_leverage': 1.0
        }
        
        # Inicializa com uma posição vazia para evitar o erro
        self.positions['BTC'] = {
            'amount': 0.0,
            'entry_price': 0.0,
            'current_price': 0.0,
            'side': 'long',
            'leverage': 1.0,
            'value': 0.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
            'entry_time': datetime.now(),
            'last_update': datetime.now(),
            'status': 'open'
        }

    def get_portfolio_status(self) -> Dict:
        """Retorna status atual do portfolio"""
        try:
            return {
                'positions': self.positions,
                'balance': self.balance,
                'total_pnl': self.total_pnl,
                'total_value': self.balance + sum(pos.get('value', 0) for pos in self.positions.values()),
                'position_count': len(self.positions),
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter status do portfolio: {e}")
            return {
                'positions': {},
                'balance': 0.0,
                'total_pnl': 0.0,
                'total_value': 0.0,
                'position_count': 0,
                'timestamp': datetime.now()
            }

    def update_balance(self, amount: float):
        """Atualiza o saldo do portfolio"""
        try:
            self.balance += amount
            self.logger.info(f"Saldo atualizado: {self.balance}")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar saldo: {e}")

    def add_position(self, symbol: str, amount: float, entry_price: float, 
                    side: str = 'long', leverage: float = 1.0) -> bool:
        """Adiciona nova posição"""
        try:
            # Verifica limites
            if len(self.positions) >= self.position_limits['max_positions']:
                self.logger.warning("Limite máximo de posições atingido")
                return False

            position_value = amount * entry_price
            if position_value / self.balance > self.position_limits['max_position_size']:
                self.logger.warning("Tamanho máximo de posição excedido")
                return False

            if leverage > self.position_limits['max_leverage']:
                self.logger.warning("Alavancagem máxima excedida")
                return False

            # Adiciona posição com todos os campos necessários
            self.positions[symbol] = {
                'amount': amount,
                'entry_price': entry_price,
                'current_price': entry_price,
                'side': side,
                'leverage': leverage,
                'value': position_value,
                'unrealized_pnl': 0.0,  # Inicializa PnL
                'realized_pnl': 0.0,    # Inicializa PnL realizado
                'entry_time': datetime.now(),
                'last_update': datetime.now(),
                'status': 'open'
            }

            self.logger.info(f"Posição adicionada: {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao adicionar posição: {str(e)}")
            return False

    def update_position(self, symbol: str, current_price: float):
        """Atualiza posição existente"""
        try:
            if symbol not in self.positions:
                return

            position = self.positions[symbol]
            old_value = position['value']
            
            # Atualiza valor e PnL
            position['current_price'] = current_price
            position['value'] = position['amount'] * current_price
            
            if position['side'] == 'long':
                position['unrealized_pnl'] = (current_price - position['entry_price']) * position['amount']
            else:
                position['unrealized_pnl'] = (position['entry_price'] - current_price) * position['amount']

            position['unrealized_pnl'] *= position['leverage']
            
            self.logger.debug(f"Posição atualizada: {symbol}")

        except Exception as e:
            self.logger.error(f"Erro ao atualizar posição: {e}")

    def close_position(self, symbol: str, exit_price: float) -> Optional[Dict]:
        """Fecha posição existente"""
        try:
            if symbol not in self.positions:
                return None

            position = self.positions[symbol]
            
            # Calcula PnL realizado
            if position['side'] == 'long':
                realized_pnl = (exit_price - position['entry_price']) * position['amount']
            else:
                realized_pnl = (position['entry_price'] - exit_price) * position['amount']

            realized_pnl *= position['leverage']
            
            # Atualiza métricas
            self.total_pnl += realized_pnl
            self.balance += realized_pnl
            
            # Registra trade
            trade_record = {
                'symbol': symbol,
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'amount': position['amount'],
                'side': position['side'],
                'pnl': realized_pnl,
                'entry_time': position['entry_time'],
                'exit_time': datetime.now(),
                'duration': (datetime.now() - position['entry_time']).total_seconds()
            }
            
            self.trade_history.append(trade_record)
            
            # Remove posição
            del self.positions[symbol]
            
            self.logger.info(f"Posição fechada: {symbol}, PnL: {realized_pnl:.2f}")
            return trade_record

        except Exception as e:
            self.logger.error(f"Erro ao fechar posição: {e}")
            return None

    def get_position_metrics(self) -> Dict:
        """Retorna métricas das posições"""
        try:
            total_exposure = sum(pos['value'] for pos in self.positions.values())
            total_leverage = sum(pos['value'] * pos['leverage'] for pos in self.positions.values())
            
            return {
                'total_positions': len(self.positions),
                'total_exposure': total_exposure,
                'total_leverage': total_leverage,
                'total_pnl': self.total_pnl,
                'unrealized_pnl': sum(pos['unrealized_pnl'] for pos in self.positions.values()),
                'portfolio_value': self.balance + total_exposure
            }

        except Exception as e:
            self.logger.error(f"Erro ao calcular métricas: {e}")
            return {}

    def get_trade_statistics(self) -> Dict:
        """Retorna estatísticas de trading"""
        try:
            if not self.trade_history:
                return {}

            pnls = [trade['pnl'] for trade in self.trade_history]
            durations = [trade['duration'] for trade in self.trade_history]
            
            return {
                'total_trades': len(self.trade_history),
                'winning_trades': len([pnl for pnl in pnls if pnl > 0]),
                'losing_trades': len([pnl for pnl in pnls if pnl < 0]),
                'avg_pnl': np.mean(pnls),
                'max_pnl': max(pnls),
                'min_pnl': min(pnls),
                'pnl_std': np.std(pnls),
                'avg_duration': np.mean(durations),
                'win_rate': len([pnl for pnl in pnls if pnl > 0]) / len(pnls)
            }

        except Exception as e:
            self.logger.error(f"Erro ao calcular estatísticas: {e}")
            return {} 

    def update_positions(self, current_prices: Dict):
        """Atualiza todas as posições com preços atuais"""
        try:
            if not current_prices:  # Se não houver preços, retorna sem erro
                return
                
            if not self.positions:  # Se não houver posições, cria uma vazia
                self.positions['BTC'] = {
                    'amount': 0.0,
                    'entry_price': 0.0,
                    'current_price': list(current_prices.values())[0],
                    'side': 'long',
                    'leverage': 1.0,
                    'value': 0.0,
                    'unrealized_pnl': 0.0,
                    'realized_pnl': 0.0,
                    'entry_time': datetime.now(),
                    'last_update': datetime.now(),
                    'status': 'open'
                }
            
            # Atualiza cada posição
            for symbol, price in current_prices.items():
                if symbol not in self.positions:
                    # Se o símbolo não existe, cria uma posição vazia
                    self.positions[symbol] = {
                        'amount': 0.0,
                        'entry_price': price,
                        'current_price': price,
                        'side': 'long',
                        'leverage': 1.0,
                        'value': 0.0,
                        'unrealized_pnl': 0.0,
                        'realized_pnl': 0.0,
                        'entry_time': datetime.now(),
                        'last_update': datetime.now(),
                        'status': 'open'
                    }
                else:
                    # Atualiza posição existente
                    position = self.positions[symbol]
                    position['current_price'] = price
                    position['value'] = position['amount'] * price
                    
                    # Calcula PnL
                    if position['side'] == 'long':
                        position['unrealized_pnl'] = (price - position['entry_price']) * position['amount']
                    else:
                        position['unrealized_pnl'] = (position['entry_price'] - price) * position['amount']
                    
                    position['unrealized_pnl'] *= position['leverage']
                    position['last_update'] = datetime.now()
            
            # Atualiza métricas
            self._update_portfolio_metrics()
            self.logger.debug("Posições atualizadas com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar posições: {str(e)}")

    def _update_portfolio_metrics(self):
        """Atualiza métricas gerais do portfolio"""
        try:
            # Calcula métricas com verificações de segurança
            total_value = sum(pos.get('value', 0) for pos in self.positions.values())
            total_unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in self.positions.values())
            
            # Atualiza métricas
            self.metrics = {
                'total_value': total_value,
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_pnl': self.total_pnl + total_unrealized_pnl,
                'position_count': len(self.positions),
                'last_update': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar métricas do portfolio: {str(e)}")
            raise  # Propaga o erro para melhor diagnóstico

    def get_portfolio_summary(self) -> Dict:
        """Retorna resumo do portfolio"""
        try:
            metrics = self.get_position_metrics()
            stats = self.get_trade_statistics()
            
            return {
                'metrics': metrics,
                'statistics': stats,
                'positions': self.positions,
                'balance': self.balance,
                'total_pnl': self.total_pnl,
                'last_update': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo do portfolio: {e}")
            return {} 