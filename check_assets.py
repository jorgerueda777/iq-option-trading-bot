#!/usr/bin/env python3
"""
Verificar assets disponibles en IQ Option
"""

from iqoptionapi.stable_api import IQ_Option

def check_available_assets():
    """Verificar assets disponibles"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    try:
        print("🔍 Verificando assets disponibles...")
        
        # Conectar
        api = IQ_Option(email, password)
        check, reason = api.connect()
        
        if check:
            print("✅ Conectado")
            
            # Obtener todos los assets
            all_assets = api.get_all_open_time()
            
            print("\n📊 ASSETS DISPONIBLES:")
            print("=" * 50)
            
            # Buscar assets que contengan AUD, EUR, USD
            for asset_name, asset_info in all_assets['binary'].items():
                if any(currency in asset_name.upper() for currency in ['AUD', 'EUR', 'USD']):
                    status = "🟢 ABIERTO" if asset_info['open'] else "🔴 CERRADO"
                    print(f"{asset_name} - {status}")
            
            print("\n🎯 ASSETS RECOMENDADOS PARA USAR:")
            recommended = ['EURUSD', 'AUDUSD', 'GBPUSD', 'USDJPY', 'USDCAD']
            
            for asset in recommended:
                if asset in all_assets['binary']:
                    status = "🟢 DISPONIBLE" if all_assets['binary'][asset]['open'] else "🔴 CERRADO"
                    print(f"✅ {asset} - {status}")
                else:
                    print(f"❌ {asset} - NO ENCONTRADO")
            
        else:
            print(f"❌ No se pudo conectar: {reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_available_assets()
