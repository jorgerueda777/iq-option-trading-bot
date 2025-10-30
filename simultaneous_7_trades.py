#!/usr/bin/env python3
"""
Ejecutar operaciones SIMULTÁNEAS con los 7 assets que funcionan
"""
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from iqoptionapi.stable_api import IQ_Option

def execute_7_simultaneous_trades():
    """Ejecutar 7 operaciones simultáneas con assets confiables"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    # LOS 7 ASSETS QUE SÍ FUNCIONAN
    working_trades = [
        {"asset": "EURUSD-OTC", "direction": "call", "amount": 1},   # COMPRA
        {"asset": "GBPUSD-OTC", "direction": "put", "amount": 1},    # VENTA
        {"asset": "GBPJPY-OTC", "direction": "call", "amount": 1},   # COMPRA
        {"asset": "EURJPY-OTC", "direction": "put", "amount": 1},    # VENTA
        {"asset": "EURGBP-OTC", "direction": "call", "amount": 1},   # COMPRA
        {"asset": "USDCHF-OTC", "direction": "put", "amount": 1},    # VENTA
        {"asset": "AUDCAD-OTC", "direction": "call", "amount": 1}    # COMPRA
    ]
    
    try:
        print("EJECUTANDO 7 OPERACIONES SIMULTANEAS...")
        print("=" * 70)
        
        # Conectar una sola vez
        api = IQ_Option(email, password)
        check, reason = api.connect()
        
        if not check:
            print(f"No se pudo conectar: {reason}")
            return
        
        # Cambiar a DEMO
        api.change_balance("PRACTICE")
        
        # Verificar balance inicial
        initial_balance = api.get_balance()
        print(f"Balance inicial: ${initial_balance}")
        print()
        
        executed_trades = []
        successful = 0
        
        # FUNCIÓN PARA EJECUTAR UNA OPERACIÓN INDIVIDUAL
        def execute_single_trade(trade_data):
            """Ejecutar una sola operación"""
            asset = trade_data["asset"]
            direction = trade_data["direction"]
            amount = trade_data["amount"]
            
            direction_text = "COMPRA" if direction == "call" else "VENTA"
            
            try:
                print(f"EJECUTANDO: {asset} {direction_text} ${amount}")
                
                # Ejecutar operación - SIEMPRE 1 minuto
                success, trade_id = api.buy(amount, asset, direction, 1)
                
                if success:
                    print(f"EJECUTADA: {asset} - ID: {trade_id}")
                    return {
                        "asset": asset,
                        "direction": direction,
                        "trade_id": trade_id,
                        "status": "success"
                    }
                else:
                    print(f"FALLO: {asset}")
                    return {
                        "asset": asset,
                        "direction": direction,
                        "status": "failed"
                    }
                    
            except Exception as e:
                print(f"ERROR {asset}: {e}")
                return {
                    "asset": asset,
                    "direction": direction,
                    "status": "error",
                    "error": str(e)
                }
        
        # EJECUTAR LAS 7 OPERACIONES SIMULTÁNEAMENTE
        print("EJECUTANDO 7 OPERACIONES AL MISMO TIEMPO...")
        
        # Usar ThreadPoolExecutor para ejecutar todas las operaciones simultáneamente
        with ThreadPoolExecutor(max_workers=7) as executor:
            # Enviar todas las operaciones al pool de threads
            future_to_trade = {executor.submit(execute_single_trade, trade): trade for trade in working_trades}
            
            # Recoger resultados conforme se completan
            for future in as_completed(future_to_trade):
                trade = future_to_trade[future]
                try:
                    result = future.result()
                    executed_trades.append(result)
                    if result["status"] == "success":
                        successful += 1
                except Exception as exc:
                    print(f'ERROR en {trade["asset"]}: {exc}')
                    executed_trades.append({
                        "asset": trade["asset"],
                        "direction": trade["direction"],
                        "status": "error",
                        "error": str(exc)
                    })
        
        print()
        print("RESUMEN DE LAS 7 OPERACIONES:")
        print("=" * 70)
        
        for trade in executed_trades:
            status_icon = "OK" if trade["status"] == "success" else "FALLO"
            direction_text = "COMPRA" if trade["direction"] == "call" else "VENTA"
            
            if trade["status"] == "success":
                print(f"{status_icon} {trade['asset']} {direction_text} - ID: {trade['trade_id']}")
            else:
                print(f"{status_icon} {trade['asset']} {direction_text} - FALLO")
        
        print()
        print(f"EXITOSAS: {successful}/7")
        print(f"FALLIDAS: {7 - successful}/7")
        
        if successful == 7:
            print("PERFECTO! TODAS LAS OPERACIONES EJECUTADAS!")
        elif successful >= 5:
            print("EXCELENTE! Mayoria de operaciones exitosas")
        elif successful >= 3:
            print("BIEN! Varias operaciones exitosas")
        
        # Verificar balance final
        final_balance = api.get_balance()
        print(f"Balance final: ${final_balance}")
        print(f"Invertido: ${initial_balance - final_balance}")
        
        return executed_trades
        
    except Exception as e:
        print(f"Error general: {e}")
        return []

if __name__ == "__main__":
    execute_7_simultaneous_trades()
