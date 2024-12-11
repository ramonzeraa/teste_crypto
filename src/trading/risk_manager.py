import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

class RiskManager:
    def __init__(self, config: Dict):
        self.logger = logging.getLogger('risk_manager')
        self.config = config
        self.positions = {}
        self.daily_stats = {
            'trades': 0,
            'profit_loss': 0.0,
            'wins': 0,
            'losses': 0
        }
        self.reset_time = datetime.now() + timedelta(days=1)
        
    def can_trade(self) -> bool:
        """Verifica se pode realizar trade baseado em regras de risco"""
        try:
            # Reseta estatísticas diárias se necessário
            self._check_daily_reset()
            
            # Verifica número máximo de trades diários
            if self.daily_stats['trades'] >= self.config['max_daily_trades']:
                self.logger.warning("Máximo de trades diários atingido")
                return False
                
            # Verifica drawdown máximo
            if self.daily_stats['profit_loss'] <= -self.config['max_daily_drawdown']:
                self.logger.warning("Drawdown máximo diário atingido")
                return False
                
            # Verifica exposição total
            total_exposure = sum(pos['value'] for pos in self.positions.values())
            if total_exposure >= self.config['max_total_exposure']:
                self.logger.warning("Exposição máxima atingida")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar regras de risco: {str(e)}")
            return False
            
    def calculate_position_size(self, symbol: str) -> float:
        """Calcula tamanho da posição baseado em risco"""
        try:
            # Pega capital disponível
            available_capital = self.config['capital'] * (1 - self.config['reserve_ratio'])
            
            # Calcula risco por trade
            risk_per_trade = available_capital * self.config['risk_per_trade']
            
            # Ajusta baseado em volatilidade e momento
            volatility_factor = self._calculate_volatility_factor(symbol)
            momentum_factor = self._calculate_momentum_factor(symbol)
            
            position_size = risk_per_trade * volatility_factor * momentum_factor
            
            # Aplica limites
            position_size = min(
                position_size,
                self.config['max_position_size'],
                available_capital * self.config['max_position_ratio']
            )
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular tamanho da posição: {str(e)}")
            return 0.0
            
    def update_position(self, symbol: str, order_data: Dict):
        """Atualiza dados de posição após ordem"""
        try:
            if order_data['status'] == 'FILLED':
                self.positions[symbol] = {
                    'entry_price': float(order_data['price']),
                    'quantity': float(order_data['quantity']),
                    'value': float(order_data['price']) * float(order_data['quantity']),
                    'side': order_data['side'],
                    'entry_time': datetime.now()
                }
                self.daily_stats['trades'] += 1
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar posição: {str(e)}")
            
    def _check_daily_reset(self):
        """Reseta estatísticas diárias se necessário"""
        if datetime.now() >= self.reset_time:
            self.daily_stats = {
                'trades': 0,
                'profit_loss': 0.0,
                'wins': 0,
                'losses': 0
            }
            self.reset_time = datetime.now() + timedelta(days=1)
            
    def _calculate_volatility_factor(self, symbol: str) -> float:
        """Calcula fator de ajuste baseado em volatilidade"""
        # Implementar cálculo de volatilidade
        return 1.0
        
    def _calculate_momentum_factor(self, symbol: str) -> float:
        """Calcula fator de ajuste baseado em momento"""
        # Implementar cálculo de momento
        return 1.0

    def update_risk_metrics(self, positions: Dict, market_data: Dict) -> None:
        """Atualiza métricas de risco"""
        try:
            # Atualiza posições
            self.positions = positions
            
            # Calcula métricas
            risk_metrics = {
                'total_exposure': sum(pos['value'] for pos in positions.values()),
                'daily_trades': self.daily_stats['trades'],
                'daily_pnl': self.daily_stats['profit_loss'],
                'win_rate': self._calculate_win_rate(),
                'risk_score': self._calculate_risk_score(market_data)
            }
            
            self.current_metrics = risk_metrics
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar métricas: {str(e)}")

    def _calculate_win_rate(self) -> float:
        """Calcula taxa de acerto"""
        total = self.daily_stats['wins'] + self.daily_stats['losses']
        if total == 0:
            return 0.0
        return self.daily_stats['wins'] / total

    def _calculate_risk_score(self, market_data: Dict) -> float:
        """Calcula score de risco"""
        try:
            # Fatores de risco
            exposure_risk = sum(pos['value'] for pos in self.positions.values()) / self.config['capital']
            trade_risk = self.daily_stats['trades'] / self.config['max_daily_trades']
            
            # Peso dos fatores
            risk_score = (
                exposure_risk * 0.4 +  # 40% peso
                trade_risk * 0.3 +     # 30% peso
                (1 - self._calculate_win_rate()) * 0.3  # 30% peso
            )
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular score de risco: {str(e)}")
            return 1.0  # Retorna risco máximo em caso de erro