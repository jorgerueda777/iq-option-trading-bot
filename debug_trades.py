#!/usr/bin/env python3
"""
Debug detallado para entender por qué fallan las operaciones
"""

import time
from iqoptionapi.stable_api import IQ_Option

def debug_individual_trades():
    """Probar cada asset individualmente para ver el error específico"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    # Assets que fallaron
    failed_assets = [
        {"asset": "AUDUSD-OTC", "direction": "call"},
        {"asset": "USDJPY-OTC", "direction": "put"},
        {"asset": "USDCAD-OTC", "direction": "call"}
    ]
    
    try:
        print("🔍 DEBUG DETALLADO DE ASSETS QUE FALLARON...")
        print("=" * 60)
        
        # Conectar
        api = IQ_Option(email, password)
        check, reason = api.connect()
        
        if not check:
            print(f"❌ No se pudo conectar: {reason}")
            return
        
        print("✅ Conectado exitosamente")
        
        # Cambiar a DEMO
        api.change_balance("PRACTICE")
        print("✅ Cambiado a cuenta DEMO")
        
        # Verificar balance
        balance = api.get_balance()
        print(f"💰 Balance disponible: ${balance}")
        print()
        
        # Probar cada asset individualmente
        for i, trade in enumerate(failed_assets, 1):
            asset = trade["asset"]
            direction = trade["direction"]
            
            print(f"🎯 PROBANDO {i}/3: {asset} {direction.upper()}")
            print("-" * 40)
            
            try:
                # Verificar si el asset está disponible
                all_assets = api.get_all_open_time()
                
                if asset in all_assets['binary']:
                    asset_status = all_assets['binary'][asset]
                    if asset_status['open']:
                        print(f"✅ {asset} está ABIERTO")
                    else:
                        print(f"❌ {asset} está CERRADO")
                        continue
                else:
                    print(f"❌ {asset} NO EXISTE en la lista")
                    continue
                
                # Intentar ejecutar la operación
                print(f"🚀 Ejecutando {asset} {direction} $1...")
                
                success, trade_id = api.buy(1, asset, direction, 1)
                
                if success:
                    print(f"✅ ÉXITO - ID: {trade_id}")
                else:
                    print(f"❌ FALLÓ - success=False")
                    
                    # Intentar obtener más información del error
                    try:
                        # Verificar balance después del intento
                        current_balance = api.get_balance()
                        print(f"💰 Balance después del intento: ${current_balance}")
                        
                        # Verificar si hay algún mensaje de error
                        print("🔍 Verificando posibles restricciones...")
                        
                    except Exception as detail_error:
                        print(f"❌ Error obteniendo detalles: {detail_error}")
                
            except Exception as e:
                print(f"❌ EXCEPCIÓN: {str(e)}")
                print(f"🔍 Tipo de error: {type(e).__name__}")
            
            print()
            time.sleep(2)  # Pausa entre pruebas
        
        print("📊 DEBUG COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    debug_individual_trades()
