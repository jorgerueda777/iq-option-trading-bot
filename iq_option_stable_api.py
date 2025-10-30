#!/usr/bin/env python3
"""
IQ Option Bot usando la librería OFICIAL iqoptionapi
Esta es la librería más usada y estable para bots
"""

import sys
import json
import time
from iqoptionapi.stable_api import IQ_Option

def test_stable_api():
    """Test usando la API estable de IQ Option"""
    
    # Credenciales
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    try:
        print("Conectando con la API ESTABLE de IQ Option...")
        
        # Conectar usando la librería oficial estable
        api = IQ_Option(email, password)
        
        # Conectar
        check, reason = api.connect()
        
        if check:
            print("Conectado exitosamente con la API estable")
            
            # Cambiar a cuenta DEMO
            api.change_balance("PRACTICE")  # PRACTICE = DEMO
            
            # Verificar balance
            balance = api.get_balance()
            print(f"Balance DEMO: ${balance}")
            
            # Configurar operación
            asset = "EURUSD-OTC"
            amount = 1  # $1
            direction = "call"  # call o put
            duration = 1  # SIEMPRE 1 minuto exacto
            
            print(f"Ejecutando operacion: {asset} {direction.upper()} ${amount}")
            
            # EJECUTAR OPERACIÓN REAL usando la API oficial
            success, trade_id = api.buy(amount, asset, direction, duration)
            
            if success:
                print(f"OPERACION EJECUTADA - ID: {trade_id}")
                
                # Esperar resultado
                print("Esperando resultado...")
                time.sleep(65)  # Esperar 65 segundos
                
                # Verificar resultado
                result = api.check_win_v3(trade_id)
                
                if result > 0:
                    print("GANASTE!")
                elif result < 0:
                    print("Perdiste")
                else:
                    print("Empate")
                    
                return {"success": True, "trade_id": trade_id, "result": result}
            else:
                print("No se pudo ejecutar la operacion")
                return {"success": False, "message": "No se pudo ejecutar"}
        else:
            print(f" No se pudo conectar: {reason}")
            return {"success": False, "message": reason}
            
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "message": str(e)}

def execute_trade(asset, amount, direction):
    """Ejecutar operación específica - SIEMPRE 1 minuto exacto"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    try:
        print(f"Ejecutando {asset} {direction} ${amount} - DURACION: 1 MINUTO EXACTO")
        
        # Conectar
        api = IQ_Option(email, password)
        check, reason = api.connect()
        
        if not check:
            return {"success": False, "message": f"No se pudo conectar: {reason}"}
        
        # Cambiar a DEMO
        api.change_balance("PRACTICE")
        
        # Ejecutar operación - SIEMPRE 1 minuto exacto
        duration = 1  # FORZAR 1 minuto siempre
        success, trade_id = api.buy(amount, asset, direction, duration)
        
        if success:
            print(f"OPERACION EJECUTADA - ID: {trade_id}")
            return {"success": True, "trade_id": trade_id}
        else:
            return {"success": False, "message": "No se pudo ejecutar la operacion"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python iq_option_stable_api.py [test|buy]")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        result = test_stable_api()
        print(json.dumps(result))
        
    elif command == "buy":
        if len(sys.argv) < 5:
            print("Uso: python iq_option_stable_api.py buy ASSET AMOUNT DIRECTION")
            return
        
        asset = sys.argv[2]
        amount = float(sys.argv[3])
        direction = sys.argv[4].lower()
        
        result = execute_trade(asset, amount, direction)
        print(json.dumps(result))

if __name__ == "__main__":
    main()
