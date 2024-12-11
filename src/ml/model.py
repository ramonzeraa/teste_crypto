from sklearn.linear_model import LinearRegression
import joblib

class TradingModel:
    def __init__(self):
        self.model = LinearRegression()  # Exemplo de modelo
        self.is_trained = False

    def train(self, X, y):
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, X):
        if not self.is_trained:
            raise Exception("Modelo não treinado.")
        return self.model.predict(X)

    def save_model(self, filename):
        joblib.dump(self.model, filename)

    def load_model(self, filename):
        self.model = joblib.load(filename)
        self.is_trained = True