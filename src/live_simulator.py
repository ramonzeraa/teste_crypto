from binance.client import Client
from datetime import datetime
import time
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np

class LiveSimulator:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.balance = 10000.00
        self.pattern_memory = {}
        self.trades = []
        self.wins = 0
        self.losses = 0
        
        # Carrega credenciais
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        self.client = Client(api_key, api_secret)

    def get_current_btc_price(self):
        """Obtém preço atual do BTC"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.config.SYMBOL)
            return float(ticker['price'])
        except Exception as e:
            print(f"\n⚠️ Erro ao obter preço: {e}")
            return None

    def ensure_indicators(self, df):
        """Garante que todos os indicadores necessários existam"""
        try:
            df = df.copy()
            
            # Bollinger Bands
            if 'bb_upper' not in df.columns:
                bb_period = 20
                std_dev = 2
                df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
                bb_std = df['close'].rolling(window=bb_period).std()
                df['bb_upper'] = df['bb_middle'] + (bb_std * std_dev)
                df['bb_lower'] = df['bb_middle'] - (bb_std * std_dev)
            
            # RSI
            if 'rsi' not in df.columns:
                period = 14
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            if 'macd' not in df.columns:
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                df['macd'] = exp1 - exp2
                df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # ATR
            if 'atr' not in df.columns:
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = np.max(ranges, axis=1)
                df['atr'] = true_range.rolling(14).mean()
            
            return df
            
        except Exception as e:
            print(f"Erro ao calcular indicadores: {e}")
            return df

    def identify_pattern(self, df):
        """Identifica padrão atual do mercado"""
        try:
            df = self.ensure_indicators(df)
            
            pattern = {
                'price_action': self.analyze_price_action(df),
                'volume_profile': self.analyze_volume(df),
                'indicators': self.analyze_indicators(df),
                'candlestick_patterns': self.analyze_candlestick_patterns(df),
                'support_resistance': self.analyze_support_resistance(df),
                'volatility': self.analyze_volatility(df),
                'timeframe': '1h'
            }
            return pattern
        except Exception as e:
            print(f"Erro ao identificar padrão: {e}")
            return None

    def analyze_price_action(self, df):
        """Analisa padrões de preço"""
        patterns = []
        last_candles = df.tail(5)
        
        # Tendência
        closes = last_candles['close'].values
        if closes[-1] > closes[-2] > closes[-3]:
            patterns.append('UPTREND')
        elif closes[-1] < closes[-2] < closes[-3]:
            patterns.append('DOWNTREND')
            
        # Suporte/Resistência
        lows = last_candles['low'].values
        highs = last_candles['high'].values
        
        if abs(lows[-1] - lows[-2]) < lows[-1] * 0.001:
            patterns.append('SUPPORT')
        if abs(highs[-1] - highs[-2]) < highs[-1] * 0.001:
            patterns.append('RESISTANCE')
            
        return patterns

    def analyze_volume(self, df):
        """Analisa perfil do volume"""
        volume_ma = df['volume'].rolling(window=20).mean()
        current_volume = df['volume'].iloc[-1]
        
        if current_volume > volume_ma.iloc[-1] * 1.5:
            return 'HIGH_VOLUME'
        elif current_volume < volume_ma.iloc[-1] * 0.5:
            return 'LOW_VOLUME'
        return 'NORMAL_VOLUME'

    def analyze_indicators(self, df):
        """Analisa indicadores técnicos"""
        signals = []
        
        # RSI
        if df['rsi'].iloc[-1] > 70:
            signals.append('RSI_OVERBOUGHT')
        elif df['rsi'].iloc[-1] < 30:
            signals.append('RSI_OVERSOLD')
        
        # MACD
        if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
            signals.append('MACD_BULLISH')
        else:
            signals.append('MACD_BEARISH')
        
        return signals

    def analyze_candlestick_patterns(self, df):
        """Analisa padrões de candlestick"""
        patterns = []
        last_candles = df.tail(3)
        
        # Doji
        if abs(last_candles['open'].iloc[-1] - last_candles['close'].iloc[-1]) < 0.1:
            patterns.append('DOJI')
        
        # Hammer
        body = abs(last_candles['open'].iloc[-1] - last_candles['close'].iloc[-1])
        lower_shadow = min(last_candles['open'].iloc[-1], last_candles['close'].iloc[-1]) - last_candles['low'].iloc[-1]
        if lower_shadow > body * 2:
            patterns.append('HAMMER')
            
        return patterns

    def analyze_support_resistance(self, df):
        """Analisa níveis de suporte e resistência"""
        levels = []
        price = df['close'].iloc[-1]
        
        # Identifica pivôs
        highs = df['high'].rolling(window=5, center=True).max()
        lows = df['low'].rolling(window=5, center=True).min()
        
        # Suportes
        recent_lows = lows.nlargest(3)
        for low in recent_lows:
            if 0.98 * low < price < 1.02 * low:
                levels.append('NEAR_SUPPORT')
                
        # Resistências
        recent_highs = highs.nlargest(3)
        for high in recent_highs:
            if 0.98 * high < price < 1.02 * high:
                levels.append('NEAR_RESISTANCE')
                
        return levels

    def analyze_volatility(self, df):
        """Analisa volatilidade"""
        signals = []
        
        if 'atr' in df.columns:
            atr = df['atr'].iloc[-1]
            atr_mean = df['atr'].mean()
            
            if atr > atr_mean * 1.5:
                signals.append('HIGH_VOLATILITY')
            elif atr < atr_mean * 0.5:
                signals.append('LOW_VOLATILITY')
        
        if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'bb_middle']):
            bb_width = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            current_width = bb_width.iloc[-1]
            mean_width = bb_width.mean()
            
            if current_width > mean_width * 1.2:
                signals.append('BB_EXPANDING')
            elif current_width < mean_width * 0.8:
                signals.append('BB_SQUEEZING')
                
        return signals
    def should_trade(self, pattern):
        """Analisa condições para trade"""
        signals = {
            'bullish': 0,
            'bearish': 0,
            'reasons': [],
            'confirmations': {
                'price_action': False,
                'volume': False,
                'volatility': False
            }
        }
        
        # Price Action (Peso 2)
        if 'UPTREND' in pattern['price_action']:
            signals['bullish'] += 2
            signals['reasons'].append("Tendência de alta")
            signals['confirmations']['price_action'] = True
        elif 'DOWNTREND' in pattern['price_action']:
            signals['bearish'] += 2
            signals['reasons'].append("Tendência de baixa")
            signals['confirmations']['price_action'] = True
            
        # Volume (Peso 1)
        if pattern['volume_profile'] == 'HIGH_VOLUME':
            signals['bullish'] += 1
            signals['reasons'].append("Volume Alto")
            signals['confirmations']['volume'] = True
        elif pattern['volume_profile'] == 'LOW_VOLUME':
            signals['reasons'].append("Volume Baixo")
            
        # Indicadores (Peso 1 cada)
        for signal in pattern['indicators']:
            if signal == 'MACD_BULLISH':
                signals['bullish'] += 1
                signals['reasons'].append("MACD Bullish")
            elif signal == 'MACD_BEARISH':
                signals['bearish'] += 1
                signals['reasons'].append("MACD Bearish")
            elif signal == 'RSI_OVERSOLD':
                signals['bullish'] += 1
                signals['reasons'].append("RSI Sobrevendido")
            elif signal == 'RSI_OVERBOUGHT':
                signals['bearish'] += 1
                signals['reasons'].append("RSI Sobrecomprado")
                
        # Volatilidade
        for signal in pattern.get('volatility', []):
            if signal == 'BB_SQUEEZING':
                signals['reasons'].append("Squeeze - Possível Movimento Forte")
                signals['confirmations']['volatility'] = True
                
        # Decisão Final
        min_score = 3.0
        min_confirmations = 2
        confirmations_count = sum(1 for v in signals['confirmations'].values() if v)
        
        if signals['bullish'] >= min_score and signals['bullish'] > signals['bearish'] * 1.5 and confirmations_count >= min_confirmations:
            signals['decision'] = 'LONG'
            signals['reasons'].append(f"\nSINAL DE COMPRA:")
            signals['reasons'].append(f"  • Pontuação de Alta: {signals['bullish']:.1f}")
            signals['reasons'].append(f"  • Confirmações: {confirmations_count}")
        elif signals['bearish'] >= min_score and signals['bearish'] > signals['bullish'] * 1.5 and confirmations_count >= min_confirmations:
            signals['decision'] = 'SHORT'
            signals['reasons'].append(f"\nSINAL DE VENDA:")
            signals['reasons'].append(f"  • Pontuação de Baixa: {signals['bearish']:.1f}")
            signals['reasons'].append(f"  • Confirmações: {confirmations_count}")
        else:
            signals['decision'] = None
            signals['reasons'].append(f"\nAGUARDANDO:")
            signals['reasons'].append(f"  • Alta: {signals['bullish']:.1f} / Baixa: {signals['bearish']:.1f}")
            signals['reasons'].append(f"  • Confirmações: {confirmations_count}/{min_confirmations}")
            
        return signals
    def execute_trade(self, pattern, current_price):
        """Executa trade"""
        try:
            position_size = self.balance * 0.01  # 1% do saldo
            direction = self.should_trade(pattern)['decision']
            
            if not direction:
                return None
                
            # Simula resultado
            exit_price = current_price * (1.002 if direction == 'LONG' else 0.998)
            profit_loss = position_size * (0.002 if direction == 'LONG' else -0.002)
            
            # Atualiza estatísticas
            self.balance += profit_loss
            if profit_loss > 0:
                self.wins += 1
            else:
                self.losses += 1
                
            trade = {
                'timestamp': datetime.now(),
                'direction': direction,
                'entry_price': current_price,
                'exit_price': exit_price,
                'profit_loss': profit_loss,
                'balance': self.balance
            }
            
            self.trades.append(trade)
            return trade
            
        except Exception as e:
            print(f"Erro ao executar trade: {e}")
            return None
    def run_simulation(self):
        """Executa simulação"""
        print("\nINICIANDO SIMULADOR COM APRENDIZADO")
        print("="*50)
        
        while True:
            try:
                current_price = self.get_current_btc_price()
                df = self.bot.get_historical_data()
                
                if current_price and df is not None:
                    pattern = self.identify_pattern(df)
                    signals = self.should_trade(pattern)
                    
                    print(f"\nANÁLISE DE MERCADO - {datetime.now().strftime('%H:%M:%S')}")
                    print("="*40)
                    print(f"BTC: ${current_price:.2f}")
                    print(f"\nPADRÕES IDENTIFICADOS:")
                    print(f"  • Price Action: {pattern['price_action']}")
                    print(f"  • Volume: {pattern['volume_profile']}")
                    print(f"  • Indicadores: {pattern['indicators']}")
                    
                    print("\nANÁLISE DE SINAIS:")
                    for reason in signals['reasons']:
                        print(f"  {reason}")
                    
                    if signals['decision']:
                        trade = self.execute_trade(pattern, current_price)
                        if trade:
                            print(f"\nTRADE EXECUTADO ({trade['direction']})")
                            print(f"  • Entrada: ${trade['entry_price']:.2f}")
                            print(f"  • Resultado: ${trade['profit_loss']:.2f}")
                            print(f"  • Saldo: ${trade['balance']:.2f}")
                    
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\n\nSIMULAÇÃO ENCERRADA")
                print(f"Total Trades: {len(self.trades)}")
                if self.trades:
                    win_rate = (self.wins / len(self.trades)) * 100
                    print(f"Win Rate: {win_rate:.1f}%")
                print(f"Saldo Final: ${self.balance:.2f}")
                break
                
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(5)