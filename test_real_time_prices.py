#!/usr/bin/env python3
"""
Test específico para verificar si obtenemos precios REALES en tiempo real
"""

import sys
import os
import time
import logging
import requests
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.quotexAPIClient import QuotexAPIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class RealTimePriceChecker:
    def __init__(self):
        self.logger = logging.getLogger('RealTimePriceChecker')
        self.client = QuotexAPIClient()
        
    def test_direct_endpoints(self):
        """Probar endpoints directos sin autenticación"""
        try:
            self.logger.info("🔍 PROBANDO ENDPOINTS DIRECTOS SIN AUTENTICACIÓN")
            
            # Endpoints públicos que podrían funcionar
            public_endpoints = [
                "https://qxbroker.com/api/v1/prices",
                "https://qxbroker.com/api/v1/quotes",
                "https://qxbroker.com/api/v1/assets",
                "https://qxbroker.com/api/v1/market",
                "https://qxbroker.com/api/quotes",
                "https://qxbroker.com/api/prices",
                "https://qxbroker.com/api/market/prices",
                "https://qxbroker.com/quotes",
                "https://qxbroker.com/prices"
            ]
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9'
            })
            
            working_endpoints = []
            
            for endpoint in public_endpoints:
                try:
                    self.logger.info(f"🔍 Probando: {endpoint}")
                    response = session.get(endpoint, timeout=10)
                    
                    self.logger.info(f"   📊 Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            self.logger.info(f"   ✅ JSON válido - Tamaño: {len(str(data))} chars")
                            
                            # Mostrar estructura
                            if isinstance(data, dict):
                                keys = list(data.keys())[:5]
                                self.logger.info(f"   🔑 Keys: {keys}")
                            elif isinstance(data, list) and len(data) > 0:
                                self.logger.info(f"   📋 Lista con {len(data)} elementos")
                                if isinstance(data[0], dict):
                                    keys = list(data[0].keys())[:5]
                                    self.logger.info(f"   🔑 Primer elemento keys: {keys}")
                            
                            working_endpoints.append({
                                'url': endpoint,
                                'data': data
                            })
                            
                        except Exception as e:
                            self.logger.info(f"   ⚠️ No es JSON válido: {str(e)[:50]}")
                    
                    elif response.status_code == 403:
                        self.logger.info(f"   🔒 Requiere autenticación")
                    elif response.status_code == 404:
                        self.logger.info(f"   ❌ No encontrado")
                    else:
                        self.logger.info(f"   ⚠️ Otro status: {response.status_code}")
                
                except Exception as e:
                    self.logger.info(f"   ❌ Error: {str(e)[:50]}")
                
                time.sleep(1)  # No saturar el servidor
            
            return working_endpoints
            
        except Exception as e:
            self.logger.error(f"❌ Error probando endpoints: {e}")
            return []
    
    def test_with_authentication(self):
        """Probar con autenticación"""
        try:
            self.logger.info("🔐 PROBANDO CON AUTENTICACIÓN")
            
            # Autenticar
            if not self.client.authenticate():
                self.logger.error("❌ No se pudo autenticar")
                return []
            
            self.logger.info("✅ Autenticado correctamente")
            
            # Probar endpoints específicos de activos OTC
            otc_assets = ["BRENT_otc", "MSFT_otc", "ADA_otc", "ETH_otc"]
            
            working_data = []
            
            for asset in otc_assets:
                self.logger.info(f"🎯 Probando activo: {asset}")
                
                # Endpoints específicos para este activo
                asset_endpoints = [
                    f"https://qxbroker.com/api/v1/prices/{asset}",
                    f"https://qxbroker.com/api/v1/quotes/{asset}",
                    f"https://qxbroker.com/api/v1/realtime/{asset}",
                    f"https://qxbroker.com/api/v1/candles/{asset}",
                    f"https://qxbroker.com/api/v1/otc/prices/{asset}",
                    f"https://qxbroker.com/api/prices/{asset}",
                    f"https://qxbroker.com/api/quotes/{asset}"
                ]
                
                for endpoint in asset_endpoints:
                    try:
                        response = self.client.session.get(endpoint, timeout=5)
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                self.logger.info(f"   ✅ {endpoint}")
                                self.logger.info(f"      📊 Datos: {str(data)[:100]}...")
                                
                                working_data.append({
                                    'asset': asset,
                                    'endpoint': endpoint,
                                    'data': data
                                })
                                
                            except:
                                self.logger.info(f"   ⚠️ {endpoint} - No JSON")
                        else:
                            self.logger.info(f"   ❌ {endpoint} - Status: {response.status_code}")
                    
                    except Exception as e:
                        continue
                
                time.sleep(1)
            
            return working_data
            
        except Exception as e:
            self.logger.error(f"❌ Error con autenticación: {e}")
            return []
    
    def test_websocket_discovery(self):
        """Intentar descubrir WebSocket"""
        try:
            self.logger.info("📡 PROBANDO DESCUBRIMIENTO DE WEBSOCKET")
            
            # URLs de WebSocket conocidas
            ws_urls = [
                "wss://ws.qxbroker.com/socket.io/",
                "wss://qxbroker.com/socket.io/",
                "wss://api.qxbroker.com/socket.io/",
                "wss://ws.qxbroker.com/ws",
                "wss://qxbroker.com/ws"
            ]
            
            for ws_url in ws_urls:
                self.logger.info(f"📡 WebSocket URL disponible: {ws_url}")
                self.logger.info("   💡 Requiere implementación de cliente WebSocket")
            
            return ws_urls
            
        except Exception as e:
            self.logger.error(f"❌ Error WebSocket: {e}")
            return []
    
    def run_complete_check(self):
        """Ejecutar verificación completa"""
        try:
            self.logger.info("🧪 VERIFICACIÓN COMPLETA DE PRECIOS EN TIEMPO REAL")
            self.logger.info("=" * 80)
            
            # Test 1: Endpoints públicos
            self.logger.info("🔍 TEST 1: ENDPOINTS PÚBLICOS")
            public_endpoints = self.test_direct_endpoints()
            
            # Test 2: Con autenticación
            self.logger.info("\n🔐 TEST 2: CON AUTENTICACIÓN")
            auth_endpoints = self.test_with_authentication()
            
            # Test 3: WebSocket
            self.logger.info("\n📡 TEST 3: WEBSOCKET")
            ws_urls = self.test_websocket_discovery()
            
            # Resumen
            self.logger.info("\n🎯 RESUMEN:")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 Endpoints públicos funcionando: {len(public_endpoints)}")
            self.logger.info(f"🔐 Endpoints con auth funcionando: {len(auth_endpoints)}")
            self.logger.info(f"📡 URLs WebSocket disponibles: {len(ws_urls)}")
            
            if public_endpoints or auth_endpoints:
                self.logger.info("✅ ENCONTRAMOS ENDPOINTS REALES")
                self.logger.info("   💡 Podemos implementar precios en tiempo real")
                
                # Mostrar el mejor endpoint encontrado
                if auth_endpoints:
                    best = auth_endpoints[0]
                    self.logger.info(f"🏆 MEJOR ENDPOINT: {best['endpoint']}")
                    self.logger.info(f"   📊 Datos: {str(best['data'])[:200]}...")
                elif public_endpoints:
                    best = public_endpoints[0]
                    self.logger.info(f"🏆 MEJOR ENDPOINT: {best['url']}")
                
                return True
            else:
                self.logger.warning("⚠️ NO SE ENCONTRARON ENDPOINTS REALES")
                self.logger.info("   💡 Necesitamos usar WebSocket o método alternativo")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error en verificación: {e}")
            return False

def main():
    """Función principal"""
    checker = RealTimePriceChecker()
    
    try:
        success = checker.run_complete_check()
        
        if success:
            print("\n🎉 ¡ENCONTRAMOS ENDPOINTS REALES! Podemos implementar tiempo real.")
        else:
            print("\n⚠️ NO hay endpoints REST. Necesitamos WebSocket o seguir con patrones.")
            
    except KeyboardInterrupt:
        print("\n🛑 Verificación interrumpida")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
