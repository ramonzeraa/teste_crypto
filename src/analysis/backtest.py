from datetime import datetime, timedelta
import logging
from src.utils.config import config
from src.core.crypto_bot import CryptoTradingBot
import time
import pandas as pd

class Backtest:
    def __init__(self, start_date=None, end_date=None, initial_balance=10000):
        self.bot = CryptoTradingBot()
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trades = []
        self.start_date = start_date or (datetime.now() - timedelta(days=30))
        self.end_date = end_date or datetime.now()
        self.config = config
        self.pattern_memory = {}  # Inicializa memória de padrões

    def should_trade(self, analysis):
        """Verifica se deve executar trade baseado na análise"""
        try:
            self.bot.current_signals = analysis['signals']
            should_execute = self.bot.should_execute_trade()
            
            if should_execute:
                # Identifica o padrão antes do trade
                pattern = self.bot.identify_pattern(analysis['signals'])
                
                # Executa o trade
                trade_result = self.execute_trade(analysis)
                
                # Atualiza a memória com o resultado
                if trade_result:
                    profit = trade_result['profit_percent']
                    self.bot.update_pattern_memory(pattern, profit)
                    
            return should_execute
            
        except Exception as e:
            logging.error(f"Erro ao verificar trade: {str(e)}")
            return False

    def execute_trade(self, analysis, current_candle, next_candle):
        """Executa um trade baseado na análise e nos candles"""
        try:
            direction = analysis['direction']
            signals = analysis.get('signals', [])
            
            # Usa preços reais dos candles
            entry_price = float(current_candle['close'])
            exit_price = float(next_candle['close'])
            
            # Calcula resultado baseado na direção
            if direction == "ALTA":
                profit_percent = (exit_price - entry_price) / entry_price
            elif direction == "BAIXA":
                profit_percent = (entry_price - exit_price) / entry_price
            else:
                return None
                
            # Calcula resultado financeiro
            position_size = self.balance * 0.01  # 1% do saldo
            profit_loss = position_size * profit_percent
            
            # Atualiza saldo
            self.balance += profit_loss
            
            # Atualiza memória de padrões do bot
            pattern = self.bot.identify_pattern(signals)
            self.bot.update_pattern_memory(pattern, profit_loss > 0)
            
            trade = {
                'direction': direction,
                'signals': signals,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'profit_loss': profit_loss,
                'profit_percent': profit_percent * 100,
                'position_size': position_size,
                'timestamp': pd.to_datetime(current_candle.name)
            }
            
            print(f"\nTrade Executado:")
            print(f"Direção: {direction}")
            print(f"Sinais: {signals}")
            print(f"Entrada: ${entry_price:.2f}")
            print(f"Saída: ${exit_price:.2f}")
            print(f"Lucro/Prejuízo: ${profit_loss:.2f} ({profit_percent*100:.2f}%)")
            
            return trade
            
        except Exception as e:
            logging.error(f"Erro ao executar trade: {e}")
            return None

    def print_results(self, partial=False):
        """Mostra resultados do backtesting"""
        if not self.trades:
            print("\n⚠️ Nenhum trade executado no período")
            return
            
        total_trades = len(self.trades)
        profitable_trades = sum(1 for t in self.trades if t['profit_loss'] > 0)
        win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
        total_profit = self.balance - self.initial_balance
        profit_percent = (total_profit / self.initial_balance) * 100
        
        if partial:
            print("\n=== Resultados Parciais ===")
        else:
            print("\n=== Resultados Finais ===")
            
        print(f"Total de Trades: {total_trades}")
        print(f"Trades Lucrativos: {profitable_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Lucro Total: ${total_profit:,.2f} ({profit_percent:,.2f}%)")
        print(f"Saldo Atual: ${self.balance:,.2f}")

    def analyze_results(self):
        """Analisa resultados dos trades"""
        if not self.trades:
            return
            
        # Análise por tipo de sinal
        signal_stats = {}
        for trade in self.trades:
            for signal in trade['signals']:
                if signal not in signal_stats:
                    signal_stats[signal] = {
                        'total': 0,
                        'wins': 0,
                        'losses': 0,
                        'profit': 0
                    }
                signal_stats[signal]['total'] += 1
                if trade['profit_loss'] > 0:
                    signal_stats[signal]['wins'] += 1
                else:
                    signal_stats[signal]['losses'] += 1
                signal_stats[signal]['profit'] += trade['profit_loss']
                
        print("\n=== Análise por Sinal ===")
        for signal, stats in signal_stats.items():
            win_rate = (stats['wins'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"\n{signal}:")
            print(f"Total: {stats['total']}")
            print(f"Win Rate: {win_rate:.2f}%")
            print(f"Lucro Total: ${stats['profit']:.2f}")

    def run(self):
        """Executa o backtesting"""
        try:
            print("\n=== Iniciando Backtesting ===")
            print(f"Período: {self.start_date.date()} até {self.end_date.date()}")
            print(f"Saldo Inicial: ${self.initial_balance:,.2f}")
            print("Carregando dados históricos...")
            
            data = self.bot.get_historical_data(
                start_date=self.start_date,
                end_date=self.end_date,
                interval=self.config.TIMEFRAMES['1h']
            )
            
            if data is None or len(data) < 100:
                raise ValueError("Dados históricos insuficientes")
                
            print(f"Dados carregados: {len(data)} períodos")
            print("\nAnalisando mercado...")
            
            trade_count = 0
            for i in range(len(data)-1):
                current_slice = data.iloc[:i+1].copy()
                next_candle = data.iloc[i+1]
                
                analysis = self.bot.analyze_market_historical(current_slice)
                
                if self.should_trade(analysis):
                    trade = self.execute_trade(analysis, current_slice.iloc[-1], next_candle)
                    if trade:
                        self.trades.append(trade)
                        trade_count += 1
                        
                    if trade_count % 10 == 0:
                        self.print_results(partial=True)
                    
            self.print_results()
            self.analyze_results()
            
        except KeyboardInterrupt:
            print("\n\nBacktesting interrompido pelo usuário!")
            self.print_results()
            
        except Exception as e:
            logging.error(f"Erro no backtesting: {str(e)}")
            print(f"\n❌ Erro durante backtesting: {str(e)}")