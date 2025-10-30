#!/usr/bin/env python3
"""
IQ Option Bot usando la librería OFICIAL ejtraderIQ
Esta librería está diseñada específicamente para bots
"""

import sys
import json
import time
from ejtraderIQ import IQOption

def test_official_api():
    """Test usando la API oficial de IQ Option"""
    
    # Credenciales
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    try:
        print("🚀 Conectando con la API OFICIAL de IQ Option...")
        
        # Conectar usando la librería oficial
        api = IQOption(email, password, 'DEMO')  # DEMO account
        
        print("✅ Conectado exitosamente con la API oficial")
        
        # Verificar balance
        balance = api.balance()
        print(f"💰 Balance DEMO: ${balance}")
        
        # Configurar operación
        symbol = "EURUSD"
        timeframe = "M1"  # 1 minuto
        volume = 1  # $1
        
        print(f"🎯 Ejecutando operación: {symbol} CALL ${volume}")
        
        # EJECUTAR OPERACIÓN REAL usando la API oficial
        trade_id = api.buy(volume, symbol, timeframe)
        
        if trade_id:
            print(f"✅ OPERACIÓN EJECUTADA - ID: {trade_id}")
            
            # Esperar resultado
            print("⏳ Esperando resultado...")
            time.sleep(65)  # Esperar 65 segundos
            
            # Verificar resultado
            win = api.checkwin(trade_id)
            
            if win > 0:
                print("🎉 ¡GANASTE!")
            elif win < 0:
                print("😞 Perdiste")
            else:
                print("🤝 Empate")
                
            return {"success": True, "trade_id": trade_id, "result": win}
        else:
            print("❌ No se pudo ejecutar la operación")
            return {"success": False, "message": "No se pudo ejecutar"}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "message": str(e)}

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python iq_option_official_api.py [test|buy]")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        result = test_official_api()
        print(json.dumps(result))
    elif command == "buy":
        if len(sys.argv) < 5:
            print("Uso: python iq_option_official_api.py buy SYMBOL AMOUNT DIRECTION")
            return
        
        symbol = sys.argv[2]
        amount = float(sys.argv[3])
        direction = sys.argv[4]  # call o put
        
        # Ejecutar operación con la API oficial
        email = "arnolbrom634@gmail.com"
        password = "7decadames"
        
        try:
            api = IQOption(email, password, 'DEMO')
            
            if direction.lower() == 'call':
                trade_id = api.buy(amount, symbol, "M1")
            else:
                trade_id = api.sell(amount, symbol, "M1")
            
            if trade_id:
                result = {"success": True, "trade_id": trade_id}
            else:
                result = {"success": False, "message": "No se pudo ejecutar"}
                
            print(json.dumps(result))
            
        except Exception as e:
            print(json.dumps({"success": False, "message": str(e)}))

if __name__ == "__main__":
    main()
