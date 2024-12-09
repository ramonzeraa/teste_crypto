import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Trade:
    symbol: str
    side: str  # "BUY" ou "SELL"
    quantity: float
    price: float
    timestamp: datetime = field(default_factory=datetime.now)
    pnl: float = 0.0
    status: str = "OPEN"

class PaperTrading:
    def __init__(self):
        self.trades: List[Trade] = []
        self.balance = 10000.0  # Saldo inicial em USDT
        self.positions: Dict[str, float] = {}  # Posições abertas
        
    def execute_trade(self, symbol: str, side: str, quantity: float, price: float) -> Trade:
        """Executa trade simulado"""
        try:
            # Calcula valor do trade
            trade_value = quantity * price
            
            # Verifica saldo
            if side == "BUY" and trade_value > self.balance:
                raise ValueError(f"Saldo insuficiente: {self.balance} USDT")
            
            # Cria trade
            trade = Trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price
            )
            
            # Atualiza saldo e posições
            if side == "BUY":
                self.balance -= trade_value
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity
            else:  # SELL
                self.balance += trade_value
                self.positions[symbol] = self.positions.get(symbol, 0) - quantity
            
            # Registra trade
            self.trades.append(trade)
            
            logging.info(f"Trade executado: {side} {quantity} {symbol} @ {price}")
            logging.info(f"Saldo atual: {self.balance:.2f} USDT")
            
            return trade
            
        except Exception as e:
            logging.error(f"Erro ao executar trade: {e}")
            raise e
    
    def get_position(self, symbol: str) -> float:
        """Retorna quantidade em posição"""
        return self.positions.get(symbol, 0)
    
    def get_balance(self) -> float:
        """Retorna saldo disponível"""
        return self.balance
    
    def get_trades(self) -> List[Trade]:
        """Retorna histórico de trades"""
        return self.trades
    
    def close_trade(self, trade: Trade, close_price: float):
        """Fecha trade e calcula P&L"""
        if trade.status == "CLOSED":
            return
            
        # Calcula P&L
        if trade.side == "BUY":
            trade.pnl = (close_price - trade.price) * trade.quantity
        else:
            trade.pnl = (trade.price - close_price) * trade.quantity
            
        trade.status = "CLOSED"
        logging.info(f"Trade fechado - P&L: {trade.pnl:.2f} USDT")