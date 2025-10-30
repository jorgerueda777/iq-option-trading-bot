#!/usr/bin/env python3
"""
Probar sistemáticamente todos los assets para ver cuáles funcionan
"""

import time
from iqoptionapi.stable_api import IQ_Option

def test_all_working_assets():
    """Probar todos los assets disponibles para ver cuáles ejecutan operaciones"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    try:
        print("🔍 PROBANDO TODOS LOS ASSETS DISPONIBLES...")
        print("=" * 70)
        
        # Conectar
        api = IQ_Option(email, password)
        check, reason = api.connect()
        
        if not check:
            print(f"❌ No se pudo conectar: {reason}")
            return
        
        print("✅ Conectado exitosamente")
        
        # Cambiar a DEMO
        api.change_balance("PRACTICE")
        
        # Obtener balance inicial
        initial_balance = api.get_balance()
        print(f"💰 Balance inicial: ${initial_balance}")
        print()
        
        # Obtener todos los assets abiertos
        all_assets = api.get_all_open_time()
        open_assets = []
        
        # Filtrar solo assets abiertos y relevantes (forex principalmente)
        for asset_name, asset_info in all_assets['binary'].items():
            if asset_info['open']:
                # Filtrar assets principales de forex
                if any(currency in asset_name.upper() for currency in ['EUR', 'USD', 'GBP', 'AUD', 'JPY', 'CAD', 'CHF', 'NZD']):
                    if '-OTC' in asset_name or '-op' in asset_name or len(asset_name) == 6:  # EURUSD format
                        open_assets.append(asset_name)
        
        print(f"🎯 ASSETS FOREX ABIERTOS ENCONTRADOS: {len(open_assets)}")
        print("-" * 70)
        
        working_assets = []
        failed_assets = []
        
        # Probar cada asset con una operación pequeña
        for i, asset in enumerate(open_assets[:15], 1):  # Limitar a 15 para no gastar mucho balance
            print(f"🧪 PROBANDO {i}/15: {asset}")
            
            try:
                # Intentar una operación de $1 call por 1 minuto
                success, trade_id = api.buy(1, asset, "call", 1)
                
                if success and trade_id:
                    print(f"✅ FUNCIONA - ID: {trade_id}")
                    working_assets.append(asset)
                    time.sleep(1)  # Pequeña pausa para no saturar
                else:
                    print(f"❌ NO FUNCIONA - success={success}")
                    failed_assets.append(asset)
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)[:50]}...")
                failed_assets.append(asset)
            
            # Pausa entre pruebas
            time.sleep(1)
        
        print()
        print("📊 RESULTADOS FINALES:")
        print("=" * 70)
        
        print(f"✅ ASSETS QUE FUNCIONAN ({len(working_assets)}):")
        for asset in working_assets:
            print(f"   ✅ {asset}")
        
        print()
        print(f"❌ ASSETS QUE NO FUNCIONAN ({len(failed_assets)}):")
        for asset in failed_assets:
            print(f"   ❌ {asset}")
        
        # Balance final
        final_balance = api.get_balance()
        print()
        print(f"💰 Balance final: ${final_balance}")
        print(f"💸 Gastado en pruebas: ${initial_balance - final_balance}")
        
        # Guardar lista de assets que funcionan
        if working_assets:
            print()
            print("🎯 LISTA DE ASSETS CONFIABLES PARA USAR:")
            print("=" * 70)
            print("working_assets = [")
            for asset in working_assets:
                print(f'    "{asset}",')
            print("]")
        
        return working_assets, failed_assets
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return [], []

if __name__ == "__main__":
    test_all_working_assets()
