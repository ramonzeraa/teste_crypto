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
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.daily_stats: Dict[str, Dict] = {}
        self.initial_capital = 0.0
        self.current_capital = 0.0
        
        # Métricas de performance
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0
        }
    
    def update_portfolio(self, balance: float):
        """Atualiza capital do portfólio"""
        if self.initial_capital == 0:
            self.initial_capital = balance
        self.current_capital = balance
        self._update_metrics()
    
    def add_position(self, position_data: Dict):
        """Adiciona nova posição"""
        try:
            position = Position(
                symbol=position_data['symbol'],
                side=position_data['side'],
                entry_price=float(position_data['entry_price']),
                quantity=float(position_data['quantity']),
                entry_time=datetime.now(),
                stop_loss=float(position_data['stop_loss']),
                take_profit=float(position_data['take_profit'])
            )
            
            self.positions[position_data['symbol']] = position
            self._log_trade('OPEN', position_data)
            
        except Exception as e:
            logging.error(f"Erro ao adicionar posição: {e}")
    
    def close_position(self, symbol: str, exit_price: float, exit_reason: str):
        """Fecha posição existente"""
        try:
            if symbol not in self.positions:
                return
            
            position = self.positions[symbol]
            
            # Calcula P&L
            if position.side == 'BUY':
                pnl = (exit_price - position.entry_price) * position.quantity
            else:
                pnl = (position.entry_price - exit_price) * position.quantity
            
            # Registra trade
            trade_data = {
                'symbol': symbol,
                'side': position.side,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'quantity': position.quantity,
                'pnl': pnl,
                'exit_reason': exit_reason,
                'duration': datetime.now() - position.entry_time
            }
            
            self._log_trade('CLOSE', trade_data)
            
            # Atualiza métricas
            self.metrics['total_trades'] += 1
            if pnl > 0:
                self.metrics['winning_trades'] += 1
                self.metrics['largest_win'] = max(self.metrics['largest_win'], pnl)
            else:
                self.metrics['largest_loss'] = min(self.metrics['largest_loss'], pnl)
            
            # Remove posição
            del self.positions[symbol]
            
        except Exception as e:
            logging.error(f"Erro ao fechar posição: {e}")
    
    def update_positions(self, current_prices: Dict[str, float]):
        """Atualiza P&L não realizado das posições"""
        try:
            total_unrealized = 0.0
            
            for symbol, position in self.positions.items():
                if symbol in current_prices:
                    current_price = current_prices[symbol]
                    
                    # Calcula P&L não realizado
                    if position.side == 'BUY':
                        unrealized = (current_price - position.entry_price) * position.quantity
                    else:
                        unrealized = (position.entry_price - current_price) * position.quantity
                    
                    position.unrealized_pnl = unrealized
                    total_unrealized += unrealized
                    
                    # Verifica stop loss e take profit
                    self._check_exit_conditions(symbol, current_price)
            
            return total_unrealized
            
        except Exception as e:
            logging.error(f"Erro ao atualizar posições: {e}")
            return 0.0
    
    def get_portfolio_summary(self) -> Dict:
        """Retorna resumo do portfólio"""
        try:
            total_positions = len(self.positions)
            total_exposure = sum(p.quantity * p.entry_price for p in self.positions.values())
            unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
            
            return {
                'total_positions': total_positions,
                'total_exposure': total_exposure,
                'unrealized_pnl': unrealized_pnl,
                'realized_pnl': sum(t['pnl'] for t in self.trade_history),
                'current_capital': self.current_capital,
                'return_pct': (self.current_capital / self.initial_capital - 1) * 100 if self.initial_capital > 0 else 0,
                'metrics': self.metrics
            }
            
        except Exception as e:
            logging.error(f"Erro ao gerar resumo: {e}")
            return {}
    
    def _check_exit_conditions(self, symbol: str, current_price: float):
        """Verifica condições de saída"""
        try:
            position = self.positions[symbol]
            
            # Verifica stop loss
            if position.side == 'BUY' and current_price <= position.stop_loss:
                self.close_position(symbol, current_price, 'stop_loss')
            elif position.side == 'SELL' and current_price >= position.stop_loss:
                self.close_position(symbol, current_price, 'stop_loss')
            
            # Verifica take profit
            elif position.side == 'BUY' and current_price >= position.take_profit:
                self.close_position(symbol, current_price, 'take_profit')
            elif position.side == 'SELL' and current_price <= position.take_profit:
                self.close_position(symbol, current_price, 'take_profit')
                
        except Exception as e:
            logging.error(f"Erro ao verificar saídas: {e}")
    
    def _log_trade(self, action: str, trade_data: Dict):
        """Registra detalhes do trade"""
        try:
            trade_record = {
                'timestamp': datetime.now(),
                'action': action,
                **trade_data
            }
            
            self.trade_history.append(trade_record)
            logging.info(f"Trade registrado: {json.dumps(trade_record, default=str)}")
            
        except Exception as e:
            logging.error(f"Erro ao registrar trade: {e}")
    
    def _update_metrics(self):
        """Atualiza métricas de performance"""
        try:
            if not self.trade_history:
                return
            
            # Calcula métricas básicas
            total_trades = len(self.trade_history)
            winning_trades = len([t for t in self.trade_history if t.get('pnl', 0) > 0])
            
            self.metrics.update({
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
                'profit_factor': self._calculate_profit_factor(),
                'sharpe_ratio': self._calculate_sharpe_ratio(),
                'max_drawdown': self._calculate_max_drawdown()
            })
            
        except Exception as e:
            logging.error(f"Erro ao atualizar métricas: {e}") 