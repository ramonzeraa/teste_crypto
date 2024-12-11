import websocket
import json
import time  # Importar a biblioteca time para usar sleep
from src.ml.parameter_optimizer import ParameterOptimizer  # Importar o otimizador
from src.ml.backtesting import Backtester  # Importar o backtester
from src.ml.model import TradingModel  # Importar o modelo

class RealTimeTrader:
    def __init__(self):
        self.optimizer = ParameterOptimizer()
        self.model = TradingModel()
        self.backtester = Backtester(self.model)
        self.prices = []  # Lista para armazenar os preços
        self.last_signal = None  # Armazena o último sinal enviado
        self.rsi_period = 14  # Período para o cálculo do RSI
        self.gains = []  # Lista para armazenar os ganhos
        self.losses = []  # Lista para armazenar as perdas

    def calculate_rsi(self):
        if len(self.prices) < self.rsi_period:
            return None  # Não há dados suficientes para calcular o RSI

        # Calcula as variações de preço
        deltas = [self.prices[i] - self.prices[i - 1] for i in range(1, len(self.prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]

        # Calcula a média dos ganhos e perdas
        avg_gain = sum(gains[-self.rsi_period:]) / self.rsi_period
        avg_loss = sum(losses[-self.rsi_period:]) / self.rsi_period

        # Verifica se a média de perdas é zero para evitar divisão por zero
        if avg_loss == 0:
            return 100  # Se não houver perdas, o RSI é 100

        # Calcula o RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def on_message(self, ws, message):
        data = json.loads(message)
        self.process_data(data)

    def on_error(self, ws, error):
        print(f"Erro: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("Conexão fechada")

    def on_open(self, ws):
        print("Conexão aberta")

    def process_data(self, data):
        price = float(data['p'])  # Preço da transação
        quantity = float(data['q'])  # Quantidade da transação
        print(f"Preço: {price}, Quantidade: {quantity}")

        # Armazena o preço recebido
        self.prices.append(price)

        # Calcula o RSI
        rsi = self.calculate_rsi()
        if rsi is not None:
            print(f"RSI: {rsi}")

            # Lógica de trading baseada no RSI
            if rsi < 30 and self.last_signal != "buy":  # Condição de sobrevenda
                print("Sinal de compra!")
                self.last_signal = "buy"
            elif rsi > 70 and self.last_signal != "sell":  # Condição de sobrecompra
                print("Sinal de venda!")
                self.last_signal = "sell"

    def run(self):
        while True:  # Loop para manter a conexão
            try:
                ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                            on_message=self.on_message,
                                            on_error=self.on_error,
                                            on_close=self.on_close)

                ws.on_open = self.on_open
                ws.run_forever()  # Mantém a conexão aberta
            except KeyboardInterrupt:
                print("Encerrado pelo usuário.")
                break  # Encerra o loop
            except Exception as e:
                print(f"Erro na conexão: {e}. Tentando reconectar...")
                for attempt in range(5):  # Limita a 5 tentativas de reconexão
                    time.sleep(5)  # Espera 5 segundos antes de tentar reconectar
                    try:
                        ws.run_forever()
                        break  # Se a reconexão for bem-sucedida, sai do loop
                    except Exception as e:
                        print(f"Tentativa {attempt + 1} falhou: {e}")
                else:
                    print("Todas as tentativas de reconexão falharam. Encerrando.")
                    break  # Encerra se todas as tentativas falharem