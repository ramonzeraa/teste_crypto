# Guia de Configuração

## 1. Ambiente de Desenvolvimento

### Requisitos Básicos
- Python 3.9+
- Git
- pip (gerenciador de pacotes Python)
- Conta Binance
- Conta Twilio (para alertas)

### Setup Inicial 
    Clone o repositório
    git clone https://github.com/ramonzeraa/robo_crypto.git

    cd robo_crypto

### Crie e ative ambiente virtual
    python -m venv venv
    source venv/bin/activate # Linux/Mac
    ou
    venv\Scripts\activate # Windows
### Instale dependências
    pip install -r requirements.txt

## 2. Configuração das APIs

### Binance API
    1. Acesse sua conta Binance
    2. Vá em API Management
    3. Crie nova API key
    4. Configure restrições:
    - Apenas leitura
    - IP fixo (recomendado)
    - Futures trading

### Twilio (Alertas)
    1. Crie conta no Twilio
    2. Obtenha credenciais
    3. Configure número de WhatsApp

### Arquivo .env
    BINANCE
        BINANCE_API_KEY=sua_api_key
        BINANCE_API_SECRET=seu_api_secret
    Twilio
        TWILIO_ACCOUNT_SID=seu_sid
        TWILIO_AUTH_TOKEN=seu_token
        TWILIO_PHONE_NUMBER=seu_numero
    Configurações Bot
        TRADE_MODE=paper # paper/live
        RISK_LEVEL=conservative # conservative/aggressive
        MAX_POSITION_SIZE=0.01 # em BTC

## 3. Verificação do Setup

### Teste de Conexão
```python
python -m tests.test_connection
```

### Teste de Alertas
```python
python -m tests.test_alerts
```

## 4. Logs e Monitoramento

### Estrutura de Logs
- `/logs/system.log`: Logs do sistema
- `/logs/trades.log`: Logs de operações
- `/logs/errors.log`: Logs de erros
- `paper_trades_log.csv`: Registro de simulações

### Monitoramento
    - Verificar logs diariamente
    - Monitorar uso de recursos
    - Acompanhar performance