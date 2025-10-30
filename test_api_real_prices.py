#!/usr/bin/env python3
"""
Test API Quotex - Verificar precios en tiempo real
Prueba específica para validar que la API obtiene datos reales
"""

import sys
import os
import time
import logging
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.quotexAPIClient import QuotexAPIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexAPIPriceTester:
    def __init__(self):
        self.logger = logging.getLogger('QuotexAPIPriceTester')
        self.client = QuotexAPIClient()
        self.test_assets = ["UK BRENT", "MICROSOFT", "ADA", "ETH"]
        
    def test_authentication(self):
        """Probar autenticación"""
        try:
            self.logger.info("🔐 PROBANDO AUTENTICACIÓN...")
            
            result = self.client.authenticate()
            
            if result:
                self.logger.info("✅ AUTENTICACIÓN EXITOSA")
                self.logger.info(f"   🔗 Autenticado: {self.client.is_authenticated}")
                return True
            else:
                self.logger.error("❌ AUTENTICACIÓN FALLIDA")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en autenticación: {e}")
            return False
    
    def test_assets_list(self):
        """Probar obtención de lista de activos"""
        try:
            self.logger.info("📊 PROBANDO LISTA DE ACTIVOS...")
            
            assets = self.client.get_assets_list()
            
            if assets:
                self.logger.info(f"✅ ACTIVOS OBTENIDOS: {len(assets)}")
                
                # Mostrar primeros 5 activos
                for i, asset in enumerate(assets[:5]):
                    if isinstance(asset, dict):
                        name = asset.get('name', 'Unknown')
                        asset_id = asset.get('id', 'Unknown')
                        self.logger.info(f"   📈 {i+1}. {name} (ID: {asset_id})")
                    else:
                        self.logger.info(f"   📈 {i+1}. {asset}")
                
                return True
            else:
                self.logger.warning("⚠️ No se obtuvieron activos")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo activos: {e}")
            return False
    
    def test_single_price(self, asset_name):
        """Probar obtención de precio individual"""
        try:
            self.logger.info(f"💰 PROBANDO PRECIO: {asset_name}")
            
            price_data = self.client.get_live_price(asset_name)
            
            if price_data:
                price = price_data.get("price", "N/A")
                direction = price_data.get("direction", "N/A")
                source = price_data.get("source", "N/A")
                timestamp = price_data.get("timestamp", "N/A")
                
                self.logger.info(f"✅ {asset_name}:")
                self.logger.info(f"   💵 Precio: {price}")
                self.logger.info(f"   📈 Dirección: {direction}")
                self.logger.info(f"   🔗 Fuente: {source}")
                self.logger.info(f"   ⏰ Timestamp: {timestamp}")
                
                # Verificar que NO sea simulado
                if source == "simulated":
                    self.logger.warning(f"⚠️ {asset_name}: DATOS SIMULADOS DETECTADOS")
                    return False
                else:
                    self.logger.info(f"✅ {asset_name}: DATOS REALES CONFIRMADOS")
                    return True
            else:
                self.logger.warning(f"⚠️ {asset_name}: No se obtuvo precio")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo precio {asset_name}: {e}")
            return False
    
    def test_multiple_prices(self):
        """Probar obtención de múltiples precios"""
        try:
            self.logger.info("💰 PROBANDO MÚLTIPLES PRECIOS...")
            
            results = {}
            
            for asset in self.test_assets:
                success = self.test_single_price(asset)
                results[asset] = success
                time.sleep(2)  # Esperar entre requests
            
            # Resumen
            successful = sum(results.values())
            total = len(results)
            
            self.logger.info("📊 RESUMEN DE PRECIOS:")
            self.logger.info("=" * 60)
            
            for asset, success in results.items():
                status = "✅ REAL" if success else "❌ FALLO"
                self.logger.info(f"   {asset}: {status}")
            
            self.logger.info(f"📈 Éxito: {successful}/{total} ({successful/total*100:.0f}%)")
            
            return successful > 0
            
        except Exception as e:
            self.logger.error(f"❌ Error en prueba múltiple: {e}")
            return False
    
    def test_real_time_updates(self):
        """Probar actualizaciones en tiempo real"""
        try:
            self.logger.info("⏰ PROBANDO ACTUALIZACIONES EN TIEMPO REAL...")
            self.logger.info("   📊 Obteniendo precios cada 5 segundos por 30 segundos")
            
            asset = "UK BRENT"  # Activo de prueba
            previous_prices = []
            
            for i in range(6):  # 6 iteraciones x 5 segundos = 30 segundos
                price_data = self.client.get_live_price(asset)
                
                if price_data:
                    current_price = price_data.get("price")
                    direction = price_data.get("direction")
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    self.logger.info(f"🔄 {i+1}/6 - {timestamp}: {asset} = {current_price:.6f} ({direction})")
                    
                    if current_price:
                        previous_prices.append(current_price)
                else:
                    self.logger.warning(f"⚠️ {i+1}/6 - No se obtuvo precio")
                
                if i < 5:  # No esperar en la última iteración
                    time.sleep(5)
            
            # Analizar variaciones
            if len(previous_prices) >= 2:
                variations = []
                for i in range(1, len(previous_prices)):
                    variation = abs(previous_prices[i] - previous_prices[i-1])
                    variations.append(variation)
                
                avg_variation = sum(variations) / len(variations)
                max_variation = max(variations)
                
                self.logger.info("📊 ANÁLISIS DE VARIACIONES:")
                self.logger.info(f"   📈 Precios obtenidos: {len(previous_prices)}")
                self.logger.info(f"   📊 Variación promedio: {avg_variation:.6f}")
                self.logger.info(f"   📊 Variación máxima: {max_variation:.6f}")
                
                # Verificar que hay variaciones reales (no datos estáticos)
                if max_variation > 0:
                    self.logger.info("✅ PRECIOS CAMBIAN EN TIEMPO REAL - DATOS REALES CONFIRMADOS")
                    return True
                else:
                    self.logger.warning("⚠️ PRECIOS ESTÁTICOS - POSIBLES DATOS SIMULADOS")
                    return False
            else:
                self.logger.warning("⚠️ No se obtuvieron suficientes precios para análisis")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en prueba tiempo real: {e}")
            return False
    
    def run_complete_test(self):
        """Ejecutar prueba completa de la API"""
        try:
            self.logger.info("🧪 INICIANDO PRUEBA COMPLETA DE API QUOTEX")
            self.logger.info("=" * 80)
            
            results = {}
            
            # Test 1: Autenticación
            self.logger.info("🔐 TEST 1: AUTENTICACIÓN")
            results['auth'] = self.test_authentication()
            
            if not results['auth']:
                self.logger.error("❌ PRUEBA ABORTADA - Sin autenticación no se puede continuar")
                return False
            
            # Test 2: Lista de activos
            self.logger.info("\n📊 TEST 2: LISTA DE ACTIVOS")
            results['assets'] = self.test_assets_list()
            
            # Test 3: Precios individuales
            self.logger.info("\n💰 TEST 3: PRECIOS INDIVIDUALES")
            results['prices'] = self.test_multiple_prices()
            
            # Test 4: Tiempo real
            self.logger.info("\n⏰ TEST 4: ACTUALIZACIONES EN TIEMPO REAL")
            results['realtime'] = self.test_real_time_updates()
            
            # Resumen final
            self.logger.info("\n🎯 RESUMEN FINAL:")
            self.logger.info("=" * 80)
            
            total_tests = len(results)
            passed_tests = sum(results.values())
            
            for test_name, result in results.items():
                status = "✅ PASÓ" if result else "❌ FALLÓ"
                self.logger.info(f"   {test_name.upper()}: {status}")
            
            success_rate = passed_tests / total_tests * 100
            self.logger.info(f"\n📈 TASA DE ÉXITO: {passed_tests}/{total_tests} ({success_rate:.0f}%)")
            
            if success_rate >= 75:
                self.logger.info("🎉 API QUOTEX FUNCIONANDO CORRECTAMENTE")
                self.logger.info("✅ LISTO PARA TRADING AUTOMÁTICO")
                return True
            else:
                self.logger.warning("⚠️ API QUOTEX TIENE PROBLEMAS")
                self.logger.warning("❌ NO RECOMENDADO PARA TRADING AUTOMÁTICO")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en prueba completa: {e}")
            return False

def main():
    """Función principal"""
    tester = QuotexAPIPriceTester()
    
    try:
        success = tester.run_complete_test()
        
        if success:
            print("\n🎉 ¡PRUEBA EXITOSA! La API obtiene precios reales.")
        else:
            print("\n⚠️ PRUEBA FALLIDA. La API necesita correcciones.")
            
    except KeyboardInterrupt:
        print("\n🛑 Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")

if __name__ == "__main__":
    main()
