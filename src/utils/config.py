from binance.client import Client
from dotenv import load_dotenv
import os
from dataclasses import dataclass, field
from typing import List, Dict

# Carrega variáveis de ambiente
load_dotenv()

# Credenciais da API
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

def get_default_timeframes() -> Dict[str, str]:
    return {
        "1m": Client.KLINE_INTERVAL_1MINUTE,
        "5m": Client.KLINE_INTERVAL_5MINUTE,
        "15m": Client.KLINE_INTERVAL_15MINUTE,
        "1h": Client.KLINE_INTERVAL_1HOUR
    }

def get_default_ema_periods() -> tuple:
    return (20, 50)

@dataclass
class TradingConfig:
    # Configurações gerais
    SYMBOL: str = "BTCUSDT"
    UPDATE_INTERVAL: int = 30  # Reduzido para 30 segundos
    ERROR_WAIT_TIME: int = 15  # Reduzido para 15 segundos
    
    # Timeframes para análise
    TIMEFRAMES: Dict[str, str] = field(default_factory=get_default_timeframes)
    
    # Parâmetros de trading
    VALOR_ENTRADA: float = 100.0
    MIN_POSITION_SIZE: float = 0.001
    MAX_POSITION_SIZE: float = 0.1
    RISK_PER_TRADE: float = 0.02
    LEVERAGE: int = 1
    MAX_TRADES_PER_DAY: int = 10
    
    # Parâmetros de Stop Loss e Take Profit
    STOP_LOSS_PCT: float = 0.01      # 1% stop loss
    TAKE_PROFIT_PCT: float = 0.02    # 2% take profit
    STOP_LOSS: float = 0.015         # 1.5% stop loss alternativo
    TAKE_PROFIT: float = 0.03        # 3% take profit alternativo
    EMERGENCY_STOP_LOSS: float = 0.05 # 5% stop loss emergencial
    
    # Parâmetros técnicos
    RSI_PERIOD: int = 14
    RSI_OVERSOLD: int = 30
    RSI_OVERBOUGHT: int = 70
    VOLUME_THRESHOLD: float = 1.5
    ADX_THRESHOLD: int = 25
    EMA_PERIODS: tuple = field(default_factory=get_default_ema_periods)
    
    # Parâmetros da IA
    MIN_CONFIDENCE: float = 0.85
    MIN_PROBABILITY: float = 0.65
    MIN_CONSISTENCY: float = 0.60
    TRAIN_TEST_SPLIT: float = 0.8
    LOOKBACK_PERIOD: int = 200
    
    # Configurações de segurança
    ENABLE_SPOT_TRADING: bool = True
    ENABLE_MARGIN_TRADING: bool = False
    
    def __post_init__(self):
        # Validações
        if self.ENABLE_MARGIN_TRADING:
            raise ValueError("Trading com margem desabilitado por segurança")
        
        if self.MAX_POSITION_SIZE > 100.0:
            raise ValueError("Tamanho máximo da posição excede limite de segurança")

# Instância global das configurações
config = TradingConfig()

# Para manter compatibilidade com código existente
SYMBOL = config.SYMBOL
UPDATE_INTERVAL = config.UPDATE_INTERVAL
ERROR_WAIT_TIME = config.ERROR_WAIT_TIME
MIN_POSITION_SIZE = config.MIN_POSITION_SIZE
MAX_POSITION_SIZE = config.MAX_POSITION_SIZE
RISK_PER_TRADE = config.RISK_PER_TRADE
LEVERAGE = config.LEVERAGE
TIMEFRAMES = config.TIMEFRAMES
MIN_PROBABILITY = config.MIN_PROBABILITY
MIN_CONSISTENCY = config.MIN_CONSISTENCY
MAX_RSI = config.RSI_OVERBOUGHT
MIN_RSI = config.RSI_OVERSOLD
STOP_LOSS_PCT = config.STOP_LOSS
TAKE_PROFIT_PCT = config.TAKE_PROFIT