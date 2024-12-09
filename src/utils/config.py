from dotenv import load_dotenv
import os

class Config:
    def __init__(self):
        load_dotenv()
        
        # Binance configs
        self.binance_api_key = os.getenv('BINANCE_API_KEY')
        self.binance_api_secret = os.getenv('BINANCE_API_SECRET')
        
        # Twilio configs
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_to = os.getenv('WHATSAPP_TO')
        self.whatsapp_from = os.getenv('WHATSAPP_FROM')
        
    def validate(self):
        """Valida se todas as configurações necessárias estão presentes"""
        required_vars = [
            'BINANCE_API_KEY',
            'BINANCE_API_SECRET',
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'WHATSAPP_TO',
            'WHATSAPP_FROM'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Variáveis de ambiente faltando: {', '.join(missing)}")