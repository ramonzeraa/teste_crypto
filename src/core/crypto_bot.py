"""
Bot principal do sistema de trading
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging
import pandas as pd

from ..analysis.market_analysis import MarketAnalysis
from ..trading.risk_management import RiskManagement
from ..data.loader import DataLoader
from ..utils.config import Config

class CryptoBot:
    def __init__(self):
        """Inicializa o bot com suas configurações e dependências"""
        self.config = Config()
        self.market_analysis = MarketAnalysis()
        self.risk_manager = RiskManagement()
        self.data_loader = DataLoader()
        
        # Bot state
        self.is_active = False
        self.current_position = None
        self.last_analysis = None
        self.last_update = None
        
        # Logging setup
        self.setup_logging()
        
    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='logs/crypto_bot.log'
        )
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Inicia a operação do bot"""
        self.logger.info("Iniciando CryptoBot...")
        self.is_active = True
        self.run_main_loop()
        
    def stop(self):
        """Para a operação do bot"""
        self.logger.info("Parando CryptoBot...")
        self.is_active = False
    
    def run_main_loop(self):
        """Loop principal de execução do bot"""
        while self.is_active:
            try:
                # 1. Atualizar dados do mercado
                market_data = self.data_loader.get_latest_data()
                
                # 2. Realizar análise
                analysis_result = self.market_analysis.analyze(market_data)
                self.last_analysis = analysis_result
                
                # 3. Verificar condições de risco
                risk_status = self.risk_manager.check_risk_levels()
                
                # 4. Executar estratégia se permitido
                if risk_status['can_trade']:
                    self.execute_strategy(analysis_result)
                
                # 5. Monitorar posições
                self.monitor_positions()
                
                self.last_update = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {str(e)}")
                self.stop()
    
    def execute_strategy(self, analysis: Dict):
        """Executa a estratégia de trading baseada na análise"""
        try:
            if self.current_position is None:
                # Verifica sinais de entrada
                if analysis['signal'] == 'BUY':
                    self.logger.info("Sinal de compra detectado...")
                    self.open_position('BUY', analysis['price'])
                    
            else:
                # Verifica sinais de saída
                if analysis['signal'] == 'SELL':
                    self.logger.info("Sinal de venda detectado...")
                    self.close_position(analysis['price'])
                    
        except Exception as e:
            self.logger.error(f"Erro ao executar estratégia: {str(e)}")
    
    def monitor_positions(self):
        """Monitora posições abertas"""
        if self.current_position:
            try:
                position_status = self.risk_manager.check_position(
                    self.current_position
                )
                
                if position_status['should_close']:
                    self.logger.info(
                        f"Fechando posição: {position_status['reason']}"
                    )
                    self.close_position()
                    
            except Exception as e:
                self.logger.error(f"Erro ao monitorar posições: {str(e)}")
    
    def open_position(self, side: str, price: float):
        """Abre uma nova posição de trading"""
        try:
            position_size = self.risk_manager.calculate_position_size()
            
            self.current_position = {
                'side': side,
                'entry_price': price,
                'size': position_size,
                'timestamp': datetime.now(),
                'stop_loss': self.risk_manager.calculate_stop_loss(side, price),
                'take_profit': self.risk_manager.calculate_take_profit(side, price)
            }
            
            self.logger.info(
                f"Posição aberta: {side} | Preço: {price} | Tamanho: {position_size}"
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao abrir posição: {str(e)}")
    
    def close_position(self, price: float = None):
        """Fecha a posição atual"""
        try:
            if self.current_position:
                result = {
                    'side': self.current_position['side'],
                    'entry_price': self.current_position['entry_price'],
                    'exit_price': price,
                    'size': self.current_position['size'],
                    'pnl': self.calculate_pnl(price)
                }
                
                self.logger.info(
                    f"Posição fechada | P&L: {result['pnl']}"
                )
                
                self.current_position = None
                return result
                
        except Exception as e:
            self.logger.error(f"Erro ao fechar posição: {str(e)}")
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calcula o P&L da posição atual"""
        if not self.current_position:
            return 0.0
            
        entry = self.current_position['entry_price']
        size = self.current_position['size']
        
        if self.current_position['side'] == 'BUY':
            return (current_price - entry) * size
        else:
            return (entry - current_price) * size
    
    def get_bot_status(self) -> Dict:
        """Retorna o status atual do bot"""
        return {
            'is_active': self.is_active,
            'current_position': self.current_position,
            'last_analysis': self.last_analysis,
            'last_update': self.last_update,
            'risk_status': self.risk_manager.get_risk_status()
        }
    
    def update_config(self, new_config: Dict):
        """Atualiza configurações do bot"""
        try:
            self.config.update(new_config)
            self.logger.info("Configurações atualizadas com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar configurações: {str(e)}")
    
    def validate_state(self) -> bool:
        """Valida o estado atual do bot"""
        try:
            # Verifica conexões
            self.data_loader.check_connection()
            
            # Verifica configurações
            if not self.config.is_valid():
                raise ValueError("Configurações inválidas")
                
            # Verifica estado do risco
            if not self.risk_manager.is_healthy():
                raise ValueError("Estado de risco não saudável")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Validação de estado falhou: {str(e)}")
            return False

