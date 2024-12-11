from src.ml.parameter_optimizer import ParameterOptimizer

# Exemplo de dados históricos
historical_data = {
    'prices': [100, 101, 102, 103, 102, 101, 100],
    'volumes': [10, 12, 11, 13, 14, 15, 16]
}
current_params = {
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bb_period': 20,
    'bb_std': 2,
    'stoch_period': 14,
    'adx_period': 14
}

optimizer = ParameterOptimizer()
optimized_params = optimizer.optimize_parameters(historical_data, current_params)
print("Parâmetros otimizados:", optimized_params)
