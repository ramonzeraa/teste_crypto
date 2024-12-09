import pandas as pd
import logging
from dataclasses import dataclass

@dataclass
class MarketAnalysis:
    def analyze_market_conditions(self, df: pd.DataFrame) -> dict:
        """Análise completa das condições de mercado"""
        try:
            # Verifica se precisamos calcular os indicadores
            if 'EMA20' not in df.columns:
                df = self._calculate_indicators(df)
                
            # Adicionar análise multi-timeframe
            timeframes = ['1m', '5m', '15m', '1h', '4h']
            analysis = {}
            
            for tf in timeframes:
                tf_data = self.resample_data(df, tf)
                analysis[tf] = self._analyze_timeframe(tf_data)
            
            return analysis
        except Exception as e:
            logging.error(f"Erro na análise de mercado: {str(e)}")
            return {
                'tendencia': 'INDEFINIDA',
                'suporte_resistencia': {'suporte': 0, 'resistencia': 0},
                'volatilidade': 0,
                'momentum': 0
            }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores se não existirem"""
        from ta.trend import EMAIndicator
        
        df = df.copy()
        if 'EMA20' not in df.columns:
            df['EMA20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
        if 'EMA50' not in df.columns:
            df['EMA50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
        return df
    
    def _analise_tendencia(self, df: pd.DataFrame) -> str:
        try:
            if 'EMA20' not in df.columns or 'EMA50' not in df.columns:
                df = self._calculate_indicators(df)
                
            ema20 = df['EMA20'].iloc[-1]
            ema50 = df['EMA50'].iloc[-1]
            preco_atual = df['close'].iloc[-1]
            
            if preco_atual > ema20 > ema50:
                return "FORTE_ALTA"
            elif preco_atual < ema20 < ema50:
                return "FORTE_BAIXA"
            return "LATERAL"
        except Exception as e:
            logging.error(f"Erro na análise de tendência: {str(e)}")
            return "INDEFINIDA"
    
    def _calc_suporte_resistencia(self, df: pd.DataFrame) -> dict:
        try:
            return {
                'suporte': df['low'].tail(20).min(),
                'resistencia': df['high'].tail(20).max()
            }
        except Exception as e:
            logging.error(f"Erro no cálculo de suporte/resistência: {str(e)}")
            return {'suporte': 0, 'resistencia': 0}
    
    def _calc_volatilidade(self, df: pd.DataFrame) -> float:
        try:
            return df['close'].pct_change().std() * 100
        except Exception as e:
            logging.error(f"Erro no cálculo de volatilidade: {str(e)}")
            return 0.0
    
    def _calc_momentum(self, df: pd.DataFrame) -> float:
        try:
            return ((df['close'].iloc[-1] / df['close'].iloc[-20]) - 1) * 100
        except Exception as e:
            logging.error(f"Erro no cálculo de momentum: {str(e)}")
            return 0.0