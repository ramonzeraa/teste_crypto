import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import logging

class RiskManager:
    def __init__(self):
        self.trades_history = []
        self.daily_stats = {}
        self.risk_metrics = {
            'max_daily_loss': -0.03,  # 3% máximo de perda diária
            'max_position_size': 0.05,  # 5% do capital por posição
            'max_open_positions': 3,    # máximo de posições simultâneas
            'min_confidence': 0.8       # confiança mínima para operar
        }
        
        # Métricas de performance
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }
    
    def can_open_position(self, capital: float, position_size: float, 
                         confidence: float) -> Dict[str, bool]:
        """Verifica se pode abrir nova posição"""
        try:
            daily_loss = self._calculate_daily_loss()
            current_exposure = self._calculate_current_exposure(capital)
            
            checks = {
                'daily_loss_limit': daily_loss > self.risk_metrics['max_daily_loss'],
                'position_size_limit': (position_size / capital) <= self.risk_metrics['max_position_size'],
                'max_positions': len(self._get_open_positions()) < self.risk_metrics['max_open_positions'],
                'confidence_threshold': confidence >= self.risk_metrics['min_confidence']
            }
            
            return {
                'allowed': all(checks.values()),
                'checks': checks
            }
            
        except Exception as e:
            logging.error(f"Erro na verificação de risco: {e}")
            return {'allowed': False, 'checks': {}}
    
    def register_trade(self, trade_data: Dict):
        """Registra uma operação"""
        try:
            trade_data['timestamp'] = datetime.now()
            self.trades_history.append(trade_data)
            self._update_performance_metrics()
            self._update_daily_stats()
            
        except Exception as e:
            logging.error(f"Erro ao registrar trade: {e}")
    
    def get_performance_report(self) -> Dict:
        """Gera relatório de performance"""
        try:
            return {
                'metrics': self.performance_metrics,
                'daily_stats': self._get_daily_summary(),
                'risk_analysis': self._get_risk_analysis(),
                'learning_curve': self._calculate_learning_curve()
            }
        except Exception as e:
            logging.error(f"Erro ao gerar relatório: {e}")
            return {}
    
    def _calculate_daily_loss(self) -> float:
        """Calcula perda diária"""
        try:
            today = datetime.now().date()
            today_trades = [
                t for t in self.trades_history 
                if t['timestamp'].date() == today
            ]
            
            if not today_trades:
                return 0.0
                
            return sum(t['profit_loss'] for t in today_trades)
            
        except Exception as e:
            logging.error(f"Erro ao calcular perda diária: {e}")
            return 0.0
    
    def _calculate_current_exposure(self, capital: float) -> float:
        """Calcula exposição atual"""
        try:
            open_positions = self._get_open_positions()
            total_exposure = sum(p['size'] for p in open_positions)
            return total_exposure / capital
            
        except Exception as e:
            logging.error(f"Erro ao calcular exposição: {e}")
            return 0.0
    
    def _update_performance_metrics(self):
        """Atualiza métricas de performance"""
        try:
            if not self.trades_history:
                return
                
            # Métricas básicas
            self.performance_metrics['total_trades'] = len(self.trades_history)
            self.performance_metrics['winning_trades'] = len([
                t for t in self.trades_history if t['profit_loss'] > 0
            ])
            self.performance_metrics['losing_trades'] = len([
                t for t in self.trades_history if t['profit_loss'] <= 0
            ])
            
            # Win rate e médias
            if self.performance_metrics['total_trades'] > 0:
                self.performance_metrics['win_rate'] = (
                    self.performance_metrics['winning_trades'] / 
                    self.performance_metrics['total_trades']
                )
            
            # Profit Factor e Sharpe Ratio
            profits = [t['profit_loss'] for t in self.trades_history if t['profit_loss'] > 0]
            losses = [abs(t['profit_loss']) for t in self.trades_history if t['profit_loss'] < 0]
            
            if profits:
                self.performance_metrics['avg_profit'] = np.mean(profits)
            if losses:
                self.performance_metrics['avg_loss'] = np.mean(losses)
            if losses and sum(losses) > 0:
                self.performance_metrics['profit_factor'] = sum(profits) / sum(losses)
            
            # Drawdown
            self.performance_metrics['max_drawdown'] = self._calculate_max_drawdown()
            
        except Exception as e:
            logging.error(f"Erro ao atualizar métricas: {e}")
    
    def _calculate_max_drawdown(self) -> float:
        """Calcula máximo drawdown"""
        try:
            if not self.trades_history:
                return 0.0
                
            equity_curve = self._generate_equity_curve()
            rolling_max = equity_curve.expanding().max()
            drawdowns = (equity_curve - rolling_max) / rolling_max
            return float(drawdowns.min())
            
        except Exception as e:
            logging.error(f"Erro ao calcular drawdown: {e}")
            return 0.0
    
    def _generate_equity_curve(self) -> pd.Series:
        """Gera curva de equity"""
        try:
            df = pd.DataFrame(self.trades_history)
            df['cumulative_return'] = df['profit_loss'].cumsum()
            return df['cumulative_return']
            
        except Exception as e:
            logging.error(f"Erro ao gerar equity curve: {e}")
            return pd.Series() 