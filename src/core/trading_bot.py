from binance.client import Client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sklearn.ensemble import RandomForestClassifier
from ..analysis.indicators import TechnicalIndicators
import time
from ..trading.paper_trading import PaperTrading  # Adiciona import
from ..utils.config import config
from sklearn.model_selection import cross_val_score

class TradingBot:
    def __init__(self):
        self.current_signals = []
        self.trade_history = []
        self.signal_performance = {}
        self.pattern_memory = {}
        self.min_signals = 3
        self.min_win_rate = 0.5
        self.learning_cycles = 0
        self.last_trades = []  # Últimos trades para análise
        self.current_position = None
        self.entry_signals = None
        
    def analyze_market(self, market_data):
        """Analisa mercado e gera sinais"""
        self.current_signals = []
        
        # Análise técnica básica
        if self.check_macd(market_data):
            self.current_signals.append('MACD_POSITIVO' if market_data['macd'] > 0 else 'MACD_NEGATIVO')
            
        if self.check_trend(market_data):
            self.current_signals.append('TENDENCIA_ALTA' if market_data['trend'] > 0 else 'TENDENCIA_BAIXA')
            
        if self.check_rsi(market_data):
            if market_data['rsi'] > 70:
                self.current_signals.append('RSI_SOBRECOMPRA')
            elif market_data['rsi'] < 30:
                self.current_signals.append('RSI_SOBREVENDA')
                
        if self.check_bollinger(market_data):
            if market_data['price'] > market_data['bb_high']:
                self.current_signals.append('BB_ALTO')
            elif market_data['price'] < market_data['bb_low']:
                self.current_signals.append('BB_BAIXO')
                
        if market_data['volume'] > market_data['avg_volume'] * 1.5:
            self.current_signals.append('VOLUME_ALTO')
            
    def identify_pattern(self, signals):
        """Cria uma assinatura única do padrão"""
        return frozenset(sorted(signals))
        
    def update_pattern_memory(self, pattern, result):
        """Atualiza memória com resultado do padrão"""
        if pattern not in self.pattern_memory:
            self.pattern_memory[pattern] = {
                'wins': 0,
                'losses': 0,
                'consecutive_losses': 0,
                'last_results': []
            }
            
        stats = self.pattern_memory[pattern]
        if result > 0:
            stats['wins'] += 1
            stats['consecutive_losses'] = 0
        else:
            stats['losses'] += 1
            stats['consecutive_losses'] += 1
            
        stats['last_results'].append(result)
        if len(stats['last_results']) > 5:
            stats['last_results'].pop(0)
            
    def get_pattern_stats(self, pattern):
        """Analisa estatísticas do padrão"""
        if pattern not in self.pattern_memory:
            return 0, 0, True  # win_rate, avg_profit, is_new
            
        mem = self.pattern_memory[pattern]
        total = mem['wins'] + mem['losses']
        
        if total == 0:
            return 0, 0, True
            
        win_rate = mem['wins'] / total
        avg_profit = sum(mem['last_results']) / len(mem['last_results']) if mem['last_results'] else 0
        
        return win_rate, avg_profit, False
        
    def execute_trade(self, market_data):
        """Executa a lógica de trading"""
        if self.current_position:
            profit = self.calculate_profit(market_data['price'])
            pattern = self.identify_pattern(self.entry_signals)
            self.update_pattern_memory(pattern, profit)
            return self.close_position(market_data)
            
        should_trade = self.should_execute_trade()
        print(f"Should trade? {should_trade}")
        
        if should_trade:
            self.entry_signals = self.current_signals.copy()
            return self.open_position(market_data)
            
        return False
        
    def get_trade_direction(self):
        """Determina direção baseada no histórico"""
        if not self.current_pattern:
            return 'NEUTRO'
            
        if self.current_pattern in self.pattern_history:
            hist = self.pattern_history[self.current_pattern]
            if hist['total_profit'] > 0:
                return 'ALTA' if 'TENDENCIA_ALTA' in self.current_signals else 'BAIXA'
                
        return 'NEUTRO'
        
    def close_position(self, market_data):
        """Fecha posição atual"""
        if self.current_position:
            profit = self.calculate_profit(market_data['price'])
            self.update_performance(self.current_signals, profit)
            self.trade_history.append({
                'direction': self.current_position,
                'signals': self.current_signals.copy(),
                'profit': profit
            })
            self.current_position = None
            self.entry_signals = None
            return True
        return False
        
    def calculate_profit(self, current_price):
        """Calcula lucro/prejuízo do trade"""
        if self.current_position == 'ALTA':
            return ((current_price - self.entry_price) / self.entry_price) * 100
        elif self.current_position == 'BAIXA':
            return ((self.entry_price - current_price) / self.entry_price) * 100
        return 0
        
    def should_execute_trade(self):
        """Verifica se deve executar trade baseado nos critérios"""
        print(f"Verificando trade - Sinais: {len(self.current_signals)} (min: {self.min_signals})")
        
        if len(self.current_signals) < self.min_signals:
            print("Trade rejeitado: número insuficiente de sinais")
            return False
            
        pattern = self.identify_pattern(self.current_signals)
        if pattern in self.pattern_memory:
            stats = self.pattern_memory[pattern]
            total_trades = stats['wins'] + stats['losses']
            
            if total_trades >= 3:
                win_rate = stats['wins'] / total_trades
                print(f"Padrão conhecido - Win Rate: {win_rate:.2f}")
                if win_rate < self.min_win_rate:
                    print("Trade rejeitado: win rate abaixo do mínimo")
                    return False
                    
                if stats['consecutive_losses'] >= 2:
                    print("Trade rejeitado: muitas perdas consecutivas")
                    return False
                    
        print("Trade aprovado")
        return True
        
    def calculate_real_probability(self):
        """Probabilidade real baseada nos win rates"""
        prob = 0.5  # Começa com 50%
        for signal in self.current_signals:
            if signal in self.signal_performance:
                prob *= self.signal_performance[signal]['weight']
        return round(prob, 4)
        
    def update_performance(self, signals, profit):
        """Atualiza performance dos sinais após cada trade"""
        is_win = profit > 0
        for signal in signals:
            self.signal_performance[signal]['total'] += 1
            if is_win:
                self.signal_performance[signal]['wins'] += 1
            
            # Ajusta peso baseado no resultado
            win_rate = self.signal_performance[signal]['wins'] / self.signal_performance[signal]['total']
            self.signal_performance[signal]['weight'] = (win_rate * 2)  # Peso entre 0 e 2
            
        # Ajusta score mínimo baseado na performance geral
        self.adjust_min_score()

    def calculate_trade_score(self, signals):
        """Calcula score do trade baseado nos pesos dos sinais"""
        score = 0
        for signal in signals:
            weight = self.signal_performance[signal]['weight']
            score += weight
        return score / len(signals)

    def adjust_min_score(self):
        """Ajusta score mínimo baseado na performance geral"""
        total_trades = sum(s['total'] for s in self.signal_performance.values())
        if total_trades > 50:  # Começa a ajustar após 50 trades
            total_wins = sum(s['wins'] for s in self.signal_performance.values())
            win_rate = total_wins / total_trades
            self.min_trade_score = 1.5 + (win_rate * 0.5)  # Ajusta entre 1.5 e 2.0