import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from textblob import TextBlob
import logging
from concurrent.futures import ThreadPoolExecutor

class NewsAnalyzer:
    def __init__(self):
        # APIs de notícias (você precisará se registrar nelas)
        self.apis = {
            'cryptopanic': 'https://cryptopanic.com/api/v1/posts/',
            'newsapi': 'https://newsapi.org/v2/everything'
        }
        self.sentiment_data = {
            'overall_sentiment': 0,
            'recent_news': [],
            'important_events': []
        }
        
    def analyze_news(self) -> Dict:
        """Analisa notícias em tempo real"""
        try:
            # Coleta notícias de múltiplas fontes
            news_data = self._collect_news()
            
            # Analisa sentimento
            self._analyze_sentiment(news_data)
            
            # Identifica eventos importantes
            self._identify_key_events(news_data)
            
            return self.sentiment_data
            
        except Exception as e:
            logging.error(f"Erro na análise de notícias: {e}")
            return {}
    
    def _collect_news(self) -> List[Dict]:
        """Coleta notícias de várias fontes"""
        news_data = []
        
        try:
            with ThreadPoolExecutor() as executor:
                # Coleta paralela de diferentes fontes
                cryptopanic_future = executor.submit(self._get_cryptopanic_news)
                newsapi_future = executor.submit(self._get_newsapi_news)
                
                news_data.extend(cryptopanic_future.result())
                news_data.extend(newsapi_future.result())
                
        except Exception as e:
            logging.error(f"Erro ao coletar notícias: {e}")
            
        return news_data
    
    def _analyze_sentiment(self, news_data: List[Dict]):
        """Analisa o sentimento das notícias"""
        try:
            sentiments = []
            
            for news in news_data:
                # Análise de sentimento usando TextBlob
                blob = TextBlob(news['title'] + ' ' + news['description'])
                sentiment = blob.sentiment.polarity
                sentiments.append(sentiment)
                
                news['sentiment'] = sentiment
            
            # Calcula sentimento geral
            self.sentiment_data['overall_sentiment'] = sum(sentiments) / len(sentiments) if sentiments else 0
            
            # Armazena notícias recentes com sentimento
            self.sentiment_data['recent_news'] = sorted(
                news_data,
                key=lambda x: x['published_at'],
                reverse=True
            )[:10]  # Mantém as 10 notícias mais recentes
            
        except Exception as e:
            logging.error(f"Erro na análise de sentimento: {e}")
    
    def _identify_key_events(self, news_data: List[Dict]):
        """Identifica eventos importantes"""
        try:
            key_words = [
                'halving', 'fork', 'regulation', 'sec', 'etf',
                'hack', 'adoption', 'institutional', 'ban'
            ]
            
            important_events = []
            
            for news in news_data:
                for word in key_words:
                    if word in news['title'].lower() or word in news['description'].lower():
                        important_events.append({
                            'event_type': word,
                            'title': news['title'],
                            'timestamp': news['published_at'],
                            'sentiment': news['sentiment']
                        })
                        break
            
            self.sentiment_data['important_events'] = important_events
            
        except Exception as e:
            logging.error(f"Erro ao identificar eventos importantes: {e}")
    
    def get_market_impact(self) -> Dict:
        """Avalia o possível impacto no mercado"""
        try:
            sentiment = self.sentiment_data['overall_sentiment']
            events = self.sentiment_data['important_events']
            
            impact = {
                'sentiment_score': sentiment,
                'market_direction': 'bullish' if sentiment > 0.2 else 'bearish' if sentiment < -0.2 else 'neutral',
                'important_events': len(events),
                'risk_level': self._calculate_risk_level(events)
            }
            
            return impact
            
        except Exception as e:
            logging.error(f"Erro ao calcular impacto: {e}")
            return {}
    
    def _calculate_risk_level(self, events: List[Dict]) -> str:
        """Calcula nível de risco baseado nos eventos"""
        try:
            high_risk_events = ['hack', 'ban', 'regulation']
            risk_count = sum(1 for event in events if event['event_type'] in high_risk_events)
            
            if risk_count >= 2:
                return 'high'
            elif risk_count == 1:
                return 'medium'
            else:
                return 'low'
                
        except Exception:
            return 'undefined' 