from binance.client import Client
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..trading.paper_trading import PaperTrading
from ..analysis.technical_indicators import TechnicalIndicators
from ..utils.config import config
import ccxt
import time
import yfinance as yf
import json
import os

class CryptoTradingBot:
    def __init__(self, api_key=None, api_secret=None):
        """Inicializa o bot com configurações otimizadas"""
        self.balance = 10000.0
        self.position_size = 0.1
        self.stop_loss = 0.02
        self.take_profit = 0.04
        self.learning_rate = 0.01
        
        # Inicializa pesos dos sinais
        self.signal_weights = {
            'TENDENCIA_ALTA': 1.0,
            'TENDENCIA_BAIXA': 1.0,
            'MACD_POSITIVO': 1.0,
            'MACD_NEGATIVO': 1.0,
            'RSI_SOBRECOMPRA': 1.0,
            'RSI_SOBREVENDA': 1.0,
            'BB_ALTO': 1.0,
            'BB_BAIXO': 1.0,
            'VOLUME_ALTO': 1.0
        }
        
        self.trade_history = []
        
        # Configurações dos indicadores
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.rsi_period = 14
        self.bb_period = 20
        self.bb_std = 2
        self.symbol = "BTC-USD"  # Símbolo padrão

        self.pattern_memory = {}
        self.current_signals = []
        self.min_signals = 2

        # Carrega memória de padrões
        self.pattern_memory_file = 'src/data/pattern_memory.json'
        self.load_pattern_memory()

    def load_pattern_memory(self):
        """Carrega memória de padrões"""
        try:
            if os.path.exists(self.pattern_memory_file):
                with open(self.pattern_memory_file, 'r') as f:
                    self.pattern_memory = json.load(f)
            else:
                self.pattern_memory = {}
        except Exception as e:
            logging.error(f"Erro ao carregar memória: {e}")
            self.pattern_memory = {}

    def initialize_indicators(self, df):
        """Inicializa indicadores técnicos"""
        try:
            # Copia o DataFrame para não modificar o original
            df = df.copy()
            
            # MACD
            exp1 = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
            exp2 = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=self.macd_signal, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['sma'] = df['close'].rolling(window=self.bb_period).mean()
            std = df['close'].rolling(window=self.bb_period).std()
            df['bb_upper'] = df['sma'] + (self.bb_std * std)
            df['bb_lower'] = df['sma'] - (self.bb_std * std)
            
            # Volume médio
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            
            # Preenche valores NaN
            df.fillna(method='bfill', inplace=True)
            
            print("Indicadores inicializados com sucesso!")
            return df
            
        except Exception as e:
            print(f"Erro ao inicializar indicadores: {str(e)}")
            return None

    def get_historical_data(self, start_date=None, end_date=None, interval='1h'):
        """Obtém dados históricos da API do Yahoo Finance"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
                
            # Download dos dados
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            
            # Renomeia colunas para lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Reseta index para ter datetime como coluna
            df = df.reset_index()
            
            print(f"Dados carregados: {len(df)} períodos")
            
            # Inicializa indicadores
            df = self.initialize_indicators(df)
            
            return df
            
        except Exception as e:
            print(f"Erro ao obter dados históricos: {str(e)}")
            return None

    def log_learning_status(self):
        """Log detalhado do status de aprendizado"""
        print("\n=== Status do Aprendizado ===")
        print(f"Learning Rate: {self.learning_rate:.4f}")
        
        if self.trade_history:
            wins = len([t for t in self.trade_history if t.get('profit', 0) > 0])
            total = len(self.trade_history)
            win_rate = wins / total if total > 0 else 0
            print(f"Win Rate: {win_rate:.2%}")
        
        print("\nPesos dos Sinais:")
        for signal, weight in sorted(self.signal_weights.items(), key=lambda x: x[1], reverse=True):
            print(f"{signal}: {weight:.2f}")

    def analyze_market_historical(self, df):
        """Analisa o mercado usando dados históricos"""
        try:
            if df is None or len(df) < 2:
                return None
            
            # Pega o último candle
            last_candle = df.iloc[-1]
            
            # Lista para armazenar sinais ativos
            active_signals = []
            signal_strength = 0
            
            # Análise MACD
            if last_candle['macd'] > last_candle['macd_signal']:
                active_signals.append('MACD_POSITIVO')
                signal_strength += 0.2
            elif last_candle['macd'] < last_candle['macd_signal']:
                active_signals.append('MACD_NEGATIVO')
                signal_strength += 0.2
            
            # Análise RSI
            if last_candle['rsi'] > 70:
                active_signals.append('RSI_SOBRECOMPRA')
                signal_strength += 0.15
            elif last_candle['rsi'] < 30:
                active_signals.append('RSI_SOBREVENDA')
                signal_strength += 0.15
            
            # Análise Bollinger Bands
            if last_candle['close'] > last_candle['bb_upper']:
                active_signals.append('BB_ALTO')
                signal_strength += 0.15
            elif last_candle['close'] < last_candle['bb_lower']:
                active_signals.append('BB_BAIXO')
                signal_strength += 0.15
            
            # Análise de Volume
            if last_candle['volume'] > last_candle['volume_sma'] * 1.5:
                active_signals.append('VOLUME_ALTO')
                signal_strength += 0.15
            
            # Análise de Tendência
            sma_curta = df['close'].rolling(window=10).mean().iloc[-1]
            sma_longa = df['close'].rolling(window=20).mean().iloc[-1]
            
            if sma_curta > sma_longa:
                active_signals.append('TENDENCIA_ALTA')
                signal_strength += 0.2
                direction = "ALTA"
            else:
                active_signals.append('TENDENCIA_BAIXA')
                signal_strength += 0.2
                direction = "BAIXA"
            
            # Calcula probabilidade baseada na força dos sinais
            probability = signal_strength if active_signals else 0
            
            return {
                'direction': direction,
                'probability': probability,
                'signals': active_signals
            }
            
        except Exception as e:
            logging.error(f"Erro na análise de mercado: {str(e)}")
            return None

    def should_execute_trade(self):
        """Verifica se deve executar trade baseado nos sinais atuais"""
        if not hasattr(self, 'current_signals') or not self.current_signals:
            return False
        
        # Mínimo de sinais reduzido para permitir mais trades
        min_signals = 2
        if len(self.current_signals) < min_signals:
            return False
        
        # Verifica padrão conhecido
        pattern = self.identify_pattern(self.current_signals)
        
        # Se o padrão é novo, dá uma chance para aprender
        if pattern not in self.pattern_memory:
            return True
        
        # Para padrões conhecidos, usa o aprendizado
        stats = self.pattern_memory[pattern]
        total_trades = stats['wins'] + stats['losses']
        
        if total_trades >= 5:  # Após 5 trades do mesmo padrão
            win_rate = stats['wins'] / total_trades
            if win_rate < 0.4:  # Win rate mínimo baixo para continuar explorando
                return False
            
            if stats['consecutive_losses'] >= 5:  # Tolerância maior a perdas
                return False
        
        # Maior probabilidade de executar trades para aprender
        probability = min(1.0, len(self.current_signals) / 4)  # 4 sinais = 100%
        return probability >= 0.4  # Probabilidade mínima baixa

    def identify_pattern(self, signals):
        """
        Identifica o padrão dos sinais atuais.
        Retorna uma tupla ordenada dos sinais para usar como chave.
        """
        if not signals:
            return tuple()
        
        # Converte lista de sinais em tupla ordenada
        pattern = tuple(sorted(signals))
        
        # Inicializa estatísticas do padrão se não existir
        if pattern not in self.pattern_memory:
            self.pattern_memory[pattern] = {
                'wins': 0,
                'losses': 0,
                'consecutive_losses': 0,
                'last_result': None
            }
        
        return pattern

    def update_pattern_memory(self, pattern, profit):
        """
        Atualiza as estatísticas do padrão após um trade
        """
        if not pattern or pattern not in self.pattern_memory:
            return
        
        stats = self.pattern_memory[pattern]
        
        if profit > 0:
            stats['wins'] += 1
            stats['consecutive_losses'] = 0
            stats['last_result'] = 'win'
        else:
            stats['losses'] += 1
            if stats['last_result'] == 'loss':
                stats['consecutive_losses'] += 1
            else:
                stats['consecutive_losses'] = 1
            stats['last_result'] = 'loss'

