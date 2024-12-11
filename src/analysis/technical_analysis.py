import pandas as pd
import numpy as np
from typing import Dict
import logging
from datetime import datetime

class TechnicalAnalyzer:
    def __init__(self):
        self.indicators = {}
        self.signals = {}
        # Pesos dos indicadores
        self.weights = {
            'rsi': 0.15,
            'macd': 0.15,
            'bb': 0.10,
            'ema': 0.20,
            'volume': 0.15,
            'stoch': 0.15,
            'adx': 0.10
        }
        self.logger = logging.getLogger('technical_analyzer')

    def analyze(self, data: pd.DataFrame) -> Dict:
        """Análise técnica aprimorada"""
        try:
            if data.empty:
                return {}

            # Calcula indicadores
            self.calculate_rsi(data)
            self.calculate_macd(data)
            self.calculate_bollinger_bands(data)
            self.calculate_ema(data)
            self.calculate_stochastic(data)
            self.calculate_adx(data)
            self.calculate_volume_analysis(data)
            
            # Gera sinais
            signals = {
                'rsi': self._analyze_rsi(),
                'macd': self._analyze_macd(),
                'bb': self._analyze_bb(),
                'ema': self._analyze_ema(),
                'stoch': self._analyze_stochastic(),
                'adx': self._analyze_adx(),
                'volume': self._analyze_volume(),
                'trend': self._analyze_trend(data),
                'timestamp': datetime.now()
            }
            
            # Calcula força geral do sinal
            signals['trend_strength'] = self._calculate_trend_strength(signals)
            signals['divergences'] = self._check_divergences(signals)
            
            # Adicionar novos indicadores
            volume_profile = self._analyze_volume_profile(data)
            support_resistance = self._find_support_resistance(data)
            
            # Melhorar cálculo de força da tendência
            trend_strength = self._calculate_trend_strength(
                rsi=signals['rsi'],
                macd=signals['macd'],
                bb=signals['bb'],
                volume=volume_profile,
                support_resistance=support_resistance
            )
            
            return {
                **signals,
                'volume_profile': volume_profile,
                'support_resistance': support_resistance,
                'trend_strength': trend_strength
            }
            
        except Exception as e:
            logging.error(f"Erro na análise técnica: {e}")
            raise

    def calculate_rsi(self, data: pd.DataFrame, period: int = 14):
        """Calcula RSI"""
        try:
            close_delta = data['close'].diff()
            
            # Calcula ganhos e perdas
            gain = (close_delta.where(close_delta > 0, 0)).rolling(window=period).mean()
            loss = (-close_delta.where(close_delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            self.indicators['rsi'] = 100 - (100 / (1 + rs))
            
        except Exception as e:
            logging.error(f"Erro no cálculo do RSI: {e}")

    def calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calcula MACD"""
        try:
            exp1 = data['close'].ewm(span=fast, adjust=False).mean()
            exp2 = data['close'].ewm(span=slow, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            
            self.indicators['macd'] = macd
            self.indicators['macd_signal'] = signal_line
            self.indicators['macd_hist'] = macd - signal_line
            
        except Exception as e:
            logging.error(f"Erro no cálculo do MACD: {e}")

    def calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std: int = 2):
        """Calcula Bandas de Bollinger"""
        try:
            sma = data['close'].rolling(window=period).mean()
            rolling_std = data['close'].rolling(window=period).std()
            
            self.indicators['bb_upper'] = sma + (rolling_std * std)
            self.indicators['bb_middle'] = sma
            self.indicators['bb_lower'] = sma - (rolling_std * std)
            
        except Exception as e:
            logging.error(f"Erro no cálculo das Bandas de Bollinger: {e}")

    def calculate_ema(self, data: pd.DataFrame):
        """Calcula EMAs"""
        try:
            self.indicators['ema_9'] = data['close'].ewm(span=9, adjust=False).mean()
            self.indicators['ema_21'] = data['close'].ewm(span=21, adjust=False).mean()
            self.indicators['ema_55'] = data['close'].ewm(span=55, adjust=False).mean()
        except Exception as e:
            logging.error(f"Erro no cálculo das EMAs: {e}")

    def calculate_stochastic(self, data: pd.DataFrame, period: int = 14):
        """Calcula Estocástico"""
        try:
            low_min = data['low'].rolling(window=period).min()
            high_max = data['high'].rolling(window=period).max()
            
            k = 100 * ((data['close'] - low_min) / (high_max - low_min))
            self.indicators['stoch_k'] = k
            self.indicators['stoch_d'] = k.rolling(window=3).mean()
        except Exception as e:
            logging.error(f"Erro no cálculo do Estocástico: {e}")

    def calculate_adx(self, data: pd.DataFrame, period: int = 14):
        """Calcula ADX"""
        try:
            plus_dm = data['high'].diff()
            minus_dm = data['low'].diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm > 0] = 0
            
            tr1 = pd.DataFrame(data['high'] - data['low'])
            tr2 = pd.DataFrame(abs(data['high'] - data['close'].shift(1)))
            tr3 = pd.DataFrame(abs(data['low'] - data['close'].shift(1)))
            frames = [tr1, tr2, tr3]
            tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
            atr = tr.rolling(period).mean()
            
            plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
            minus_di = abs(100 * (minus_dm.rolling(period).mean() / atr))
            dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
            adx = ((dx.shift(1) * (period - 1)) + dx) / period
            self.indicators['adx'] = adx
            self.indicators['plus_di'] = plus_di
            self.indicators['minus_di'] = minus_di
        except Exception as e:
            logging.error(f"Erro no cálculo do ADX: {e}")

    def calculate_volume_analysis(self, data: pd.DataFrame):
        """Analisa volume"""
        try:
            self.indicators['volume_sma'] = data['volume'].rolling(window=20).mean()
            self.indicators['volume_ratio'] = data['volume'] / self.indicators['volume_sma']
        except Exception as e:
            logging.error(f"Erro na análise de volume: {e}")

    def _analyze_rsi(self) -> Dict:
        """Analisa sinais do RSI"""
        try:
            rsi = self.indicators.get('rsi', pd.Series())
            if rsi.empty:
                return {}
                
            last_rsi = rsi.iloc[-1]
            return {
                'value': last_rsi,
                'oversold': last_rsi < 30,
                'overbought': last_rsi > 70
            }
            
        except Exception as e:
            logging.error(f"Erro na análise do RSI: {e}")
            return {}

    def _analyze_macd(self) -> Dict:
        """Analisa sinais do MACD"""
        try:
            hist = self.indicators.get('macd_hist', pd.Series())
            if hist.empty:
                return {}
                
            last_hist = hist.iloc[-1]
            prev_hist = hist.iloc[-2]
            
            return {
                'value': last_hist,
                'crossover': prev_hist < 0 and last_hist > 0,
                'crossunder': prev_hist > 0 and last_hist < 0
            }
            
        except Exception as e:
            logging.error(f"Erro na análise do MACD: {e}")
            return {}

    def _analyze_bb(self) -> Dict:
        """Analisa sinais das Bandas de Bollinger"""
        try:
            if not all(k in self.indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
                return {}
                
            last_close = self.indicators['bb_middle'].index[-1]
            
            return {
                'upper': self.indicators['bb_upper'].iloc[-1],
                'lower': self.indicators['bb_lower'].iloc[-1],
                'middle': self.indicators['bb_middle'].iloc[-1],
                'width': (self.indicators['bb_upper'].iloc[-1] - 
                         self.indicators['bb_lower'].iloc[-1]) / 
                        self.indicators['bb_middle'].iloc[-1]
            }
            
        except Exception as e:
            logging.error(f"Erro na análise das BBs: {e}")
            return {}

    def _analyze_trend(self, data: pd.DataFrame) -> str:
        """Analisa tendência geral"""
        try:
            sma_20 = data['close'].rolling(window=20).mean()
            sma_50 = data['close'].rolling(window=50).mean()
            
            if sma_20.iloc[-1] > sma_50.iloc[-1]:
                return 'bullish'
            elif sma_20.iloc[-1] < sma_50.iloc[-1]:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logging.error(f"Erro na análise de tendência: {e}")
            return 'neutral'

    def _analyze_ema(self) -> Dict:
        """Analisa sinais das EMAs"""
        try:
            ema_9 = self.indicators.get('ema_9', pd.Series())
            if ema_9.empty:
                return {}
                
            last_ema_9 = ema_9.iloc[-1]
            last_ema_21 = self.indicators.get('ema_21', pd.Series()).iloc[-1]
            last_ema_55 = self.indicators.get('ema_55', pd.Series()).iloc[-1]
            
            if last_ema_9 > last_ema_21 and last_ema_21 > last_ema_55:
                return {'trend': 'bullish'}
            elif last_ema_9 < last_ema_21 and last_ema_21 < last_ema_55:
                return {'trend': 'bearish'}
            else:
                return {'trend': 'neutral'}
            
        except Exception as e:
            logging.error(f"Erro na análise das EMAs: {e}")
            return {}

    def _analyze_stochastic(self) -> Dict:
        """Analisa sinais do Estocástico"""
        try:
            stoch_k = self.indicators.get('stoch_k', pd.Series())
            if stoch_k.empty:
                return {}
                
            last_stoch_k = stoch_k.iloc[-1]
            last_stoch_d = self.indicators.get('stoch_d', pd.Series()).iloc[-1]
            
            return {
                'value': last_stoch_k,
                'oversold': last_stoch_k < 20,
                'overbought': last_stoch_k > 80
            }
            
        except Exception as e:
            logging.error(f"Erro na análise do Estocástico: {e}")
            return {}

    def _analyze_adx(self) -> Dict:
        """Analisa sinais do ADX"""
        try:
            adx = self.indicators.get('adx', pd.Series())
            if adx.empty:
                return {}
                
            last_adx = adx.iloc[-1]
            last_plus_di = self.indicators.get('plus_di', pd.Series()).iloc[-1]
            last_minus_di = self.indicators.get('minus_di', pd.Series()).iloc[-1]
            
            return {
                'value': last_adx,
                'trend_strength': last_adx,
                'trend': 'bullish' if last_plus_di > last_minus_di else 'bearish'
            }
            
        except Exception as e:
            logging.error(f"Erro na análise do ADX: {e}")
            return {}

    def _analyze_volume(self) -> Dict:
        """Analisa sinais de volume"""
        try:
            volume_ratio = self.indicators.get('volume_ratio', pd.Series())
            if volume_ratio.empty:
                return {}
                
            last_volume_ratio = volume_ratio.iloc[-1]
            
            return {
                'value': last_volume_ratio,
                'trend': 'increasing' if last_volume_ratio > 1 else 'decreasing'
            }
            
        except Exception as e:
            logging.error(f"Erro na análise de volume: {e}")
            return {}

    def _check_divergences(self, signals: Dict) -> Dict:
        """Verifica divergências entre indicadores"""
        try:
            divergences = {
                'price_rsi': False,
                'price_macd': False,
                'indicators_sentiment': False,
                'severity': 'low'
            }
            
            # Verifica divergência preço/RSI
            if 'rsi' in signals:
                rsi_trend = 'bullish' if signals['rsi']['value'] > 50 else 'bearish'
                if rsi_trend != signals['trend']:
                    divergences['price_rsi'] = True
            
            # Verifica divergência preço/MACD
            if 'macd' in signals:
                macd_trend = 'bullish' if signals['macd']['value'] > 0 else 'bearish'
                if macd_trend != signals['trend']:
                    divergences['price_macd'] = True
            
            # Calcula severidade
            divergence_count = sum(1 for v in divergences.values() if v is True)
            if divergence_count >= 2:
                divergences['severity'] = 'high'
            elif divergence_count == 1:
                divergences['severity'] = 'medium'
            
            return divergences
            
        except Exception as e:
            logging.error(f"Erro na verificação de divergências: {e}")
            return {}

    def _calculate_trend_strength(self, rsi: Dict, macd: Dict, bb: Dict, 
                                volume: Dict, support_resistance: Dict) -> float:
        """Calcula força da tendência considerando múltiplos fatores"""
        try:
            # Pesos dos indicadores
            weights = {
                'rsi': 0.2,
                'macd': 0.3,
                'bb': 0.2,
                'volume': 0.15,
                'sr': 0.15
            }
            
            # Normaliza RSI
            rsi_strength = (rsi['value'] - 50) / 50
            
            # Normaliza MACD
            macd_strength = np.tanh(macd['value'] / 100)
            
            # Normaliza Bollinger
            bb_strength = bb['width'] * (1 if bb['trend'] == 'bullish' else -1)
            
            # Normaliza Volume
            vol_strength = (volume['strength'] - 1) * (1 if volume['trend'] == 'increasing' else -1)
            
            # Calcula força baseada em S/R
            price = support_resistance['pivot']
            sr_strength = (price - support_resistance['support_1']) / (
                support_resistance['resistance_1'] - support_resistance['support_1']
            ) - 0.5
            
            # Calcula média ponderada
            trend_strength = (
                weights['rsi'] * rsi_strength +
                weights['macd'] * macd_strength +
                weights['bb'] * bb_strength +
                weights['volume'] * vol_strength +
                weights['sr'] * sr_strength
            )
            
            return np.clip(trend_strength, -1, 1)
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular força da tendência: {e}")
            return 0.0

    def _analyze_volume_profile(self, data: pd.DataFrame) -> Dict:
        """Analisa o perfil do volume"""
        try:
            volume = data['volume'].values
            close = data['close'].values
            
            # Calcula volume médio
            avg_volume = np.mean(volume)
            
            # Analisa distribuição do volume
            volume_trend = 'increasing' if volume[-1] > avg_volume else 'decreasing'
            
            # Calcula força do volume
            volume_strength = volume[-1] / avg_volume
            
            # Detecta picos de volume
            volume_peaks = np.where(volume > avg_volume * 1.5)[0]
            
            return {
                'trend': volume_trend,
                'strength': volume_strength,
                'peaks': len(volume_peaks),
                'average': avg_volume
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de volume: {e}")
            return {
                'trend': 'neutral',
                'strength': 1.0,
                'peaks': 0,
                'average': 0
            }

    def _find_support_resistance(self, data: pd.DataFrame) -> Dict:
        """Encontra níveis de suporte e resistência"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            # Calcula níveis usando médias móveis
            ma20 = np.mean(close[-20:])
            ma50 = np.mean(close[-50:])
            
            # Encontra pivôs
            pivot = (high[-1] + low[-1] + close[-1]) / 3
            
            # Define níveis
            r1 = 2 * pivot - low[-1]
            s1 = 2 * pivot - high[-1]
            
            return {
                'support_1': s1,
                'resistance_1': r1,
                'ma20': ma20,
                'ma50': ma50,
                'pivot': pivot
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular suporte/resistência: {e}")
            return {
                'support_1': 0,
                'resistance_1': 0,
                'ma20': 0,
                'ma50': 0,
                'pivot': 0
            }
