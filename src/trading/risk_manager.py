from typing import Dict, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from decimal import Decimal, ROUND_DOWN

class RiskManager:
    def __init__(self, config: Dict):
        # Configurações básicas
        self.config = config
        self.max_position_size = config.get('max_position_size', 0.02)  # 2% do capital
        self.max_total_risk = config.get('max_total_risk', 0.05)       # 5% do capital
        self.max_daily_drawdown = config.get('max_daily_drawdown', 0.03) # 3% do capital
        self.max_slippage = config.get('max_slippage', 0.001)         # 0.1% máximo de slippage
        self.min_order_interval = config.get('min_order_interval', 60) # 60 segundos entre ordens
        
        # Estado interno
        self.positions = {}
        self.daily_pnl = []
        self.last_order_time = None
        self.trade_history = []
        
        # Métricas de risco
        self.risk_metrics = {
            'current_drawdown': 0.0,
            'daily_drawdown': 0.0,
            'risk_score': 0.0,
            'position_exposure': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'avg_win_loss_ratio': 0.0
        }
    
    def calculate_position_size(self, capital: float, signal_strength: float, 
                              volatility: float, current_exposure: float) -> float:
        """Calcula tamanho da posição baseado em múltiplos fatores"""
        try:
            # Base size (1% do capital)
            base_size = capital * 0.01
            
            # Ajusta baseado na força do sinal (0.5 a 1.5)
            signal_multiplier = 0.5 + abs(signal_strength)
            
            # Ajusta baseado na volatilidade (reduz se alta volatilidade)
            volatility_multiplier = 1 - (volatility * 2)
            volatility_multiplier = max(0.5, min(1.0, volatility_multiplier))
            
            # Ajusta baseado na exposição atual
            exposure_multiplier = 1 - (current_exposure / self.max_total_risk)
            exposure_multiplier = max(0, min(1.0, exposure_multiplier))
            
            # Ajusta baseado no win rate histórico
            if self.risk_metrics['win_rate'] > 0:
                win_rate_multiplier = min(1.2, self.risk_metrics['win_rate'])
            else:
                win_rate_multiplier = 1.0
            
            # Calcula tamanho final
            position_size = (base_size * signal_multiplier * volatility_multiplier * 
                           exposure_multiplier * win_rate_multiplier)
            
            # Limita ao máximo permitido
            max_allowed = capital * self.max_position_size
            position_size = min(position_size, max_allowed)
            
            # Arredonda para baixo para precisão do ativo
            return Decimal(str(position_size)).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
            
        except Exception as e:
            logging.error(f"Erro no cálculo do tamanho da posição: {e}")
            return Decimal('0')
    
    def calculate_stop_loss(self, entry_price: float, volatility: float, 
                          atr: float, side: str) -> Dict:
        """Calcula níveis de stop loss dinâmico"""
        try:
            # Stop base (2 ATR)
            base_stop = atr * 2
            
            # Ajusta baseado na volatilidade
            volatility_adjustment = 1 + volatility
            adjusted_stop = base_stop * volatility_adjustment
            
            # Calcula take profit (2:1 risk/reward)
            if side == 'BUY':
                stop_loss = entry_price - adjusted_stop
                emergency_stop = entry_price - (adjusted_stop * 1.5)
                take_profit = entry_price + (adjusted_stop * 2)
            else:
                stop_loss = entry_price + adjusted_stop
                emergency_stop = entry_price + (adjusted_stop * 1.5)
                take_profit = entry_price - (adjusted_stop * 2)
            
            return {
                'stop_loss': stop_loss,
                'emergency_stop': emergency_stop,
                'take_profit': take_profit,
                'trailing_step': base_stop * 0.5
            }
            
        except Exception as e:
            logging.error(f"Erro no cálculo do stop loss: {e}")
            return {}
    
    def update_risk_metrics(self, positions: Dict, current_prices: Dict):
        """Atualiza métricas de risco"""
        try:
            total_exposure = 0
            unrealized_pnl = 0
            
            for symbol, position in positions.items():
                if symbol in current_prices:
                    price = current_prices[symbol]
                    size = position['quantity']
                    entry = position['entry_price']
                    
                    # Calcula exposição
                    exposure = (size * price) / position['account_size']
                    total_exposure += exposure
                    
                    # Calcula P&L não realizado
                    if position['side'] == 'BUY':
                        pnl = (price - entry) * size
                    else:
                        pnl = (entry - price) * size
                    
                    unrealized_pnl += pnl
            
            # Atualiza métricas
            self.risk_metrics['position_exposure'] = total_exposure
            self.risk_metrics['current_drawdown'] = -min(0, unrealized_pnl)
            
            # Atualiza drawdown diário
            self.daily_pnl.append(unrealized_pnl)
            if len(self.daily_pnl) > 1440:  # Mantém 24h de dados
                self.daily_pnl.pop(0)
            
            self.risk_metrics['daily_drawdown'] = -min(0, sum(self.daily_pnl))
            
            # Calcula score de risco (0-100)
            exposure_score = (total_exposure / self.max_total_risk) * 40
            drawdown_score = (self.risk_metrics['daily_drawdown'] / 
                            (self.max_daily_drawdown * 100)) * 60
            
            self.risk_metrics['risk_score'] = exposure_score + drawdown_score
            
            return self.risk_metrics
            
        except Exception as e:
            logging.error(f"Erro na atualização de métricas de risco: {e}")
            return {}
    
    def can_open_position(self, symbol: str, size: float, capital: float) -> bool:
        """Verifica se pode abrir nova posiç��o"""
        try:
            # Verifica tempo mínimo entre ordens
            if self.last_order_time:
                time_since_last = (datetime.now() - self.last_order_time).total_seconds()
                if time_since_last < self.min_order_interval:
                    return False
            
            # Verifica exposição total
            new_exposure = (size / capital) + self.risk_metrics['position_exposure']
            if new_exposure > self.max_total_risk:
                return False
            
            # Verifica drawdown diário
            if self.risk_metrics['daily_drawdown'] > self.max_daily_drawdown:
                return False
            
            # Verifica score de risco
            if self.risk_metrics['risk_score'] > 80:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Erro na verificação de posição: {e}")
            return False
    
    def should_reduce_exposure(self) -> bool:
        """Verifica se deve reduzir exposição"""
        return (self.risk_metrics['risk_score'] > 70 or
                self.risk_metrics['daily_drawdown'] > (self.max_daily_drawdown * 0.8))
    
    def update_trade_metrics(self, trade_result: Dict):
        """Atualiza métricas de trading"""
        try:
            self.trade_history.append(trade_result)
            
            # Mantém apenas últimos 100 trades
            if len(self.trade_history) > 100:
                self.trade_history.pop(0)
            
            # Calcula win rate
            winning_trades = len([t for t in self.trade_history if t['pnl'] > 0])
            total_trades = len(self.trade_history)
            self.risk_metrics['win_rate'] = winning_trades / total_trades if total_trades > 0 else 0
            
            # Calcula profit factor
            gross_profit = sum([t['pnl'] for t in self.trade_history if t['pnl'] > 0])
            gross_loss = abs(sum([t['pnl'] for t in self.trade_history if t['pnl'] < 0]))
            self.risk_metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # Calcula média ganho/perda
            avg_win = np.mean([t['pnl'] for t in self.trade_history if t['pnl'] > 0]) if winning_trades > 0 else 0
            avg_loss = abs(np.mean([t['pnl'] for t in self.trade_history if t['pnl'] < 0])) if total_trades - winning_trades > 0 else 0
            self.risk_metrics['avg_win_loss_ratio'] = avg_win / avg_loss if avg_loss > 0 else 0
            
        except Exception as e:
            logging.error(f"Erro na atualização de métricas de trading: {e}") 