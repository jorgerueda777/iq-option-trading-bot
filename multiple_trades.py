#!/usr/bin/env python3
"""
Ejecutar múltiples operaciones simultáneamente
"""

import time
from iqoptionapi.stable_api import IQ_Option

def execute_multiple_trades():
    """Ejecutar múltiples operaciones"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    # Lista de operaciones a ejecutar
    trades = [
        {"asset": "AUDUSD-OTC", "direction": "call", "amount": 1},   # COMPRA
        {"asset": "EURUSD-OTC", "direction": "put", "amount": 1},    # VENTA
        {"asset": "GBPUSD-OTC", "direction": "call", "amount": 1},   # COMPRA
        {"asset": "USDJPY-OTC", "direction": "put", "amount": 1},    # VENTA
        {"asset": "USDCAD-OTC", "direction": "call", "amount": 1}    # COMPRA
    ]
    
    try:
        print("🚀 EJECUTANDO OPERACIONES MÚLTIPLES...")
        print("=" * 60)
        
        # Conectar una sola vez
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
        
        # Ejecutar cada operación
        for i, trade in enumerate(trades, 1):
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
                    executed_trades.append({
                        "asset": asset,
                        "direction": direction,
                        "amount": amount,
                        "trade_id": trade_id,
                        "status": "success"
                    })
                else:
                    print(f"❌ FALLÓ")
                    executed_trades.append({
                        "asset": asset,
                        "direction": direction,
                        "amount": amount,
                        "trade_id": None,
                        "status": "failed"
                    })
                
                # Pequeña pausa entre operaciones
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                executed_trades.append({
                    "asset": asset,
                    "direction": direction,
                    "amount": amount,
                    "trade_id": None,
                    "status": "error",
                    "error": str(e)
                })
        
        print()
        print("📊 RESUMEN DE OPERACIONES:")
        print("=" * 60)
        
        successful = 0
        failed = 0
        
        for trade in executed_trades:
            status_icon = "✅" if trade["status"] == "success" else "❌"
            direction_text = "📈 COMPRA" if trade["direction"] == "call" else "📉 VENTA"
            
            if trade["status"] == "success":
                print(f"{status_icon} {trade['asset']} {direction_text} - ID: {trade['trade_id']}")
                successful += 1
            else:
                print(f"{status_icon} {trade['asset']} {direction_text} - FALLÓ")
                failed += 1
        
        print()
        print(f"🎉 EXITOSAS: {successful}/5")
        print(f"❌ FALLIDAS: {failed}/5")
        
        # Verificar balance final
        final_balance = api.get_balance()
        print(f"💰 Balance final: ${final_balance}")
        
        return executed_trades
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return []

if __name__ == "__main__":
    execute_multiple_trades()
