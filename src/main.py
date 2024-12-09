import logging
from datetime import datetime, timedelta
import time
import random
from .core.crypto_bot import CryptoTradingBot
from .utils.config import TradingConfig, config
from .trading.paper_trading import PaperTrading
from .utils.monitoring import TradingMonitor
from .trading.validation import TradingValidator
from .core.market_expert import MarketExpert
from .analysis.backtest import Backtest
from .core.live_simulator import LiveSimulator

def countdown(seconds):
    """Mostra contagem regressiva"""
    for i in range(seconds, 0, -1):
        print(f"\rPróxima atualização em {i} segundos...", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 50 + "\r", end="")  # Limpa a linha

def main():
    config = config()
    bot = CryptoTradingBot(config)  # Cria o bot primeiro
    
    print("\n1. Executar Bot em Tempo Real")
    print("2. Executar Backtesting")
    print("3. Executar Simulador com Aprendizado")
    
    choice = input("\nEscolha uma opção (1-3): ")
    
    if choice == "3":
        simulator = LiveSimulator(bot, config)  # Passa bot e config
        simulator.run_simulation()

def print_analysis(analysis):
    """Imprime análise de forma mais amigável"""
    if not analysis:
        print("\n❌ Erro ao obter análise do mercado")
        return
        
    rt = analysis['real_time']
    pred = analysis['predictions']
    ind = analysis['indicators']
    
    print("\n" + "="*50)
    print("🔍 ANÁLISE DE MERCADO BITCOIN")
    print("="*50)
    
    # Preço e variações
    print(f"\n💰 Preço Atual: ${rt['current_price']:,.2f}")
    dist_max = ((rt['historical_high'] - rt['current_price'])/rt['current_price'])*100
    print(f"📊 Máxima Histórica: ${rt['historical_high']:,.2f} ({dist_max:.1f}% distante)")
    
    # Volume
    print(f"\n📈 Volume 24h: {rt['volume_24h']:,.0f} BTC")
    print(f"🔄 Trades 24h: {rt['trades_24h']:,}")
    
    # Indicadores
    print(f"\n📉 INDICADORES TÉCNICOS:")
    print(f"RSI: {ind['rsi']:.1f} ({'Sobrecomprado' if ind['rsi']>70 else 'Sobrevendido' if ind['rsi']<30 else 'Neutro'})")
    print(f"MACD: {ind['macd']:.2f}")
    
    # Previsões
    print(f"\n🔮 PREVISÕES POR TIMEFRAME:")
    print("  Curto Prazo:")
    print(f"    1min: {pred['1m']['direction']} ({pred['1m']['probability']:.1%})")
    print(f"    5min: {pred['5m']['direction']} ({pred['5m']['probability']:.1%})")
    print("  Médio/Longo Prazo:")
    print(f"    15min: {pred['15m']['direction']} ({pred['15m']['probability']:.1%})")
    print(f"    1hora: {pred['1h']['direction']} ({pred['1h']['probability']:.1%})")
    
    # Recomendação
    print("\n⚡ RECOMENDAÇÃO:")
    confidence = sum(p['probability'] for p in pred.values()) / len(pred)
    if confidence < 0.5:
        print("🔸 AGUARDAR - Baixa confiança nas previsões")
    elif all(p['direction'] == "ALTA" for p in pred.values()):
        print("🟢 COMPRA - Tendência de alta em todos os timeframes")
    elif all(p['direction'] == "BAIXA" for p in pred.values()):
        print("🔴 VENDA - Tendência de baixa em todos os timeframes")
    else:
        print("🟡 NEUTRO - Sinais mistos entre timeframes")
    
    print("\n" + "="*50)

def run_backtest_analysis():
    """Executa análise de backtesting"""
    # Define período
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # últimos 30 dias
    
    # Executa backtesting
    backtest = Backtest(
        start_date=start_date,
        end_date=end_date,
        initial_balance=10000  # $10k inicial
    )
    
    backtest.run()

def run_real_time_bot():
    """Executa o bot em tempo real"""
    try:
        bot = CryptoTradingBot()
        initial_balance = 10000.0
        current_balance = initial_balance
        trades = []
        
        print("\n=== Bot Iniciado em Tempo Real ===")
        print(f"Saldo Inicial: ${initial_balance:,.2f}")
        print(f"Par: {config.SYMBOL}")
        print(f"Timeframe: {config.TIMEFRAMES['1h']}")
        print("\nMonitorando mercado...")
        
        while True:
            try:
                # Obtém dados mais recentes
                data = bot.get_historical_data(
                    symbol=config.SYMBOL,
                    interval=config.TIMEFRAMES['1h'],
                    limit=100
                )
                
                if data is None:
                    print("⚠️ Aguardando dados do mercado...")
                    time.sleep(5)
                    continue
                
                # Analisa mercado
                analysis = bot.analyze_market_real_time(data)
                
                if analysis:
                    direction = analysis.get('direction', 'NEUTRO')
                    probability = analysis.get('probability', 0)
                    signals = analysis.get('indicators', {}).get('signals', [])
                    current_price = analysis['indicators']['current_price']
                    
                    # Mostra análise em tempo real
                    print("\n" + "="*50)
                    print(f"📊 Análise em Tempo Real - {datetime.now().strftime('%H:%M:%S')}")
                    print(f"Preço Atual: ${current_price:,.2f}")
                    print(f"Direção: {direction}")
                    print(f"Probabilidade: {probability:.2f}")
                    print(f"Sinais Ativos: {[s['type'] for s in signals]}")
                    
                    # Verifica condições para trade
                    if should_trade(analysis):
                        trade = execute_real_trade(analysis, current_balance)
                        if trade:
                            trades.append(trade)
                            current_balance = trade['new_balance']
                            
                            # Mostra resultado do trade
                            print("\n🔄 Trade Executado:")
                            print(f"Entrada: ${trade['entry_price']:,.2f}")
                            print(f"Direção: {trade['direction']}")
                            print(f"Lucro/Prejuízo: ${trade['profit_loss']:,.2f}")
                            print(f"Saldo Atual: ${current_balance:,.2f}")
                    
                # Mostra estatísticas a cada 10 trades
                if len(trades) % 10 == 0 and trades:
                    show_statistics(trades, initial_balance, current_balance)
                
                # Aguarda próxima análise
                time.sleep(10)  # Ajuste esse tempo conforme necessário
                
            except KeyboardInterrupt:
                print("\n\n🛑 Bot interrompido pelo usuário!")
                show_statistics(trades, initial_balance, current_balance)
                break
                
            except Exception as e:
                logging.error(f"Erro durante execução: {e}")
                print(f"\n❌ Erro: {e}")
                time.sleep(5)
                
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        print(f"\n❌ Erro fatal: {e}")

def should_trade(analysis):
    """Verifica se deve executar trade"""
    direction = analysis.get('direction', 'NEUTRO')
    probability = analysis.get('probability', 0)
    signals = analysis.get('indicators', {}).get('signals', [])
    
    return (
        direction != "NEUTRO" and
        probability >= 0.3 and
        len(signals) >= 1
    )

def execute_real_trade(analysis, current_balance):
    """Executa trade em tempo real"""
    try:
        direction = analysis['direction']
        current_price = analysis['indicators']['current_price']
        
        # Simula execução com 1% do saldo
        position_size = current_balance * 0.01
        units = position_size / current_price
        
        # Simula resultado (em produção, isso seria uma ordem real)
        profit_loss = random.uniform(-0.005, 0.005) * position_size
        new_balance = current_balance + profit_loss
        
        return {
            'timestamp': datetime.now(),
            'direction': direction,
            'entry_price': current_price,
            'position_size': position_size,
            'units': units,
            'profit_loss': profit_loss,
            'new_balance': new_balance
        }
        
    except Exception as e:
        logging.error(f"Erro ao executar trade: {e}")
        return None

def show_statistics(trades, initial_balance, current_balance):
    """Mostra estatísticas das operações"""
    print("\n📈 Estatísticas:")
    print(f"Total de Trades: {len(trades)}")
    profitable_trades = sum(1 for t in trades if t['profit_loss'] > 0)
    win_rate = (profitable_trades / len(trades)) * 100 if trades else 0
    total_profit = current_balance - initial_balance
    profit_percent = (total_profit / initial_balance) * 100
    
    print(f"Trades Lucrativos: {profitable_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Lucro Total: ${total_profit:,.2f} ({profit_percent:,.2f}%)")
    print(f"Saldo Atual: ${current_balance:,.2f}")

if __name__ == "__main__":
    # Configuração do logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n1. Executar Bot em Tempo Real")
    print("2. Executar Backtesting")
    print("3. Executar Simulador com Aprendizado")
    choice = input("\nEscolha uma opção (1-3): ")
    
    if choice == "1":
        bot = CryptoTradingBot(config)
        run_real_time_bot()
    elif choice == "2":
        bot = CryptoTradingBot(config)
        run_backtest_analysis()
    elif choice == "3":
        bot = CryptoTradingBot(config)
        simulator = LiveSimulator(bot, config)
        simulator.run_simulation()
    else:
        print("Opção inválida!") 