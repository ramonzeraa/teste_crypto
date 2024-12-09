import pytest
from src.core.crypto_bot import CryptoTradingBot
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def bot():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    return CryptoTradingBot(api_key, api_secret)

def test_get_historical_data(bot):
    df = bot.get_historical_data('BTCUSDT', limit=100)
    assert isinstance(df, pd.DataFrame)
    assert len(df) <= 100
    assert 'close' in df.columns

def test_calculate_indicators(bot):
    df = bot.get_historical_data('BTCUSDT', limit=100)
    df_with_indicators = bot.calculate_indicators(df)
    
    required_columns = ['EMA20', 'EMA50', 'MACD', 'RSI']
    for col in required_columns:
        assert col in df_with_indicators.columns

def test_predict_movement(bot):
    bot.train_model('BTCUSDT')
    prediction, probability = bot.predict_movement('BTCUSDT')
    
    assert isinstance(prediction, (int, bool))
    assert isinstance(probability, float)
    assert 0 <= probability <= 1
