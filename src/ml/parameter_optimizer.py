from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
from scipy.optimize import minimize
import logging
from src.database.database import Database
from sklearn.ensemble import RandomForestRegressor
import joblib

class ParameterOptimizer:
    def __init__(self):
        self.logger = logging.getLogger('parameter_optimizer')
        self.db = Database()
        self.model = self._load_or_create_model()
        self.performance_history = []
        
    def _load_or_create_model(self):
        """Carrega modelo existente ou cria um novo"""
        try:
            return joblib.load('model_state.joblib')
        except:
            return RandomForestRegressor(n_estimators=100)

    def optimize_parameters(self, historical_data: Dict, current_params: Dict) -> Dict:
        """Otimiza parâmetros baseado em dados históricos"""
        try:
            self.logger.info("Iniciando otimização de parâmetros...")
            
            # Mantém os parâmetros atuais como base
            optimized_params = current_params.copy()
            
            # Prepara dados
            X = self._prepare_features(historical_data)
            y = self._calculate_targets(historical_data)
            
            # Verifica se temos dados suficientes para prever
            if X.shape[0] < 1 or X.shape[1] < 8:
                self.logger.warning("Dados insuficientes para otimização")
                return current_params
            
            # Treina modelo com novos dados
            self.model.fit(X, y)
            
            # Prediz ajustes para cada parâmetro
            predictions = self.model.predict(X[-1].reshape(1, -1))
            
            # Verifica se temos previsões suficientes
            if len(predictions) < 8:
                self.logger.warning("Previsões insuficientes, mantendo parâmetros atuais")
                return current_params
            
            # Ajusta parâmetros mantendo limites seguros
            optimized_params['rsi_period'] = max(5, min(50, int(round(predictions[0]))))
            optimized_params['macd_fast'] = max(5, min(50, int(round(predictions[1]))))
            optimized_params['macd_slow'] = max(10, min(100, int(round(predictions[2]))))
            optimized_params['macd_signal'] = max(5, min(50, int(round(predictions[3]))))
            optimized_params['bb_period'] = max(5, min(50, int(round(predictions[4]))))
            optimized_params['bb_std'] = max(1.0, min(4.0, predictions[5]))
            optimized_params['stoch_period'] = max(5, min(50, int(round(predictions[6]))))
            optimized_params['adx_period'] = max(5, min(50, int(round(predictions[7]))))
            
            # Avalia performance
            score = self._evaluate_parameters(optimized_params, X, y)
            
            # Salva histórico
            self._update_performance_history(optimized_params, score)
            
            # Salva no banco de dados
            self._save_performance(optimized_params, score, historical_data)
            
            return optimized_params
            
        except Exception as e:
            self.logger.error(f"Erro na otimização: {str(e)}")
            return current_params

    def _prepare_features(self, data: Dict) -> np.array:
        """Prepara features para otimização"""
        prices = np.array(data['prices'])
        volumes = np.array(data['volumes'])
        
        # Calcula features
        returns = np.diff(prices) / prices[:-1]
        vol_changes = np.diff(volumes) / volumes[:-1]
        volatility = np.std(returns[-20:])
        
        # Combina features
        features = np.column_stack((
            returns,
            vol_changes,
            np.abs(returns),
            np.abs(vol_changes),
            np.full_like(returns, volatility)
        ))
        
        return features

    def _calculate_targets(self, data: Dict) -> np.array:
        """Calcula targets para otimização"""
        prices = np.array(data['prices'])
        future_returns = np.diff(prices) / prices[:-1]
        return np.sign(future_returns)

    def _evaluate_parameters(self, params: Dict, X: np.array, y: np.array) -> float:
        """Avalia performance dos parâmetros"""
        try:
            predictions = self._simulate_trading(X, list(params.values()))
            score = np.mean(predictions == y)
            return float(score)
        except Exception as e:
            self.logger.error(f"Erro na avaliação: {str(e)}")
            return 0.0

    def _save_performance(self, params: Dict, score: float, market_data: Dict):
        """Salva performance no banco de dados"""
        try:
            # Converte arrays numpy para listas
            market_data_serializable = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in market_data.items()}
            
            self.db.save_performance(
                params,
                score,
                market_data_serializable,
                {'timestamp': datetime.now().isoformat()}
            )
        except Exception as e:
            self.logger.error(f"Erro ao salvar performance: {str(e)}")

    def _update_performance_history(self, params: Dict, score: float):
        """Atualiza histórico de performance em memória"""
        self.performance_history.append({
            'parameters': params.copy(),
            'score': score,
            'timestamp': datetime.now()
        })
        
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)

    def _simulate_trading(self, X: np.array, params: List[float]) -> np.array:
        """Simula trading com conjunto de parâmetros"""
        try:
            signals = np.zeros(len(X))
            
            # Simula decisões de trading
            for i in range(len(X)):
                if X[i, 0] > params[0]:  # Retorno > threshold
                    signals[i] = 1
                elif X[i, 0] < -params[0]:
                    signals[i] = -1
                    
            return signals
            
        except Exception as e:
            self.logger.error(f"Erro na simulação: {str(e)}")
            return np.zeros(len(X))