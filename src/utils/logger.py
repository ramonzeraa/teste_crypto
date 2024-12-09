import logging
import logging.handlers
from datetime import datetime
import os
from typing import Optional
import json
from pathlib import Path

class CustomLogger:
    def __init__(self, name: str = "trading_bot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Cria diretórios de log
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Log geral
        general_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "bot.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        general_handler.setLevel(logging.INFO)
        
        # Log de trades
        trade_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "trades.log",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        trade_handler.setLevel(logging.INFO)
        
        # Log de erros
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "errors.log",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Formatadores
        general_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        trade_formatter = logging.Formatter(
            '%(asctime)s - %(message)s'
        )
        
        error_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d\n%(message)s\n'
        )
        
        # Aplica formatadores
        general_handler.setFormatter(general_formatter)
        trade_handler.setFormatter(trade_formatter)
        error_handler.setFormatter(error_formatter)
        
        # Adiciona handlers
        self.logger.addHandler(general_handler)
        self.logger.addHandler(trade_handler)
        self.logger.addHandler(error_handler)
        
        # Handler específico para trades
        self.trade_logger = logging.getLogger(f"{name}.trades")
        self.trade_logger.addHandler(trade_handler)
    
    def log_trade(self, trade_data: dict):
        """Registra informações de trade"""
        try:
            trade_info = json.dumps(trade_data)
            self.trade_logger.info(trade_info)
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar trade: {e}")
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """Registra erros com contexto"""
        try:
            error_msg = f"Erro: {str(error)}"
            if context:
                error_msg = f"Contexto: {context}\n{error_msg}"
            
            self.logger.error(error_msg, exc_info=True)
            
        except Exception as e:
            print(f"Erro crítico no logger: {e}")
    
    def log_performance(self, metrics: dict):
        """Registra métricas de performance"""
        try:
            performance_info = json.dumps(metrics)
            self.logger.info(f"Performance: {performance_info}")
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar performance: {e}")
