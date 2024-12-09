import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class MLAnalyzer:
    def __init__(self):
        self.technical_scaler = StandardScaler()
        self.sentiment_scaler = StandardScaler()
        self.rf_model = RandomForestClassifier(n_estimators=100)
        self.gb_model = GradientBoostingRegressor()
        self.prediction_history = []
        self.accuracy_metrics = {'rf': [], 'gb': []}
    
    def prepare_data(self, technical_data: Dict, news_data: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara dados para o modelo"""
        try:
            # Características técnicas
            technical_features = np.array([
                technical_data['indicators']['rsi'],
                technical_data['indicators']['macd_line'],
                technical_data['indicators']['bb_high'],
                technical_data['indicators']['bb_low'],
                technical_data['strength']
            ]).reshape(1, -1)
            
            # Características de sentimento
            sentiment_features = np.array([
                news_data['overall_sentiment'],
                len(news_data['important_events']),
                news_data.get('market_impact', {}).get('risk_level', 0)
            ]).reshape(1, -1)
            
            # Normalização
            technical_scaled = self.technical_scaler.fit_transform(technical_features)
            sentiment_scaled = self.sentiment_scaler.fit_transform(sentiment_features)
            
            return technical_scaled, sentiment_scaled
            
        except Exception as e:
            logging.error(f"Erro na preparação dos dados: {e}")
            return None, None
    
    def predict(self, technical_data: Dict, news_data: Dict) -> Dict:
        """Faz previsões usando múltiplos modelos"""
        try:
            technical_scaled, sentiment_scaled = self.prepare_data(technical_data, news_data)
            if technical_scaled is None or sentiment_scaled is None:
                return {}
            
            # Combina características
            combined_features = np.concatenate([technical_scaled, sentiment_scaled], axis=1)
            
            # Previsões
            predictions = {
                'direction': self.rf_model.predict(combined_features)[0],
                'price_change': self.gb_model.predict(combined_features)[0],
                'confidence': self._calculate_confidence(combined_features)
            }
            
            # Registra previsão
            self._log_prediction(predictions)
            
            return predictions
            
        except Exception as e:
            logging.error(f"Erro nas previsões: {e}")
            return {}
    
    def learn(self, features: Dict, actual_outcome: float):
        """Aprende com os resultados reais"""
        try:
            technical_scaled, sentiment_scaled = self.prepare_data(
                features['technical'],
                features['news']
            )
            
            if technical_scaled is None or sentiment_scaled is None:
                return
            
            combined_features = np.concatenate([technical_scaled, sentiment_scaled], axis=1)
            
            # Atualiza modelos
            self.rf_model.fit(combined_features, [actual_outcome > 0])
            self.gb_model.fit(combined_features, [actual_outcome])
            
            # Atualiza métricas
            self._update_accuracy_metrics(actual_outcome)
            
        except Exception as e:
            logging.error(f"Erro no aprendizado: {e}")
    
    def _calculate_confidence(self, features: np.ndarray) -> float:
        """Calcula nível de confiança da previsão"""
        try:
            rf_proba = self.rf_model.predict_proba(features)[0]
            confidence = max(rf_proba)
            return float(confidence)
            
        except Exception:
            return 0.5
    
    def _log_prediction(self, prediction: Dict):
        """Registra previsão para análise posterior"""
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'prediction': prediction
        })
        
        # Mantém apenas últimas 1000 previsões
        if len(self.prediction_history) > 1000:
            self.prediction_history.pop(0)
    
    def _update_accuracy_metrics(self, actual_outcome: float):
        """Atualiza métricas de precisão"""
        try:
            if self.prediction_history:
                last_prediction = self.prediction_history[-1]['prediction']
                
                # Atualiza métricas para cada modelo
                predicted_direction = last_prediction['direction']
                actual_direction = actual_outcome > 0
                
                self.accuracy_metrics['rf'].append(predicted_direction == actual_direction)
                
                # Mantém apenas últimas 100 métricas
                for metric_list in self.accuracy_metrics.values():
                    if len(metric_list) > 100:
                        metric_list.pop(0)
                        
        except Exception as e:
            logging.error(f"Erro na atualização de métricas: {e}")
    
    def get_performance_metrics(self) -> Dict:
        """Retorna métricas de performance dos modelos"""
        try:
            return {
                'rf_accuracy': np.mean(self.accuracy_metrics['rf']) if self.accuracy_metrics['rf'] else 0,
                'prediction_count': len(self.prediction_history),
                'confidence_trend': self._calculate_confidence_trend()
            }
        except Exception as e:
            logging.error(f"Erro ao calcular métricas: {e}")
            return {}
    
    def _calculate_confidence_trend(self) -> float:
        """Calcula tendência da confiança nas últimas previsões"""
        try:
            if len(self.prediction_history) < 10:
                return 0
                
            recent_confidence = [
                p['prediction']['confidence'] 
                for p in self.prediction_history[-10:]
            ]
            return float(np.mean(recent_confidence))
            
        except Exception:
            return 0 