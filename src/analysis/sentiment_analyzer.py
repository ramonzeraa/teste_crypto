from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from textblob import TextBlob
import requests
import json
from concurrent.futures import ThreadPoolExecutor

class SentimentAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger('sentiment_analyzer')
        self.sentiment_cache = {}
        self.sources = {
            'fear_greed': 'https://api.alternative.me/fng/',
            # Outras APIs podem ser adicionadas aqui
        }
        self.cache_duration = timedelta(minutes=15)
    
    def analyze_market_sentiment(self) -> Dict:
        """Analisa o sentimento do mercado"""
        try:
            # Obtém Fear & Greed Index
            fear_greed = self._get_fear_greed_index()
            
            # Analisa tendência de volume
            volume_trend = self._analyze_volume_trend()
            
            # Analisa price action
            price_action = self._analyze_price_action()
            
            # Timestamp da análise
            timestamp = datetime.now()
            
            # Calcula score geral
            overall_score = (
                fear_greed['value'] / 100 * 0.4 +  # 40% peso
                volume_trend['strength'] * 0.3 +    # 30% peso
                price_action['momentum'] * 0.3      # 30% peso
            )
            
            return {
                'fear_greed_index': fear_greed,
                'volume_trend': volume_trend,
                'price_action': price_action,
                'timestamp': timestamp,
                'overall': overall_score
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de sentimento: {str(e)}")
            return {}
    
    def _get_fear_greed_index(self) -> Dict:
        """Obtém índice Fear & Greed"""
        try:
            response = requests.get(self.sources['fear_greed'])
            data = response.json()
            
            return {
                'value': int(data['data'][0]['value']),
                'classification': data['data'][0]['value_classification'],
                'timestamp': datetime.fromtimestamp(int(data['data'][0]['timestamp']))
            }
            
        except Exception as e:
            logging.error(f"Erro ao obter Fear & Greed: {e}")
            return {'value': 50, 'classification': 'neutral'}
    
    def _analyze_volume_trend(self) -> Dict:
        """Analisa tendência do volume"""
        try:
            # Aqui você usaria o BinanceDataLoader para obter dados
            # Por enquanto, retornamos um exemplo
            return {
                'trend': 'increasing',
                'strength': 0.75,
                'unusual_activity': False
            }
            
        except Exception as e:
            logging.error(f"Erro na análise de volume: {e}")
            return {'trend': 'neutral', 'strength': 0.5}
    
    def _analyze_price_action(self) -> Dict:
        """Analisa ação do preço"""
        try:
            # Aqui você usaria o BinanceDataLoader para obter dados
            # Por enquanto, retornamos um exemplo
            return {
                'trend': 'bullish',
                'momentum': 0.65,
                'volatility': 'moderate'
            }
            
        except Exception as e:
            logging.error(f"Erro na análise de preço: {e}")
            return {'trend': 'neutral', 'momentum': 0.5}
    
    def _calculate_overall_sentiment(self, data: Dict) -> float:
        """Calcula sentimento geral"""
        try:
            # Fear & Greed (0-100) para (-1 a 1)
            fear_greed = (data['fear_greed_index']['value'] - 50) / 50
            
            # Volume (-1 a 1)
            volume_score = 1 if data['volume_trend']['trend'] == 'increasing' else -1
            volume_score *= data['volume_trend']['strength']
            
            # Preço (-1 a 1)
            price_score = 1 if data['price_action']['trend'] == 'bullish' else -1
            price_score *= data['price_action']['momentum']
            
            # Média ponderada
            weights = [0.4, 0.3, 0.3]  # Fear&Greed, Volume, Preço
            overall = np.average([fear_greed, volume_score, price_score], 
                               weights=weights)
            
            return float(np.clip(overall, -1, 1))
            
        except Exception as e:
            logging.error(f"Erro no cálculo de sentimento: {e}")
            return 0.0
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Verifica se cache está válido"""
        if symbol not in self.sentiment_cache:
            return False
            
        cache_age = datetime.now() - self.sentiment_cache[symbol]['timestamp']
        return cache_age < self.cache_duration
    
    def _get_default_sentiment(self) -> Dict:
        """Retorna sentimento padrão em caso de erro"""
        return {
            'fear_greed_index': {'value': 50, 'classification': 'neutral'},
            'volume_trend': {'trend': 'neutral', 'strength': 0.5},
            'price_action': {'trend': 'neutral', 'momentum': 0.5},
            'overall': 0.0,
            'timestamp': datetime.now()
        } 