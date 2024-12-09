"""
Testes Unitários para DataLoader
"""
import unittest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from src.data.loader import DataLoader

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        # Carrega variáveis de ambiente
        load_dotenv()
        
        self.loader = DataLoader()
        
        # Em ambiente de teste, usamos os mocks do Binance Client
        # Não precisamos das chaves reais pois vamos simular as respostas
        with patch('binance.client.Client'):
            self.loader.connect(
                api_key=os.getenv('BINANCE_API_KEY'),
                api_secret=os.getenv('BINANCE_API_SECRET')
            )
    
    @patch('binance.client.Client')
    def test_connection(self, mock_client):
        """Testa conexão com Binance"""
        # Configura mock
        mock_client.return_value.get_system_status.return_value = {'status': 0}
        
        # Testa conexão
        self.assertTrue(self.loader.connected)
        self.assertIsNotNone(self.loader.client)
    
    @patch('binance.client.Client')
    def test_get_latest_data(self, mock_client):
        """Testa obtenção de dados recentes"""
        # Mock de dados
        mock_klines = [
            [1625097600000, "35000", "36000", "34000", "35500", "100", 1625097900000, 
             "3500000", 1000, "50", "1750000", "0"],
            [1625097900000, "35500", "36500", "35000", "36000", "150", 1625098200000,
             "5250000", 1500, "75", "2625000", "0"]
        ]
        mock_client.return_value.get_klines.return_value = mock_klines
        
        # Obtém dados
        df = self.loader.get_latest_data('BTCUSDT', '1h')
        
        # Verifica estrutura
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(all(col in df.columns for col in 
                          ['open', 'high', 'low', 'close', 'volume'])) 
    
    @patch('binance.client.Client')
    def test_historical_data(self, mock_client):
        """Testa obtenção de dados históricos"""
        # Mock de dados históricos
        mock_historical = [
            [1625097600000, "35000", "36000", "34000", "35500", "100", 1625097900000, 
             "3500000", 1000, "50", "1750000", "0"]
        ] * 100  # 100 candles
        mock_client.return_value.get_historical_klines.return_value = mock_historical
        
        # Define período
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Obtém dados
        df = self.loader.get_historical_data('BTCUSDT', '1h', start_date, end_date)
        
        # Verifica dados
        self.assertEqual(len(df), 100)
        self.assertTrue(df.index.is_monotonic_increasing)
    
    def test_cache_system(self):
        """Testa sistema de cache"""
        # Prepara dados de teste
        test_data = pd.DataFrame({
            'close': [100, 200, 300]
        })
        
        # Simula cache
        cache_key = 'BTCUSDT_1h'
        self.loader.cache[cache_key] = {
            'data': test_data,
            'last_update': datetime.now()
        }
        
        # Verifica cache válido
        self.assertIn(cache_key, self.loader.cache)
        self.assertIsInstance(self.loader.cache[cache_key]['data'], pd.DataFrame)
    
    @patch('binance.client.Client')
    def test_account_balance(self, mock_client):
        """Testa obtenção de saldo"""
        # Mock de saldo
        mock_client.return_value.get_asset_balance.return_value = {
            'asset': 'USDT',
            'free': '1000.00',
            'locked': '0.00'
        }
        
        # Obtém saldo
        balance = self.loader.get_account_balance('USDT')
        
        # Verifica
        self.assertIsInstance(balance, float)
        self.assertEqual(balance, 1000.00)
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Testa conexão sem credenciais
        with self.assertRaises(Exception):
            self.loader.connect('', '')
        
        # Testa obtenção de dados sem conexão
        with self.assertRaises(Exception):
            self.loader.get_latest_data()
    
    @patch('binance.client.Client')
    def test_connection_check(self, mock_client):
        """Testa verificação de conexão"""
        # Mock de status
        mock_client.return_value.get_system_status.return_value = {'status': 0}
        
        # Testa conexão ativa
        self.assertTrue(self.loader.check_connection())
        
        # Simula falha
        mock_client.return_value.get_system_status.side_effect = Exception()
        self.assertFalse(self.loader.check_connection())
    
    def test_data_processing(self):
        """Testa processamento de dados"""
        # Dados de teste
        test_klines = [
            [1625097600000, "35000", "36000", "34000", "35500", "100", 
             1625097900000, "3500000", 1000, "50", "1750000", "0"]
        ]
        
        # Processa dados
        df = self.loader._process_klines(test_klines)
        
        # Verifica tipos de dados
        self.assertIsInstance(df.index[0], pd.Timestamp)
        self.assertIsInstance(df['close'][0], float)
        self.assertIsInstance(df['volume'][0], float)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        self.loader.cache.clear()
        if hasattr(self.loader, 'client'):
            self.loader.client = None
            self.loader.connected = False