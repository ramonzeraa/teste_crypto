"""
Sistema de Logging Personalizado
"""
import logging
import os
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

class TradingLogger:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Configura sistema de logging"""
        # Cria diretório de logs se não existir
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Nome do arquivo baseado na data
        log_file = log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configura formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler para arquivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configura logger root
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler) 
    
    def log_trade(self, trade_data: Dict):
        """Registra informações de trade"""
        try:
            trade_type = trade_data.get('type', 'UNKNOWN').upper()
            symbol = trade_data.get('symbol', 'UNKNOWN')
            price = trade_data.get('price', 0)
            
            message = (
                f"TRADE {trade_type} | "
                f"Symbol: {symbol} | "
                f"Price: {price} | "
                f"PnL: {trade_data.get('pnl', 0):.2f}"
            )
            
            self.logger.info(message)
            
            # Log detalhado em arquivo separado
            self._log_trade_details(trade_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar trade: {str(e)}")
    
    def log_error(self, error: Exception, context: str = None):
        """Registra erros do sistema"""
        try:
            message = f"ERRO: {str(error)}"
            if context:
                message = f"{context} | {message}"
            
            self.logger.error(message, exc_info=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar erro: {str(e)}")
    
    def log_strategy(self, strategy_data: Dict):
        """Registra sinais e análises da estratégia"""
        try:
            message = (
                f"STRATEGY | "
                f"Signal: {strategy_data.get('signal')} | "
                f"Indicators: {strategy_data.get('indicators', {})} | "
                f"Confidence: {strategy_data.get('confidence', 0):.2f}"
            )
            
            self.logger.info(message)
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar estratégia: {str(e)}")
    
    def _log_trade_details(self, trade_data: Dict):
        """Registra detalhes do trade em arquivo separado"""
        try:
            log_dir = Path('logs/trades')
            log_dir.mkdir(exist_ok=True)
            
            # Arquivo específico para trades
            trade_log = log_dir / f"trades_{datetime.now().strftime('%Y%m')}.log"
            
            # Formata detalhes do trade
            details = [
                f"Timestamp: {datetime.now()}",
                f"Type: {trade_data.get('type')}",
                f"Symbol: {trade_data.get('symbol')}",
                f"Price: {trade_data.get('price')}",
                f"Size: {trade_data.get('size')}",
                f"PnL: {trade_data.get('pnl', 0):.2f}",
                f"Stop Loss: {trade_data.get('stop_loss')}",
                f"Take Profit: {trade_data.get('take_profit')}",
                f"Strategy: {trade_data.get('strategy')}",
                "-------------------"
            ]
            
            # Append ao arquivo
            with open(trade_log, 'a') as f:
                f.write('\n'.join(details) + '\n')
                
        except Exception as e:
            self.logger.error(f"Erro ao registrar detalhes do trade: {str(e)}")
    
    def rotate_logs(self, max_days: int = 30):
        """Remove logs antigos"""
        try:
            log_dir = Path('logs')
            current_date = datetime.now()
            
            for log_file in log_dir.glob('*.log'):
                file_date_str = log_file.stem.split('_')[1]
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                
                # Remove logs mais antigos que max_days
                if (current_date - file_date).days > max_days:
                    log_file.unlink()
                    
        except Exception as e:
            self.logger.error(f"Erro ao rotacionar logs: {str(e)}")