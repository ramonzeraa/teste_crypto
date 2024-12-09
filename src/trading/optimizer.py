import numpy as np
import itertools
from ..analysis.backtest import Backtest
from datetime import datetime, timedelta

def optimize_parameters():
    """
    Otimiza parâmetros do modelo usando grid search
    """
    print("\n=== Iniciando Otimização de Parâmetros ===")
    
    # Define os parâmetros a serem testados
    best_params = {
        'rsi_oversold': range(20, 40, 5),      # RSI sobrevendido
        'rsi_overbought': range(60, 80, 5),    # RSI sobrecomprado
        'confidence_threshold': np.arange(0.5, 0.8, 0.05),  # Confiança mínima
        'stop_loss': np.arange(0.01, 0.03, 0.005),         # Stop Loss
        'take_profit': np.arange(0.02, 0.05, 0.005)        # Take Profit
    }
    
    results = []
    total_combinations = np.prod([len(v) for v in best_params.values()])
    current = 0
    
    print(f"Testando {total_combinations} combinações de parâmetros...")
    
    # Grid search
    for params in itertools.product(*best_params.values()):
        current += 1
        param_dict = dict(zip(best_params.keys(), params))
        
        # Atualiza progresso
        print(f"\rProgresso: {current}/{total_combinations} ({current/total_combinations*100:.1f}%)", end="")
        
        # Executa backtesting com os parâmetros atuais
        backtest = Backtest(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            initial_balance=10000
        )
        
        backtest_result = backtest.run(param_dict)
        
        if backtest_result:
            results.append({
                'params': param_dict,
                'profit': backtest_result['total_profit'],
                'win_rate': backtest_result['win_rate'],
                'max_drawdown': backtest_result['max_drawdown']
            })
    
    print("\n\n=== Resultados da Otimização ===")
    
    if not results:
        print("❌ Nenhum resultado válido encontrado")
        return None
        
    # Encontra melhores parâmetros
    best_result = max(results, key=lambda x: x['profit'])
    
    print("\n🏆 Melhores Parâmetros Encontrados:")
    print(f"RSI Sobrevendido: {best_result['params']['rsi_oversold']}")
    print(f"RSI Sobrecomprado: {best_result['params']['rsi_overbought']}")
    print(f"Confiança Mínima: {best_result['params']['confidence_threshold']:.2f}")
    print(f"Stop Loss: {best_result['params']['stop_loss']:.3f}")
    print(f"Take Profit: {best_result['params']['take_profit']:.3f}")
    
    print("\n📊 Resultados com Melhores Parâmetros:")
    print(f"Lucro Total: ${best_result['profit']:,.2f}")
    print(f"Win Rate: {best_result['win_rate']:.1f}%")
    print(f"Drawdown Máximo: {best_result['max_drawdown']:.1f}%")
    
    return best_result['params']