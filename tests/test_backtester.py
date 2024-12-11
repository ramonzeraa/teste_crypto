# src/tests/test_backtester.py
import pandas as pd
from src.ml.backtesting import Backtester
from src.ml.model import TradingModel  # Certifique-se de que o modelo esteja importado

# Exemplo de dados históricos em um DataFrame
historical_data = pd.DataFrame({
    'close': [100, 101, 102, 103, 102, 101, 100]
})

# Crie e treine o modelo antes de usar o backtester
model = TradingModel()
# Aqui você deve treinar o modelo com dados reais antes de usar
# model.train(X, y)  # Substitua por dados reais

backtester = Backtester(model)  # Passa o modelo treinado
score = backtester.run_backtest(historical_data, {'rsi_period': 14})  # Use parâmetros adequados
print("Score do backtest:", score)