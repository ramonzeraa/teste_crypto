"""
Sistema de Logging
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class TradingLogger:
    def __init__(self):
        """Inicializa sistema de logging"""
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(logging.INFO)
        
        # Cria diretório de logs se não existir
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # Handler para arquivo
        self.setup_file_handler()
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
    
    def setup_file_handler(self):
        """Configura handler de arquivo"""
        try:
            # Remove handlers antigos de arquivo
            for handler in self.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    self.logger.removeHandler(handler)
            
            # Cria novo handler
            log_file = self.log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Erro ao configurar arquivo de log: {str(e)}")
            raise