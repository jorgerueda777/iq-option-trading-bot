#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from iqoptionapi.stable_api import IQ_Option

def execute_dynamic_trades(signals_data):
    """Ejecutar operaciones dinámicas basadas en señales reales"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    # Parsear las señales recibidas
    try:
        import json
        signals = json.loads(signals_data)
    except:
        print("Error: No se pudieron parsear las señales")
        return []
    
    try:
        print(f"EJECUTANDO {len(signals)} OPERACIONES DINAMICAS INVERTIDAS...")
        print("*** MODO INVERSO ACTIVADO: HACEMOS LO CONTRARIO DE LAS SEÑALES ***")
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
        def execute_single_trade(signal):
            """Ejecutar operación con ESTRATEGIA DE ALTERNANCIA"""
            asset = signal["asset"]
            original_direction = signal["direction"].lower()  # call o put
            
            # *** ESTRATEGIA DE ALTERNANCIA ***
            # Determinar si es minuto par o impar
            from datetime import datetime
            current_minute = datetime.now().minute
            is_even_minute = (current_minute % 2 == 0)
            
            # EJECUTAR SIEMPRE COMO MANDA EL BOT (SIN INVERSIÓN)
            direction = original_direction
            if original_direction == "call":
                direction_text = "COMPRA (COMO MANDA EL BOT)"
            else:
                direction_text = "VENTA (COMO MANDA EL BOT)"
            strategy_mode = "DIRECTO"
            
            amount = 1  # Siempre $1
            
            try:
                print(f"*** ESTRATEGIA DE ALTERNANCIA ***")
                print(f"MINUTO ACTUAL: {current_minute} ({'PAR' if is_even_minute else 'IMPAR'}) - MODO: {strategy_mode}")
                print(f"SEÑAL ORIGINAL: {asset} {original_direction.upper()}")
                print(f"EJECUTANDO: {asset} {direction_text} ${amount}")
                print(f"API CALL: api.buy({amount}, {asset}, {direction}, 0.5)")
                
                
                # Ejecutar operación - CAMBIADO A 30 SEGUNDOS
                success, trade_id = api.buy(amount, asset, direction, 0.5)
                
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
        
        # EJECUTAR LAS OPERACIONES SIMULTÁNEAMENTE
        print(f"EJECUTANDO {len(signals)} OPERACIONES AL MISMO TIEMPO...")
        
        # Usar ThreadPoolExecutor para ejecutar todas las operaciones simultáneamente
        with ThreadPoolExecutor(max_workers=len(signals)) as executor:
            # Enviar todas las operaciones al pool de threads
            future_to_signal = {executor.submit(execute_single_trade, signal): signal for signal in signals}
            
            # Recoger resultados conforme se completan
            for future in as_completed(future_to_signal):
                signal = future_to_signal[future]
                try:
                    result = future.result()
                    executed_trades.append(result)
                    if result["status"] == "success":
                        successful += 1
                except Exception as exc:
                    print(f'ERROR en {signal["asset"]}: {exc}')
                    executed_trades.append({
                        "asset": signal["asset"],
                        "direction": signal["direction"],
                        "status": "error",
                        "error": str(exc)
                    })
        
        print()
        print(f"RESUMEN DE LAS {len(signals)} OPERACIONES:")
        print("=" * 70)
        
        for trade in executed_trades:
            status_icon = "OK" if trade["status"] == "success" else "FALLO"
            direction_text = "COMPRA" if trade["direction"] == "call" else "VENTA"
            
            if trade["status"] == "success":
                print(f"{status_icon} {trade['asset']} {direction_text} - ID: {trade['trade_id']}")
            else:
                print(f"{status_icon} {trade['asset']} {direction_text} - FALLO")
        
        print()
        print(f"EXITOSAS: {successful}/{len(signals)}")
        print(f"FALLIDAS: {len(signals) - successful}/{len(signals)}")
        
        
        if successful == len(signals):
            print("PERFECTO! TODAS LAS OPERACIONES EJECUTADAS!")
        elif successful >= len(signals) * 0.7:
            print("EXCELENTE! Mayoria de operaciones exitosas")
        elif successful >= 1:
            print("BIEN! Algunas operaciones exitosas")
        
        # Verificar balance final
        final_balance = api.get_balance()
        print(f"Balance final: ${final_balance}")
        print(f"Invertido: ${initial_balance - final_balance}")
        
        return executed_trades
        
    except Exception as e:
        print(f"Error general: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        signals_json = sys.argv[1]
        execute_dynamic_trades(signals_json)
    else:
        print("Error: Se requieren las señales como parámetro")
