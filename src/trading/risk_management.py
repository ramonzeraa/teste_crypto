from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy as np
from typing import Dict, Optional
import pandas as pd

@dataclass
class Position:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime

class RiskManager:
    def __init__(self, config):
        self.config = config
        self.max_daily_loss = config.MAX_DAILY_LOSS
        self.max_position_size = config.MAX_POSITION_SIZE
        self.current_daily_loss = 0
        self.open_positions = []
        self.daily_trades = []
        self.last_reset = datetime.now()
        
    def can_trade(self, symbol, side, quantity, price):
        """Verifica se pode abrir nova posição"""
        try:
            # Reset diário se necessário
            self._check_daily_reset()
            
            # Verifica limite diário de perda
            if self.current_daily_loss >= self.max_daily_loss:
                logging.warning("Limite diário de perda atingido")
                return False
                
            # Verifica número máximo de trades diários
            if len(self.daily_trades) >= self.config.MAX_DAILY_TRADES:
                logging.warning("Limite diário de trades atingido")
                return False
                
            # Verifica exposição total
            total_exposure = sum(p.quantity * p.entry_price for p in self.open_positions)
            new_exposure = quantity * price
            
            if (total_exposure + new_exposure) > self.max_position_size:
                logging.warning("Limite de exposição excedido")
                return False
                
            # Adicionar filtros de volatilidade
            if self.get_current_volatility() > self.max_volatility:
                return False
                
            # Adicionar proteção contra drawdown
            if self.current_drawdown > self.max_drawdown:
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Erro ao verificar regras de risco: {e}")
            return False
            
    def add_position(self, symbol, side, quantity, price, stop_loss, take_profit):
        """Adiciona nova posição"""
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now()
        )
        
        self.open_positions.append(position)
        self.daily_trades.append(position)
        
        return position
        
    def update_daily_loss(self, loss):
        """Atualiza perda diária"""
        self.current_daily_loss += loss
        
    def _check_daily_reset(self):
        """Reseta contadores diários se necessário"""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.current_daily_loss = 0
            self.daily_trades = []
            self.last_reset = now
            logging.info("Contadores diários resetados")

    def should_execute_trade(self, signals, market_data):
        """Filtros mais rigorosos"""
        # Mínimo de sinais
        if len(signals) < 3:
            return False
        
        # Probabilidade mínima
        if self.calculate_real_probability(signals, market_data) < 0.65:
            return False
        
        # Bloqueia sinais ruins
        bad_signals = ['RSI_SOBREVENDA', 'BB_BAIXO', 'TENDENCIA_BAIXA']
        if any(signal in signals for signal in bad_signals):
            return False
        
        # Requer sinais principais
        required = ['MACD_POSITIVO', 'TENDENCIA_ALTA']
        if not all(signal in signals for signal in required):
            return False
        
        return True

    def calculate_real_probability(self, signals, market_data):
        """Calcula probabilidade real baseada em sinais confirmados"""
        base_prob = 0.0
        
        # Pesos ajustados baseados na análise anterior
        signal_weights = {
            'MACD_POSITIVO': 0.20,
            'TENDENCIA_ALTA': 0.30,
            'RSI_SOBRECOMPRA': 0.15,
            'BB_ALTO': 0.15,
            'VOLUME_ALTO': 0.20
        }
        
        # Conta apenas sinais confirmados
        confirmed_signals = 0
        for signal in signals:
            if signal in signal_weights:
                base_prob += signal_weights[signal]
                confirmed_signals += 1
        
        # Requer mínimo de sinais
        if confirmed_signals < 3:
            return 0.0
        
        # Ajusta baseado na tendência
        if 'TENDENCIA_ALTA' in signals and 'MACD_POSITIVO' in signals:
            base_prob *= 1.2  # Bonus para tendência confirmada
        
        return min(round(base_prob, 2), 1.0)

    def optimize_trade_execution(self):
        """Otimização baseada na análise"""
        
        # Priorizar combinações lucrativas
        if self.has_winning_combination():
            self.increase_position_size()
        
        # Filtrar sinais ruins
        bad_signals = ['BB_BAIXO', 'RSI_SOBREVENDA']
        if any(signal in self.current_signals for signal in bad_signals):
            return False
        
        # Verificar condições de mercado
        if self.market_conditions == 'LATERAL':
            return False

class RiskManagement:
    def __init__(self):
        self.config = {
            'max_position_size': 0.02,  # 2% do capital
            'max_daily_loss': 0.05,     # 5% do capital
            'stop_loss_pct': 0.02,      # 2% stop loss
            'take_profit_pct': 0.04,    # 4% take profit
            'max_trades_day': 5,        # Máximo trades por dia
        }
        self.daily_stats = self.reset_daily_stats()
        
    def reset_daily_stats(self) -> Dict:
        """Reseta estatísticas diárias"""
        return {
            'trades_count': 0,
            'daily_pnl': 0.0,
            'last_reset': datetime.now(),
            'positions': []
        }
    
    def calculate_position_size(self, capital: float, price: float) -> float:
        """Calcula tamanho da posição baseado no risco"""
        try:
            risk_amount = capital * self.config['max_position_size']
            return risk_amount / price
            
        except Exception as e:
            raise Exception(f"Erro ao calcular position size: {str(e)}")
    
    def calculate_stop_loss(self, side: str, entry_price: float) -> float:
        """Calcula nível de stop loss"""
        try:
            if side == 'BUY':
                return entry_price * (1 - self.config['stop_loss_pct'])
            else:
                return entry_price * (1 + self.config['stop_loss_pct'])
                
        except Exception as e:
            raise Exception(f"Erro ao calcular stop loss: {str(e)}")
    
    def calculate_take_profit(self, side: str, entry_price: float) -> float:
        """Calcula nível de take profit"""
        try:
            if side == 'BUY':
                return entry_price * (1 + self.config['take_profit_pct'])
            else:
                return entry_price * (1 - self.config['take_profit_pct'])
                
        except Exception as e:
            raise Exception(f"Erro ao calcular take profit: {str(e)}")
    
    def check_risk_levels(self) -> Dict:
        """Verifica níveis de risco atuais"""
        try:
            # Verifica reset diário
            self._check_daily_reset()
            
            can_trade = True
            reasons = []
            
            # Verifica número máximo de trades
            if self.daily_stats['trades_count'] >= self.config['max_trades_day']:
                can_trade = False
                reasons.append("Limite diário de trades atingido")
            
            # Verifica perda máxima diária
            if abs(self.daily_stats['daily_pnl']) >= self.config['max_daily_loss']:
                can_trade = False
                reasons.append("Limite de perda diária atingido")
            
            return {
                'can_trade': can_trade,
                'reasons': reasons,
                'daily_stats': self.daily_stats
            }
            
        except Exception as e:
            raise Exception(f"Erro ao verificar níveis de risco: {str(e)}")
    
    def check_position(self, position: Dict) -> Dict:
        """Verifica status da posição atual"""
        try:
            current_price = position.get('current_price')
            if not current_price:
                return {'should_close': False, 'reason': None}
            
            should_close = False
            reason = None
            
            # Verifica Stop Loss
            if position['side'] == 'BUY':
                if current_price <= position['stop_loss']:
                    should_close = True
                    reason = "Stop Loss atingido"
                elif current_price >= position['take_profit']:
                    should_close = True
                    reason = "Take Profit atingido"
            else:  # SELL
                if current_price >= position['stop_loss']:
                    should_close = True
                    reason = "Stop Loss atingido"
                elif current_price <= position['take_profit']:
                    should_close = True
                    reason = "Take Profit atingido"
            
            return {
                'should_close': should_close,
                'reason': reason
            }
            
        except Exception as e:
            raise Exception(f"Erro ao verificar posição: {str(e)}")
    
    def update_stats(self, trade_result: Dict):
        """Atualiza estatísticas de trading"""
        try:
            self.daily_stats['trades_count'] += 1
            self.daily_stats['daily_pnl'] += trade_result.get('pnl', 0)
            self.daily_stats['positions'].append(trade_result)
            
        except Exception as e:
            raise Exception(f"Erro ao atualizar estatísticas: {str(e)}")
    
    def _check_daily_reset(self):
        """Verifica e executa reset diário se necessário"""
        now = datetime.now()
        last_reset = self.daily_stats['last_reset']
        
        if now.date() > last_reset.date():
            self.daily_stats = self.reset_daily_stats()
    
    def is_healthy(self) -> bool:
        """Verifica se o sistema está saudável para operar"""
        try:
            risk_check = self.check_risk_levels()
            return risk_check['can_trade']
            
        except Exception as e:
            return False