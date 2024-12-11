import pandas as pd
import numpy as np
from typing import Dict
import logging
from datetime import datetime

class TechnicalAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger('technical_analyzer')
        self.indicators = {}
        
        # Pesos dos indicadores para análise
        self.weights = {
            'rsi': 0.2,
            'macd': 0.3,
            'bb': 0.2,
            'volume': 0.15,
            'sr': 0.15
        }

    def analyze(self, data: pd.DataFrame) -> Dict:
        """Análise técnica completa"""
        try:
            if data.empty:
                self.logger.warning("DataFrame vazio recebido")
                return {}

            # Calcula todos os indicadores
            self._calculate_all_indicators(data)
            
            # Análises básicas
            rsi_analysis = self._analyze_rsi()
            macd_analysis = self._analyze_macd()
            bb_analysis = self._analyze_bb()
            ema_analysis = self._analyze_ema()
            stoch_analysis = self._analyze_stochastic()
            adx_analysis = self._analyze_adx()
            
            # Análises avançadas
            volume_profile = self._analyze_volume_profile(data)
            support_resistance = self._find_support_resistance(data)
            
            # Determina tendência
            trend = self._analyze_trend(data)
            
            # Calcula força da tendência
            trend_strength = self._calculate_trend_strength(
                rsi=rsi_analysis,
                macd=macd_analysis,
                bb=bb_analysis,
                volume=volume_profile,
                support_resistance=support_resistance
            )
            
            # Monta resultado
            result = {
                'rsi': rsi_analysis,
                'macd': macd_analysis,
                'bb': bb_analysis,
                'ema': ema_analysis,
                'stoch': stoch_analysis,
                'adx': adx_analysis,
                'volume_profile': volume_profile,
                'support_resistance': support_resistance,
                'trend': trend,
                'trend_strength': trend_strength,
                'timestamp': datetime.now()
            }
            
            # Adiciona análise de divergências
            result['divergences'] = self._check_divergences(result)
            
            self.logger.info(f"Análise técnica completada: {trend} ({trend_strength:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na análise técnica: {e}")
            raise

    def _calculate_all_indicators(self, data: pd.DataFrame):
        """Calcula todos os indicadores técnicos"""
        try:
            self._calculate_rsi(data)
            self._calculate_macd(data)
            self._calculate_bollinger_bands(data)
            self._calculate_ema(data)
            self._calculate_stochastic(data)
            self._calculate_adx(data)
            self._calculate_volume_analysis(data)
        except Exception as e:
            self.logger.error(f"Erro no cálculo dos indicadores: {e}")
            raise

    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14):
        """Calcula RSI"""
        try:
            close_delta = data['close'].diff()
            gain = (close_delta.where(close_delta > 0, 0)).rolling(window=period).mean()
            loss = (-close_delta.where(close_delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            self.indicators['rsi'] = 100 - (100 / (1 + rs))
        except Exception as e:
            self.logger.error(f"Erro no cálculo do RSI: {e}")
            raise

    def _calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
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
            self.logger.error(f"Erro no cálculo do MACD: {e}")
            raise

    def _calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std: int = 2):
        """Calcula Bandas de Bollinger"""
        try:
            sma = data['close'].rolling(window=period).mean()
            rolling_std = data['close'].rolling(window=period).std()
            
            self.indicators['bb_upper'] = sma + (rolling_std * std)
            self.indicators['bb_middle'] = sma
            self.indicators['bb_lower'] = sma - (rolling_std * std)
        except Exception as e:
            self.logger.error(f"Erro no cálculo das Bandas de Bollinger: {e}")
            raise

    def _calculate_ema(self, data: pd.DataFrame):
        """Calcula EMAs"""
        try:
            self.indicators['ema_9'] = data['close'].ewm(span=9, adjust=False).mean()
            self.indicators['ema_21'] = data['close'].ewm(span=21, adjust=False).mean()
            self.indicators['ema_55'] = data['close'].ewm(span=55, adjust=False).mean()
        except Exception as e:
            self.logger.error(f"Erro no cálculo das EMAs: {e}")
            raise

    def _calculate_stochastic(self, data: pd.DataFrame, period: int = 14):
        """Calcula Estocástico"""
        try:
            low_min = data['low'].rolling(window=period).min()
            high_max = data['high'].rolling(window=period).max()
            
            k = 100 * ((data['close'] - low_min) / (high_max - low_min))
            self.indicators['stoch_k'] = k
            self.indicators['stoch_d'] = k.rolling(window=3).mean()
        except Exception as e:
            self.logger.error(f"Erro no cálculo do Estocástico: {e}")
            raise

    def _calculate_adx(self, data: pd.DataFrame, period: int = 14):
        """Calcula ADX"""
        try:
            tr1 = pd.DataFrame(data['high'] - data['low'])
            tr2 = pd.DataFrame(abs(data['high'] - data['close'].shift(1)))
            tr3 = pd.DataFrame(abs(data['low'] - data['close'].shift(1)))
            frames = [tr1, tr2, tr3]
            tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
            atr = tr.rolling(period).mean()
            
            plus_dm = data['high'].diff()
            minus_dm = data['low'].diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm > 0] = 0
            
            plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
            minus_di = abs(100 * (minus_dm.rolling(period).mean() / atr))
            dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
            adx = ((dx.shift(1) * (period - 1)) + dx) / period
            
            self.indicators['adx'] = adx
            self.indicators['plus_di'] = plus_di
            self.indicators['minus_di'] = minus_di
        except Exception as e:
            self.logger.error(f"Erro no cálculo do ADX: {e}")
            raise

    def _calculate_volume_analysis(self, data: pd.DataFrame):
        """Analisa volume"""
        try:
            self.indicators['volume_sma'] = data['volume'].rolling(window=20).mean()
            self.indicators['volume_ratio'] = data['volume'] / self.indicators['volume_sma']
        except Exception as e:
            self.logger.error(f"Erro na análise de volume: {e}")
            raise

    def _analyze_volume_profile(self, data: pd.DataFrame) -> Dict:
        """Analisa o perfil do volume"""
        try:
            volume = data['volume'].values
            close = data['close'].values
            
            avg_volume = np.mean(volume)
            volume_trend = 'increasing' if volume[-1] > avg_volume else 'decreasing'
            volume_strength = volume[-1] / avg_volume
            volume_peaks = np.where(volume > avg_volume * 1.5)[0]
            
            return {
                'trend': volume_trend,
                'strength': volume_strength,
                'peaks': len(volume_peaks),
                'average': avg_volume
            }
        except Exception as e:
            self.logger.error(f"Erro na análise de volume: {e}")
            return {'trend': 'neutral', 'strength': 1.0, 'peaks': 0, 'average': 0}

    def _find_support_resistance(self, data: pd.DataFrame) -> Dict:
        """Encontra níveis de suporte e resistência"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            ma20 = np.mean(close[-20:])
            ma50 = np.mean(close[-50:])
            
            pivot = (high[-1] + low[-1] + close[-1]) / 3
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
            return {'support_1': 0, 'resistance_1': 0, 'ma20': 0, 'ma50': 0, 'pivot': 0}

    def _analyze_rsi(self) -> Dict:
        """Analisa RSI"""
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
            self.logger.error(f"Erro na análise do RSI: {e}")
            return {}

    def _analyze_macd(self) -> Dict:
        """Analisa MACD"""
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
            self.logger.error(f"Erro na análise do MACD: {e}")
            return {}

    def _analyze_bb(self) -> Dict:
        """Analisa Bandas de Bollinger"""
        try:
            if not all(k in self.indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
                return {}
            
            return {
                'upper': self.indicators['bb_upper'].iloc[-1],
                'lower': self.indicators['bb_lower'].iloc[-1],
                'middle': self.indicators['bb_middle'].iloc[-1],
                'width': (self.indicators['bb_upper'].iloc[-1] - 
                         self.indicators['bb_lower'].iloc[-1]) / 
                        self.indicators['bb_middle'].iloc[-1]
            }
        except Exception as e:
            self.logger.error(f"Erro na análise das BBs: {e}")
            return {}

    def _analyze_ema(self) -> Dict:
        """Analisa EMAs"""
        try:
            ema_9 = self.indicators.get('ema_9', pd.Series())
            if ema_9.empty:
                return {}
            
            last_ema_9 = ema_9.iloc[-1]
            last_ema_21 = self.indicators['ema_21'].iloc[-1]
            last_ema_55 = self.indicators['ema_55'].iloc[-1]
            
            if last_ema_9 > last_ema_21 and last_ema_21 > last_ema_55:
                trend = 'bullish'
            elif last_ema_9 < last_ema_21 and last_ema_21 < last_ema_55:
                trend = 'bearish'
            else:
                trend = 'neutral'
                
            return {'trend': trend}
        except Exception as e:
            self.logger.error(f"Erro na análise das EMAs: {e}")
            return {}

    def _analyze_stochastic(self) -> Dict:
        """Analisa Estocástico"""
        try:
            stoch_k = self.indicators.get('stoch_k', pd.Series())
            if stoch_k.empty:
                return {}
            
            last_k = stoch_k.iloc[-1]
            return {
                'value': last_k,
                'oversold': last_k < 20,
                'overbought': last_k > 80
            }
        except Exception as e:
            self.logger.error(f"Erro na análise do Estocástico: {e}")
            return {}

    def _analyze_adx(self) -> Dict:
        """Analisa ADX"""
        try:
            adx = self.indicators.get('adx', pd.Series())
            if adx.empty:
                return {}
            
            last_adx = adx.iloc[-1]
            last_plus_di = self.indicators['plus_di'].iloc[-1]
            last_minus_di = self.indicators['minus_di'].iloc[-1]
            
            return {
                'value': last_adx,
                'trend_strength': last_adx,
                'trend': 'bullish' if last_plus_di > last_minus_di else 'bearish'
            }
        except Exception as e:
            self.logger.error(f"Erro na análise do ADX: {e}")
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
            return 'neutral'
        except Exception as e:
            self.logger.error(f"Erro na análise de tendência: {e}")
            return 'neutral'

    def _check_divergences(self, signals: Dict) -> Dict:
        """Verifica divergências entre indicadores"""
        try:
            price_rsi = False
            price_macd = False
            
            if 'rsi' in signals:
                rsi_trend = 'bullish' if signals['rsi']['value'] > 50 else 'bearish'
                price_rsi = rsi_trend != signals['trend']
            
            if 'macd' in signals:
                macd_trend = 'bullish' if signals['macd']['value'] > 0 else 'bearish'
                price_macd = macd_trend != signals['trend']
            
            divergence_count = sum([price_rsi, price_macd])
            severity = 'high' if divergence_count >= 2 else 'medium' if divergence_count == 1 else 'low'
            
            return {
                'price_rsi': price_rsi,
                'price_macd': price_macd,
                'indicators_sentiment': False,
                'severity': severity
            }
        except Exception as e:
            self.logger.error(f"Erro na verificação de divergências: {e}")
            return {'price_rsi': False, 'price_macd': False, 'indicators_sentiment': False, 'severity': 'low'}

    def _calculate_trend_strength(self, rsi: Dict, macd: Dict, bb: Dict, 
                                volume: Dict, support_resistance: Dict) -> float:
        """Calcula força da tendência"""
        try:
            # Normaliza indicadores
            rsi_strength = (rsi['value'] - 50) / 50
            macd_strength = np.tanh(macd['value'] / 100)
            bb_strength = bb['width']
            vol_strength = volume['strength'] - 1
            
            # Calcula força S/R
            price = support_resistance['pivot']
            sr_range = support_resistance['resistance_1'] - support_resistance['support_1']
            sr_strength = ((price - support_resistance['support_1']) / sr_range) - 0.5 if sr_range != 0 else 0
            
            # Média ponderada
            trend_strength = (
                self.weights['rsi'] * rsi_strength +
                self.weights['macd'] * macd_strength +
                self.weights['bb'] * bb_strength +
                self.weights['volume'] * vol_strength +
                self.weights['sr'] * sr_strength
            )
            
            return np.clip(trend_strength, -1, 1)
        except Exception as e:
            self.logger.error(f"Erro ao calcular força da tendência: {e}")
            return 0.0