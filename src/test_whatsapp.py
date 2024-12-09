from twilio.rest import Client
import os
from dotenv import load_dotenv
import time

def test_whatsapp_connection():
    try:
        load_dotenv()
        
        print("\n🔍 Configurações:")
        sid = os.getenv('TWILIO_ACCOUNT_SID')
        token = os.getenv('TWILIO_AUTH_TOKEN')
        print(f"SID: {sid[:6]}...{sid[-4:]}")
        
        # Cria cliente
        client = Client(sid, token)
        
        print("\n📱 Enviando mensagem...")
        
        # Usando exatamente seu número
        message = client.messages.create(
            from_='whatsapp:+14155238886',
            content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
            content_variables='{"1":"12/1","2":"3pm"}',
            to='whatsapp:+556181473793'  # Seu número exato do console
        )
        
        print(f"\nID: {message.sid}")
        
        # Monitora entrega e mostra mais detalhes
        for i in range(1, 4):
            time.sleep(3)
            msg = client.messages(message.sid).fetch()
            print(f"\nTentativa {i}:")
            print(f"Status: {msg.status}")
            print(f"Erro: {msg.error_message if msg.error_message else 'Nenhum'}")
            
            if msg.status == 'delivered':
                print("\n✅ Sucesso!")
                return True
                
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        if hasattr(e, 'msg'):
            print(f"Mensagem: {e.msg}")
        return False

if __name__ == "__main__":
    print("🤖 Teste Final")
    test_whatsapp_connection() 