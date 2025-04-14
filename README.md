# 🤖 Robô de Análise de Trades com Criptomoedas usando Inteligência Artificial

Este projeto é um robô de trading inteligente desenvolvido em Python, com foco na análise de dados do mercado de criptomoedas utilizando técnicas de Inteligência Artificial e Machine Learning. O sistema é capaz de coletar dados de mercado, treinar modelos e sugerir ações de compra e venda com base em análises preditivas.

## 📊 Funcionalidades

- Coleta de dados em tempo real de exchanges (via API)  
- Análise técnica com indicadores como RSI, MACD, Médias Móveis, etc.  
- Treinamento de modelos preditivos (Regressão, LSTM, XGBoost, etc.)  
- Sugestões automatizadas de compra e venda  
- Interface de visualização de sinais e tendências  
- Logs e relatórios das decisões do robô  

## 🧠 Tecnologias Utilizadas

- Python 3.12+  
- Pandas, NumPy, Scikit-learn  
- TensorFlow ou PyTorch (para redes neurais)  
- XGBoost  
- ccxt (integração com exchanges)  
- Matplotlib / Plotly  
- Flask (API e interface web)  

## 🚀 Como Executar o Projeto

### 1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/robo-cripto-ia.git
cd robo-cripto-ia
```

### 2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

### 3. Instale as dependências:

```bash
pip install -r requirements.txt
```

### 4. Configure sua API Key da exchange (Ex: Binance) no `.env`.

### 5. Execute a aplicação:

```bash
python main.py
```


## ✅ Requisitos

- Python 3.10 ou superior  
- Conta em uma exchange com API Key  
- Internet estável para coleta em tempo real  

## 📌 Observações

- Este projeto é apenas educacional. Use com cautela em ambientes de produção.  
- Nenhuma decisão de trade deve ser feita exclusivamente com base no robô. Faça sua própria análise!  

## 🧠 Possibilidades de Expansão

- Execução automática de ordens (modo real)  
- Backtesting com históricos personalizados  
- Suporte a múltiplas exchanges simultaneamente  
- Sistema de notificação por e-mail ou Telegram  

## 👨‍💻 Autor

Desenvolvido por Ramon Candido Luz  
📧 ramoncandido64@gmail.com  
🔗 https://www.linkedin.com/in/ramon-c%C3%A2ndido-416b1824b/

---

### ⭐ Se você gostou do projeto, deixe uma estrela no repositório!
