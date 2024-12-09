from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class TradingValidator:
    def __init__(self):
        self.start_date = datetime.now()
        self.trades = []
        self.daily_stats = []
        self.validation_metrics = {
            'win_rate': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'total_trades': 0
        }
        
    def add_trade(self, trade):
        """Registra e analisa trade"""
        self.trades.append(trade)
        self.update_metrics()
        self.save_trade(trade)
        
    def update_metrics(self):
        """Atualiza métricas de performance"""
        if len(self.trades) < 1:
            return
            
        wins = [t for t in self.trades if t['pnl'] > 0]
        losses = [t for t in self.trades if t['pnl'] <= 0]
        
        self.validation_metrics.update({
            'win_rate': len(wins) / len(self.trades) if self.trades else 0,
            'profit_factor': (
                abs(sum(t['pnl'] for t in wins)) / 
                abs(sum(t['pnl'] for t in losses))
                if losses else float('inf')
            ),
            'max_drawdown': self.calculate_drawdown(),
            'sharpe_ratio': self.calculate_sharpe(),
            'avg_win': np.mean([t['pnl'] for t in wins]) if wins else 0,
            'avg_loss': np.mean([t['pnl'] for t in losses]) if losses else 0,
            'total_trades': len(self.trades)
        })
        
    def calculate_drawdown(self):
        """Calcula drawdown máximo"""
        if not self.trades:
            return 0
            
        balance = 1000  # Saldo inicial
        balances = [balance]
        
        for trade in self.trades:
            balance += trade['pnl']
            balances.append(balance)
            
        peak = balances[0]
        max_dd = 0
        
        for balance in balances:
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak
            max_dd = max(max_dd, dd)
            
        return max_dd
        
    def calculate_sharpe(self):
        """Calcula Sharpe Ratio"""
        if len(self.trades) < 2:
            return 0
            
        returns = [t['pnl'] / t['size'] for t in self.trades]
        return np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0
        
    def save_trade(self, trade):
        """Salva trade em CSV"""
        df = pd.DataFrame([{
            'timestamp': trade['timestamp'],
            'direction': trade['direction'],
            'entry_price': trade['entry_price'],
            'exit_price': trade['exit_price'],
            'size': trade['size'],
            'pnl': trade['pnl'],
            'win_rate': self.validation_metrics['win_rate'],
            'drawdown': self.validation_metrics['max_drawdown']
        }])
        
        df.to_csv('logs/validation_trades.csv', 
                 mode='a', 
                 header=not os.path.exists('logs/validation_trades.csv'))
                 
    def generate_report(self):
        """Gera relatório de validação"""
        days_running = (datetime.now() - self.start_date).days
        
        report = f"""
        === Relatório de Validação ===
        Período: {days_running} dias
        Trades Totais: {self.validation_metrics['total_trades']}
        
        Performance:
        - Win Rate: {self.validation_metrics['win_rate']:.2%}
        - Profit Factor: {self.validation_metrics['profit_factor']:.2f}
        - Max Drawdown: {self.validation_metrics['max_drawdown']:.2%}
        - Sharpe Ratio: {self.validation_metrics['sharpe_ratio']:.2f}
        
        Médias:
        - Gain: {self.validation_metrics['avg_win']:.2f} USDT
        - Loss: {self.validation_metrics['avg_loss']:.2f} USDT
        
        Status: {'APROVADO' if self.check_ready() else 'EM VALIDAÇÃO'}
        """
        
        self.plot_performance()
        return report
        
    def check_ready(self):
        """Verifica se está pronto para trading real"""
        return all([
            self.validation_metrics['total_trades'] >= 50,
            self.validation_metrics['win_rate'] >= 0.60,
            self.validation_metrics['max_drawdown'] <= 0.05,
            self.validation_metrics['profit_factor'] >= 1.5,
            (datetime.now() - self.start_date).days >= 30
        ])
        
    def plot_performance(self):
        """Gera gráficos de performance"""
        df = pd.read_csv('logs/validation_trades.csv')
        
        fig = make_subplots(rows=2, cols=1, 
                          subplot_titles=('Equity Curve', 'Win Rate & Drawdown'))
        
        # Equity Curve
        balance = 1000
        equity = [balance]
        for pnl in df['pnl']:
            balance += pnl
            equity.append(balance)
            
        fig.add_trace(
            go.Scatter(y=equity, name='Equity'),
            row=1, col=1
        )
        
        # Win Rate & Drawdown
        fig.add_trace(
            go.Scatter(y=df['win_rate'], name='Win Rate'),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(y=df['drawdown'], name='Drawdown'),
            row=2, col=1
        )
        
        fig.update_layout(height=800, title_text='Performance Metrics')
        fig.write_html('logs/performance.html') 