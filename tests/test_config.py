"""
Testes Unitários para Config
"""
import unittest
from unittest.mock import patch
import os
from datetime import datetime
from pathlib import Path
from src.utils.config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        """Setup para cada teste"""
        self.config = Config()
        
    def test_initialization(self):
        """Testa inicialização das configurações"""
        # Verifica configurações da API
        self.assertIn('api_key', self.config.api_config)
        self.assertIn('api_secret', self.config.api_config)
        
        # Verifica configurações de trading
        self.assertIn('symbol', self.config.trading_config)
        self.assertIn('position_size', self.config.trading_config)
        self.assertIn('stop_loss', self.config.trading_config)
        
        # Verifica configurações do sistema
        self.assertIn('debug_mode', self.config.system_config)
        self.assertIn('log_level', self.config.system_config)
    
    def test_config_validation(self):
        """Testa validação de configurações"""
        # Testa configuração válida
        self.assertTrue(self.config.validate_config())
        
        # Testa configuração inválida
        self.config.trading_config['position_size'] = 2.0  # Valor inválido
        with self.assertRaises(Exception):
            self.config.validate_config()
    
    def test_config_update(self):
        """Testa atualização de configurações"""
        updates = {
            'symbol': 'ETHUSDT',
            'timeframe': '4h',
            'position_size': 0.05
        }
        
        # Atualiza configurações
        self.config.update_config('trading', updates)
        
        # Verifica atualizações
        self.assertEqual(self.config.trading_config['symbol'], 'ETHUSDT')
        self.assertEqual(self.config.trading_config['timeframe'], '4h')
        self.assertEqual(self.config.trading_config['position_size'], 0.05) 
    
    def test_save_load_config(self):
        """Testa salvamento e carregamento de configurações"""
        # Modifica algumas configurações
        self.config.trading_config['symbol'] = 'ETHUSDT'
        self.config.system_config['debug_mode'] = True
        
        # Salva configurações
        test_config_path = 'test_config.json'
        self.config.save_config(test_config_path)
        
        # Cria nova instância e carrega
        new_config = Config()
        new_config.load_config(test_config_path)
        
        # Verifica se configurações foram mantidas
        self.assertEqual(new_config.trading_config['symbol'], 'ETHUSDT')
        self.assertEqual(new_config.system_config['debug_mode'], True)
        
        # Limpa arquivo de teste
        os.remove(test_config_path)
    
    def test_sensitive_data_protection(self):
        """Testa proteção de dados sensíveis"""
        # Obtém configuração segura
        safe_config = self.config.get_config('api')
        
        # Verifica se dados sensíveis estão mascarados
        self.assertEqual(safe_config['api_key'], '***')
        self.assertEqual(safe_config['api_secret'], '***')
        
        # Verifica se dados não sensíveis estão visíveis
        full_config = self.config.get_config()
        self.assertIn('trading', full_config)
        self.assertIn('system', full_config)
    
    def test_invalid_updates(self):
        """Testa atualizações inválidas"""
        # Testa seção inválida
        with self.assertRaises(ValueError):
            self.config.update_config('invalid_section', {})
        
        # Testa valores inválidos
        with self.assertRaises(Exception):
            self.config.update_config('trading', {
                'position_size': -1  # Valor inválido
            })
    
    def test_config_persistence(self):
        """Testa persistência de configurações"""
        config_dir = Path('config')
        config_dir.mkdir(exist_ok=True)
        
        # Salva configurações
        self.config.save_config()
        
        # Verifica se arquivo existe
        self.assertTrue((config_dir / 'settings.json').exists())
        
        # Limpa diretório de teste
        import shutil
        shutil.rmtree(config_dir)
    
    def test_environment_variables(self):
        """Testa integração com variáveis de ambiente"""
        # Simula variáveis de ambiente
        test_env = {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'WHATSAPP_TO': 'test_to',
            'WHATSAPP_FROM': 'test_from'
        }
        
        with patch.dict(os.environ, test_env):
            test_config = Config()
            self.assertEqual(test_config.api_config['api_key'], 'test_key')
            self.assertEqual(test_config.notification_config['twilio_sid'], 'test_sid')
    
    def tearDown(self):
        """Limpeza após cada teste"""
        # Remove arquivos temporários
        for path in Path('.').glob('test_*.json'):
            path.unlink()
        
        if Path('config').exists():
            import shutil
            shutil.rmtree('config')

if __name__ == '__main__':
    unittest.main()