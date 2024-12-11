import pandas as pd
from .model import TradingModel

def train_model(data):
    # Supondo que 'data' seja um DataFrame com as colunas 'features' e 'target'
    X = data[['feature1', 'feature2']]  # Substitua pelos nomes reais das features
    y = data['target']  # Substitua pelo nome real do target

    model = TradingModel()
    model.train(X, y)
    model.save_model('model_state.joblib')  # Salvar o modelo treinado