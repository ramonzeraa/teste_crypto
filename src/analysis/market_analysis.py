import pandas as pd
import numpy as np
from typing import Dict, List, Union
from datetime import datetime

class AnaliseMercado:
    def __init__(self):
        self.dados = None
        self.metricas = {}
        self.ultima_atualizacao = None
        
    def processar_ohlcv(self, dados: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados OHLCV com cálculos básicos
        
        Args:
            dados: DataFrame com colunas [open, high, low, close, volume]
            
        Returns:
            DataFrame processado com métricas adicionais
        """
        if self.validar_dados(dados):
            self.dados = dados
            self.ultima_atualizacao = datetime.now()
            
            # Cálculos básicos
            self.dados['variacao'] = self.dados['close'].pct_change()
            self.dados['range'] = self.dados['high'] - self.dados['low']
            self.dados['volume_medio'] = self.dados['volume'].rolling(window=20).mean()
            
            return self.dados
        return None
        
    def calcular_metricas(self) -> Dict:
        """
        Calcula métricas básicas do mercado
        
        Returns:
            Dicionário com métricas calculadas
        """
        if self.dados is None:
            return {}
            
        self.metricas = {
            'tendencia': self.calcular_tendencia(),
            'volatilidade': self.calcular_volatilidade(),
            'volume_status': self.analisar_volume(),
            'momentum': self.calcular_momentum()
        }
        
        return self.metricas
        
    def analisar_padroes(self) -> List[Dict]:
        """
        Analisa padrões de mercado
        
        Returns:
            Lista de padrões identificados
        """
        padroes = []
        if self.dados is not None:
            # Identificação de padrões
            if self.identificar_suporte_resistencia():
                padroes.append({
                    'tipo': 'suporte_resistencia',
                    'dados': self.niveis_sr
                })
            
            if self.identificar_tendencia():
                padroes.append({
                    'tipo': 'tendencia',
                    'dados': self.dados_tendencia
                })
                
        return padroes

    def calcular_tendencia(self) -> str:
        """Calcula a tendência atual do mercado"""
        if len(self.dados) < 20:
            return "indefinida"
            
        sma_curta = self.dados['close'].rolling(window=9).mean()
        sma_longa = self.dados['close'].rolling(window=20).mean()
        
        if sma_curta.iloc[-1] > sma_longa.iloc[-1]:
            return "alta"
        elif sma_curta.iloc[-1] < sma_longa.iloc[-1]:
            return "baixa"
        return "lateral"
        
    def calcular_volatilidade(self) -> float:
        """Calcula a volatilidade atual"""
        return self.dados['variacao'].std() * np.sqrt(252)
        
    def analisar_volume(self) -> str:
        """Analisa o status do volume"""
        vol_atual = self.dados['volume'].iloc[-1]
        vol_medio = self.dados['volume_medio'].iloc[-1]
        
        if vol_atual > vol_medio * 1.5:
            return "alto"
        elif vol_atual < vol_medio * 0.5:
            return "baixo"
        return "normal"
        
    def calcular_momentum(self) -> float:
        """Calcula o momentum atual"""
        return (self.dados['close'].iloc[-1] / 
                self.dados['close'].iloc[-10] - 1) * 100

    @staticmethod
    def validar_dados(dados: pd.DataFrame) -> bool:
        """
        Valida a estrutura dos dados de mercado
        
        Args:
            dados: DataFrame a ser validado
            
        Returns:
            bool: True se válido, False caso contrário
        """
        colunas_necessarias = ['open', 'high', 'low', 'close', 'volume']
        return all(col in dados.columns for col in colunas_necessarias)

    def obter_resumo(self) -> Dict:
        """
        Retorna um resumo da análise atual
        
        Returns:
            Dict com resumo das análises
        """
        return {
            'ultima_atualizacao': self.ultima_atualizacao,
            'metricas': self.metricas,
            'padroes': self.analisar_padroes(),
            'status_mercado': {
                'tendencia': self.calcular_tendencia(),
                'volume': self.analisar_volume(),
                'volatilidade': self.calcular_volatilidade()
            }
        }