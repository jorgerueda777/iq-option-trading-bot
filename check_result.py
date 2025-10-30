#!/usr/bin/env python3
"""
Verificar resultado de operación
"""

from iqoptionapi.stable_api import IQ_Option

def check_trade_result():
    """Verificar resultado de la operación"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    trade_id = 13243067163  # ID de la operación
    
    try:
        print("🔍 Verificando resultado de la operación...")
        
        # Conectar
        api = IQ_Option(email, password)
        check, reason = api.connect()
        
        if check:
            print("✅ Conectado")
            
            # Cambiar a DEMO
            api.change_balance("PRACTICE")
            
            # Verificar resultado
            result = api.check_win_v3(trade_id)
            
            print(f"📊 Resultado de la operación {trade_id}:")
            
            if result > 0:
                print("🎉 ¡GANASTE!")
            elif result < 0:
                print("😞 Perdiste")
            else:
                print("🤝 Empate o aún en progreso")
                
            # Verificar balance actual
            balance = api.get_balance()
            print(f"💰 Balance actual: ${balance}")
            
        else:
            print(f"❌ No se pudo conectar: {reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_trade_result()
