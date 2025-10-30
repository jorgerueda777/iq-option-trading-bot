#!/usr/bin/env python3
"""
Encontrar MÁS assets que funcionen - Estrategia completa
"""

import time
from iqoptionapi.stable_api import IQ_Option

def find_more_working_assets():
    """Estrategia completa para encontrar más assets que funcionen"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    try:
        print("🔍 BÚSQUEDA EXHAUSTIVA DE ASSETS QUE FUNCIONEN...")
        print("=" * 70)
        
        # Conectar
        api = IQ_Option(email, password)
        check, reason = api.connect()
        
        if not check:
            print(f"❌ No se pudo conectar: {reason}")
            return
        
        print("✅ Conectado exitosamente")
        api.change_balance("PRACTICE")
        
        initial_balance = api.get_balance()
        print(f"💰 Balance inicial: ${initial_balance}")
        print()
        
        # ESTRATEGIA 1: Probar assets sin sufijos
        print("🎯 ESTRATEGIA 1: Assets SIN sufijos (-OTC, -op)")
        print("-" * 50)
        
        basic_assets = [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
            "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
            "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "CADCHF",
            "CADJPY", "CHFJPY", "EURAUD", "EURCAD", "EURCHF",
            "EURNZD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD",
            "NZDCAD", "NZDCHF", "NZDJPY"
        ]
        
        working_basic = []
        
        for i, asset in enumerate(basic_assets[:10], 1):  # Probar primeros 10
            print(f"🧪 {i}/10: {asset}")
            try:
                success, trade_id = api.buy(1, asset, "call", 1)
                if success and trade_id:
                    print(f"✅ FUNCIONA - ID: {trade_id}")
                    working_basic.append(asset)
                else:
                    print(f"❌ NO FUNCIONA")
                time.sleep(1)
            except Exception as e:
                print(f"❌ ERROR: {str(e)[:30]}...")
        
        print()
        print("🎯 ESTRATEGIA 2: Assets con diferentes sufijos")
        print("-" * 50)
        
        # Probar diferentes variaciones de assets que sabemos que existen
        variations = []
        base_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "GBPJPY"]
        suffixes = ["", "-OTC", "-op", "_OTC", "_op", "-otc", "-OP"]
        
        for base in base_pairs:
            for suffix in suffixes:
                variations.append(f"{base}{suffix}")
        
        working_variations = []
        
        for i, asset in enumerate(variations[:15], 1):  # Probar 15 variaciones
            print(f"🧪 {i}/15: {asset}")
            try:
                success, trade_id = api.buy(1, asset, "call", 1)
                if success and trade_id:
                    print(f"✅ FUNCIONA - ID: {trade_id}")
                    working_variations.append(asset)
                else:
                    print(f"❌ NO FUNCIONA")
                time.sleep(1)
            except Exception as e:
                print(f"❌ ERROR: {str(e)[:30]}...")
        
        print()
        print("🎯 ESTRATEGIA 3: Assets de crypto populares")
        print("-" * 50)
        
        crypto_assets = [
            "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "ADAUSD",
            "DOTUSD", "LINKUSD", "BCHUSD", "XLMUSD", "EOSUSD"
        ]
        
        working_crypto = []
        
        for i, asset in enumerate(crypto_assets[:5], 1):  # Probar 5 cryptos
            print(f"🧪 {i}/5: {asset}")
            try:
                success, trade_id = api.buy(1, asset, "call", 1)
                if success and trade_id:
                    print(f"✅ FUNCIONA - ID: {trade_id}")
                    working_crypto.append(asset)
                else:
                    print(f"❌ NO FUNCIONA")
                time.sleep(1)
            except Exception as e:
                print(f"❌ ERROR: {str(e)[:30]}...")
        
        # RESULTADOS FINALES
        print()
        print("📊 RESUMEN COMPLETO DE ASSETS QUE FUNCIONAN:")
        print("=" * 70)
        
        all_working = []
        
        # Assets ya conocidos que funcionan
        known_working = ["EURUSD-OTC", "GBPUSD-OTC", "GBPJPY-OTC"]
        all_working.extend(known_working)
        
        # Nuevos encontrados
        all_working.extend(working_basic)
        all_working.extend(working_variations)
        all_working.extend(working_crypto)
        
        # Eliminar duplicados
        all_working = list(set(all_working))
        
        print(f"✅ TOTAL DE ASSETS QUE FUNCIONAN: {len(all_working)}")
        print()
        
        for i, asset in enumerate(all_working, 1):
            print(f"   {i}. ✅ {asset}")
        
        print()
        print("🎯 LISTA FINAL PARA USAR EN EL BOT:")
        print("=" * 70)
        print("working_assets = [")
        for asset in all_working:
            print(f'    "{asset}",')
        print("]")
        
        # Balance final
        final_balance = api.get_balance()
        print()
        print(f"💰 Balance final: ${final_balance}")
        print(f"💸 Gastado en investigación: ${initial_balance - final_balance}")
        
        return all_working
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return []

if __name__ == "__main__":
    find_more_working_assets()
