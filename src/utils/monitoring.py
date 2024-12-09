from datetime import datetime
import pandas as pd
import numpy as np
import os

class TradingMonitor:
    def __init__(self):
        self.signals_history = []
        self.volatility_history = []
        self.trades_history = []
        self.current_trend = None
        self.trend_strength = 0
        
    def update_signals(self, timeframes_data, current_price):
        """Atualiza e analisa sinais"""
        signal = {
            'timestamp': datetime.now(),
            'price': current_price,
            'signals': timeframes_data,
            'volatility': self.calculate_volatility(timeframes_data)
        }
        
        self.signals_history.append(signal)
        self.update_trend(signal)
        self.log_signal(signal)
        
        return self.analyze_signal(signal)
        
    def calculate_volatility(self, timeframes_data):
        """Calcula índice de volatilidade"""
        probabilities = [tf['probability'] for tf in timeframes_data.values()]
        return {
            'std': np.std(probabilities),
            'range': max(probabilities) - min(probabilities),
            'consistency': self.check_signal_consistency(timeframes_data)
        }
        
    def check_signal_consistency(self, timeframes_data):
        """Verifica consistência entre timeframes"""
        directions = [tf['direction'] for tf in timeframes_data.values()]
        main_direction = max(set(directions), key=directions.count)
        agreement = directions.count(main_direction) / len(directions)
        return agreement
        
    def update_trend(self, signal):
        """Atualiza tendência atual"""
        new_trend = signal['signals']['1h']['direction']
        
        if self.current_trend != new_trend:
            self.trend_strength = 1
        else:
            self.trend_strength += 1
            
        self.current_trend = new_trend
        
    def analyze_signal(self, signal):
        """Análise completa do sinal"""
        volatility = signal['volatility']
        
        return {
            'should_trade': (
                volatility['consistency'] >= 0.75 and  # 75% concordância
                volatility['std'] < 0.15 and          # Baixa dispersão
                self.trend_strength >= 2              # Mínimo 2 ciclos
            ),
            'risk_factor': self.calculate_risk_factor(signal),
            'stop_multiplier': self.calculate_stop_multiplier(volatility),
            'confidence': self.calculate_confidence(signal)
        }
        
    def calculate_risk_factor(self, signal):
        """Calcula fator de risco dinâmico"""
        vol = signal['volatility']
        base_risk = 0.01  # 1% base
        
        risk_multiplier = (
            (vol['consistency'] * 1.2) *    # Maior consistência = maior risco
            (1 - vol['std'] * 2) *          # Menor dispersão = maior risco
            (min(self.trend_strength, 5) / 5)  # Força da tendência
        )
        
        return base_risk * risk_multiplier
        
    def calculate_stop_multiplier(self, volatility):
        """Calcula multiplicador de stop loss"""
        return 1 + (volatility['std'] * 2)  # Aumenta stop em volatilidade alta
        
    def calculate_confidence(self, signal):
        """Calcula confiança geral do sinal"""
        weights = {'1h': 0.4, '15m': 0.3, '5m': 0.2, '1m': 0.1}
        
        weighted_prob = sum(
            signal['signals'][tf]['probability'] * weights[tf]
            for tf in weights
        )
        
        confidence = weighted_prob * signal['volatility']['consistency']
        return confidence
        
    def log_signal(self, signal):
        """Registra sinal detalhado"""
        log_entry = {
            'timestamp': signal['timestamp'],
            'price': signal['price'],
            'direction_1h': signal['signals']['1h']['direction'],
            'prob_1h': signal['signals']['1h']['probability'],
            'consistency': signal['volatility']['consistency'],
            'volatility_std': signal['volatility']['std'],
            'trend_strength': self.trend_strength,
            'confidence': self.calculate_confidence(signal)
        }
        
        pd.DataFrame([log_entry]).to_csv(
            'logs/signals_log.csv',
            mode='a',
            header=not os.path.exists('logs/signals_log.csv')
        ) 