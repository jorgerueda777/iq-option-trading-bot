#!/usr/bin/env python3
"""
Quotex Simple API Discovery
Método simple para descubrir endpoints reales de Quotex
"""

import sys
import time
import logging
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexSimpleDiscovery:
    def __init__(self):
        self.driver = None
        
    def setup_simple_chrome(self):
        """Configurar Chrome simple"""
        try:
            logging.info("🛡️ Configurando Chrome simple...")
            
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.maximize_window()
            
            logging.info("✅ Chrome configurado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome: {e}")
            return False
    
    def open_quotex_with_devtools(self):
        """Abrir Quotex y mostrar instrucciones para DevTools"""
        try:
            logging.info("🌐 Abriendo Quotex...")
            self.driver.get("https://qxbroker.com/")
            time.sleep(5)
            
            logging.info("🔍 INSTRUCCIONES PARA DESCUBRIR LA API:")
            logging.info("=" * 80)
            logging.info("1. 🖱️  Presiona F12 para abrir DevTools")
            logging.info("2. 📊 Ve a la pestaña 'Network' (Red)")
            logging.info("3. ✅ Asegúrate de que esté grabando (botón rojo)")
            logging.info("4. 🔄 Recarga la página (F5)")
            logging.info("5. 👤 Haz login con:")
            logging.info("   📧 Email: arnolbrom634@gmail.com")
            logging.info("   🔑 Password: 7decadames")
            logging.info("6. 🔍 En Network, busca requests que contengan:")
            logging.info("   - 'api'")
            logging.info("   - 'auth' o 'login'")
            logging.info("   - 'price' o 'asset'")
            logging.info("   - 'websocket' o 'ws'")
            logging.info("7. 📋 Copia las URLs importantes y pégalas aquí")
            logging.info("=" * 80)
            
            # Esperar input del usuario
            logging.info("⏰ Esperando que hagas login y explores...")
            logging.info("   Presiona ENTER cuando hayas terminado de explorar")
            input()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error abriendo Quotex: {e}")
            return False
    
    def extract_javascript_globals(self):
        """Extraer variables globales de JavaScript"""
        try:
            logging.info("🧠 EXTRAYENDO VARIABLES GLOBALES DE JAVASCRIPT...")
            
            js_code = """
            try {
                let globals = {};
                
                // Buscar variables globales relacionadas con trading
                let keywords = ['quotex', 'api', 'socket', 'price', 'asset', 'trade', 'auth', 'user', 'config'];
                
                for (let key in window) {
                    try {
                        let value = window[key];
                        let keyLower = key.toLowerCase();
                        
                        // Buscar por keywords
                        for (let keyword of keywords) {
                            if (keyLower.includes(keyword)) {
                                globals[key] = {
                                    type: typeof value,
                                    value: typeof value === 'object' ? JSON.stringify(value).substring(0, 200) : String(value).substring(0, 100)
                                };
                                break;
                            }
                        }
                    } catch (e) {
                        // Ignorar errores de acceso
                    }
                }
                
                // Buscar en localStorage
                let storage = {};
                try {
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        if (key) {
                            let keyLower = key.toLowerCase();
                            for (let keyword of keywords) {
                                if (keyLower.includes(keyword)) {
                                    storage[key] = localStorage.getItem(key).substring(0, 100);
                                    break;
                                }
                            }
                        }
                    }
                } catch (e) {}
                
                // Buscar configuraciones de red
                let networkInfo = {
                    location: window.location.href,
                    origin: window.location.origin,
                    userAgent: navigator.userAgent.substring(0, 100)
                };
                
                return {
                    globals: globals,
                    storage: storage,
                    network: networkInfo,
                    timestamp: Date.now()
                };
                
            } catch (error) {
                return { error: error.message };
            }
            """
            
            result = self.driver.execute_script(js_code)
            
            if result and not result.get('error'):
                logging.info("📊 VARIABLES GLOBALES ENCONTRADAS:")
                
                if result.get('globals'):
                    globals_data = result['globals']
                    logging.info(f"🌐 Variables globales: {len(globals_data)}")
                    for key, data in globals_data.items():
                        logging.info(f"   🔧 {key}: {data['type']}")
                        logging.info(f"      Valor: {data['value']}")
                
                if result.get('storage'):
                    storage_data = result['storage']
                    logging.info(f"💾 LocalStorage: {len(storage_data)}")
                    for key, value in storage_data.items():
                        logging.info(f"   📦 {key}: {value}")
                
                if result.get('network'):
                    network_data = result['network']
                    logging.info(f"🌐 Información de red:")
                    logging.info(f"   📍 URL: {network_data['location']}")
                    logging.info(f"   🏠 Origin: {network_data['origin']}")
            
            return result
            
        except Exception as e:
            logging.error(f"❌ Error extrayendo JavaScript: {e}")
            return None
    
    def manual_endpoint_collection(self):
        """Recopilar endpoints manualmente del usuario"""
        try:
            logging.info("📝 RECOPILACIÓN MANUAL DE ENDPOINTS:")
            logging.info("=" * 60)
            
            endpoints = []
            
            logging.info("🔍 Por favor, pega las URLs de API que encontraste:")
            logging.info("   (Una por línea, presiona ENTER en línea vacía para terminar)")
            
            while True:
                url = input("URL: ").strip()
                if not url:
                    break
                
                if url.startswith('http'):
                    endpoints.append(url)
                    logging.info(f"✅ Agregado: {url}")
                else:
                    logging.warning(f"⚠️ URL inválida: {url}")
            
            if endpoints:
                logging.info(f"📊 Total endpoints recopilados: {len(endpoints)}")
                
                # Guardar endpoints
                output_file = "D:/iq_quot/manual_quotex_endpoints.json"
                data = {
                    "collection_timestamp": time.time(),
                    "total_endpoints": len(endpoints),
                    "endpoints": endpoints
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                logging.info(f"💾 Endpoints guardados en: {output_file}")
            
            return endpoints
            
        except Exception as e:
            logging.error(f"❌ Error recopilando endpoints: {e}")
            return []
    
    def test_common_endpoints(self):
        """Probar endpoints comunes de Quotex"""
        try:
            logging.info("🧪 PROBANDO ENDPOINTS COMUNES...")
            
            # Endpoints comunes que suelen usar las plataformas de trading
            common_endpoints = [
                "https://qxbroker.com/api/login",
                "https://qxbroker.com/api/auth",
                "https://qxbroker.com/api/user",
                "https://qxbroker.com/api/assets",
                "https://qxbroker.com/api/prices",
                "https://qxbroker.com/api/trade",
                "https://api.qxbroker.com/login",
                "https://api.qxbroker.com/auth",
                "https://api.qxbroker.com/assets",
                "https://api.qxbroker.com/prices",
                "https://ws.qxbroker.com/socket.io/",
                "wss://ws.qxbroker.com/socket.io/"
            ]
            
            import requests
            
            working_endpoints = []
            
            for endpoint in common_endpoints:
                try:
                    if endpoint.startswith('ws'):
                        logging.info(f"🌐 WebSocket: {endpoint} (no se puede probar con requests)")
                        continue
                    
                    response = requests.get(endpoint, timeout=5)
                    status = response.status_code
                    
                    if status != 404:  # Si no es 404, podría ser válido
                        working_endpoints.append({
                            "url": endpoint,
                            "status": status,
                            "content_type": response.headers.get('content-type', 'unknown')
                        })
                        logging.info(f"✅ {status} {endpoint}")
                    else:
                        logging.info(f"❌ {status} {endpoint}")
                
                except Exception as e:
                    logging.info(f"⚠️ Error {endpoint}: {str(e)[:50]}")
            
            if working_endpoints:
                logging.info(f"📊 Endpoints que responden: {len(working_endpoints)}")
                return working_endpoints
            else:
                logging.info("❌ No se encontraron endpoints que respondan")
                return []
            
        except Exception as e:
            logging.error(f"❌ Error probando endpoints: {e}")
            return []
    
    def run_simple_discovery(self):
        """Ejecutar descubrimiento simple"""
        try:
            logging.info("🕵️ INICIANDO DESCUBRIMIENTO SIMPLE DE API QUOTEX")
            logging.info("=" * 80)
            
            # 1. Configurar Chrome
            if not self.setup_simple_chrome():
                return False
            
            # 2. Abrir Quotex con instrucciones
            if not self.open_quotex_with_devtools():
                return False
            
            # 3. Extraer JavaScript
            self.extract_javascript_globals()
            
            # 4. Recopilar endpoints manualmente
            manual_endpoints = self.manual_endpoint_collection()
            
            # 5. Probar endpoints comunes
            common_endpoints = self.test_common_endpoints()
            
            # 6. Resumen
            logging.info("🎯 RESUMEN DEL DESCUBRIMIENTO:")
            logging.info("=" * 60)
            logging.info(f"📝 Endpoints manuales: {len(manual_endpoints)}")
            logging.info(f"🧪 Endpoints comunes que responden: {len(common_endpoints)}")
            
            if manual_endpoints or common_endpoints:
                logging.info("✅ ¡Descubrimiento exitoso!")
                logging.info("   Ahora podemos crear una API client real")
            else:
                logging.info("⚠️ No se encontraron endpoints")
                logging.info("   Necesitamos más investigación manual")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error en descubrimiento: {e}")
            return False
        finally:
            if self.driver:
                logging.info("🔍 Cerrando en 5 segundos...")
                time.sleep(5)
                self.driver.quit()

def main():
    """Función principal"""
    discovery = QuotexSimpleDiscovery()
    discovery.run_simple_discovery()

if __name__ == "__main__":
    main()
