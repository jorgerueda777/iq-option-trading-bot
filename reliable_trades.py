#!/usr/bin/env python3
"""
Ejecutar operaciones solo con assets CONFIABLES que funcionan
"""

import time
from iqoptionapi.stable_api import IQ_Option

def execute_reliable_trades():
    """Ejecutar operaciones solo con assets que sabemos que funcionan"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    # ASSETS CONFIABLES que sabemos que funcionan
    reliable_trades = [
        {"asset": "EURUSD-OTC", "direction": "call", "amount": 1},   # COMPRA
        {"asset": "EURUSD-OTC", "direction": "put", "amount": 1},    # VENTA
        {"asset": "GBPUSD-OTC", "direction": "call", "amount": 1},   # COMPRA
        {"asset": "GBPUSD-OTC", "direction": "put", "amount": 1},    # VENTA
        {"asset": "EURUSD-OTC", "direction": "call", "amount": 1}    # COMPRA
    ]
    
    try:
        print("🚀 EJECUTANDO OPERACIONES CON ASSETS CONFIABLES...")
        print("=" * 60)
        
        # Conectar
        api = IQ_Option(email, password)
        check, reason = api.connect()
        
        if not check:
            print(f"❌ No se pudo conectar: {reason}")
            return
        
        # Cambiar a DEMO
        api.change_balance("PRACTICE")
        
        # Verificar balance inicial
        initial_balance = api.get_balance()
        print(f"💰 Balance inicial: ${initial_balance}")
        print()
        
        executed_trades = []
        successful = 0
        
        # Ejecutar cada operación
        for i, trade in enumerate(reliable_trades, 1):
            asset = trade["asset"]
            direction = trade["direction"]
            amount = trade["amount"]
            
            direction_text = "📈 COMPRA" if direction == "call" else "📉 VENTA"
            
            print(f"🎯 {i}/5 - {asset} {direction_text} ${amount}")
            
            try:
                # Ejecutar operación - SIEMPRE 1 minuto
                success, trade_id = api.buy(amount, asset, direction, 1)
                
                if success:
                    print(f"✅ EJECUTADA - ID: {trade_id}")
                    successful += 1
                    executed_trades.append({
                        "asset": asset,
                        "direction": direction,
                        "trade_id": trade_id,
                        "status": "success"
                    })
                else:
                    print(f"❌ FALLÓ")
                    executed_trades.append({
                        "asset": asset,
                        "direction": direction,
                        "status": "failed"
                    })
                
                # Pausa entre operaciones
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                executed_trades.append({
                    "asset": asset,
                    "direction": direction,
                    "status": "error",
                    "error": str(e)
                })
        
        print()
        print("📊 RESUMEN FINAL:")
        print("=" * 60)
        print(f"🎉 EXITOSAS: {successful}/5")
        print(f"❌ FALLIDAS: {5 - successful}/5")
        
        # Balance final
        final_balance = api.get_balance()
        print(f"💰 Balance final: ${final_balance}")
        
        return executed_trades
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return []

if __name__ == "__main__":
    execute_reliable_trades()
