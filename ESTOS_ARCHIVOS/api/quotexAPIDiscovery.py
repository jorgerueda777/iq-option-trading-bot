#!/usr/bin/env python3
"""
Quotex API Discovery
Intercepta y descubre los endpoints reales de la API de Quotex
"""

import sys
import time
import logging
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexAPIDiscovery:
    def __init__(self):
        self.driver = None
        self.network_logs = []
        self.api_endpoints = []
        
    def setup_chrome_with_logging(self):
        """Configurar Chrome con logging de red habilitado"""
        try:
            logging.info("🛡️ Configurando Chrome con interceptación de red...")
            
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-extensions")
            
            # HABILITAR LOGGING DE RED
            options.add_argument("--enable-logging")
            options.add_argument("--log-level=0")
            options.add_argument("--v=1")
            
            # Habilitar DevTools
            options.add_experimental_option("useAutomationExtension", False)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Habilitar logging de red en DevTools
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Runtime.enable', {})
            
            logging.info("✅ Chrome configurado con interceptación de red")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome: {e}")
            return False
    
    def open_quotex_and_login(self):
        """Abrir Quotex y hacer login"""
        try:
            logging.info("🌐 Abriendo Quotex...")
            self.driver.get("https://qxbroker.com/")
            time.sleep(5)
            
            logging.info("👤 HAZ LOGIN MANUAL - 45 segundos")
            logging.info("   📧 Email: arnolbrom634@gmail.com")
            logging.info("   🔑 Password: 7decadames")
            logging.info("   ⚠️ ¡IMPORTANTE! Mientras haces login, interceptaré todas las requests")
            
            # Interceptar requests durante login
            start_time = time.time()
            while time.time() - start_time < 45:  # 45 segundos
                try:
                    # Obtener logs de performance
                    logs = self.driver.get_log('performance')
                    for log in logs:
                        message = json.loads(log['message'])
                        if message['message']['method'] == 'Network.responseReceived':
                            url = message['message']['params']['response']['url']
                            status = message['message']['params']['response']['status']
                            
                            # Filtrar URLs de API
                            if any(keyword in url.lower() for keyword in ['api', 'auth', 'login', 'user', 'trade', 'price', 'asset']):
                                self.api_endpoints.append({
                                    'url': url,
                                    'status': status,
                                    'method': message['message']['params']['response'].get('method', 'GET'),
                                    'timestamp': time.time()
                                })
                                logging.info(f"🔍 API Call: {status} {url}")
                
                except Exception as e:
                    pass
                
                time.sleep(1)
            
            # Navegar a trading
            try:
                logging.info("🔄 Navegando a plataforma de trading...")
                self.driver.get("https://qxbroker.com/trade")
                time.sleep(5)
                
                # Interceptar más requests
                for i in range(10):
                    try:
                        logs = self.driver.get_log('performance')
                        for log in logs:
                            message = json.loads(log['message'])
                            if message['message']['method'] == 'Network.responseReceived':
                                url = message['message']['params']['response']['url']
                                status = message['message']['params']['response']['status']
                                
                                if any(keyword in url.lower() for keyword in ['api', 'price', 'asset', 'market', 'quote']):
                                    self.api_endpoints.append({
                                        'url': url,
                                        'status': status,
                                        'method': message['message']['params']['response'].get('method', 'GET'),
                                        'timestamp': time.time()
                                    })
                                    logging.info(f"🔍 Trading API: {status} {url}")
                    except:
                        pass
                    
                    time.sleep(2)
                    
            except Exception as e:
                logging.error(f"❌ Error navegando a trading: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error abriendo Quotex: {e}")
            return False
    
    def analyze_network_traffic(self):
        """Analizar tráfico de red interceptado"""
        try:
            logging.info("📊 ANALIZANDO TRÁFICO DE RED INTERCEPTADO...")
            logging.info("=" * 80)
            
            if not self.api_endpoints:
                logging.warning("⚠️ No se interceptaron llamadas de API")
                return
            
            # Agrupar por dominio
            domains = {}
            for endpoint in self.api_endpoints:
                url = endpoint['url']
                domain = url.split('/')[2] if '://' in url else 'unknown'
                
                if domain not in domains:
                    domains[domain] = []
                domains[domain].append(endpoint)
            
            # Mostrar resultados
            for domain, endpoints in domains.items():
                logging.info(f"🌐 DOMINIO: {domain}")
                logging.info(f"   📊 Total requests: {len(endpoints)}")
                
                # Agrupar por path
                paths = {}
                for endpoint in endpoints:
                    url = endpoint['url']
                    path = '/'.join(url.split('/')[3:]) if '://' in url else url
                    
                    if path not in paths:
                        paths[path] = []
                    paths[path].append(endpoint)
                
                # Mostrar paths más comunes
                sorted_paths = sorted(paths.items(), key=lambda x: len(x[1]), reverse=True)
                
                for path, path_endpoints in sorted_paths[:10]:  # Top 10
                    status_codes = [ep['status'] for ep in path_endpoints]
                    unique_statuses = list(set(status_codes))
                    
                    logging.info(f"   📋 /{path}")
                    logging.info(f"      Calls: {len(path_endpoints)} | Status: {unique_statuses}")
                    
                    # Mostrar URL completa del primer endpoint
                    if path_endpoints:
                        full_url = path_endpoints[0]['url']
                        logging.info(f"      URL: {full_url}")
                
                logging.info("-" * 60)
            
            # Buscar endpoints específicos de interés
            logging.info("🎯 ENDPOINTS DE INTERÉS:")
            
            interest_keywords = ['auth', 'login', 'price', 'asset', 'trade', 'market', 'quote', 'websocket', 'ws']
            
            for keyword in interest_keywords:
                matching_endpoints = [ep for ep in self.api_endpoints if keyword in ep['url'].lower()]
                
                if matching_endpoints:
                    logging.info(f"🔍 {keyword.upper()}:")
                    for ep in matching_endpoints[:5]:  # Primeros 5
                        logging.info(f"   {ep['status']} {ep['url']}")
            
            # Guardar resultados
            self.save_discovered_endpoints()
            
        except Exception as e:
            logging.error(f"❌ Error analizando tráfico: {e}")
    
    def save_discovered_endpoints(self):
        """Guardar endpoints descubiertos"""
        try:
            output_file = "D:/iq_quot/discovered_quotex_endpoints.json"
            
            # Preparar datos para guardar
            unique_endpoints = []
            seen_urls = set()
            
            for endpoint in self.api_endpoints:
                url = endpoint['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_endpoints.append(endpoint)
            
            data = {
                "discovery_timestamp": time.time(),
                "total_endpoints": len(unique_endpoints),
                "endpoints": unique_endpoints
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"💾 Endpoints guardados en: {output_file}")
            logging.info(f"📊 Total endpoints únicos: {len(unique_endpoints)}")
            
        except Exception as e:
            logging.error(f"❌ Error guardando endpoints: {e}")
    
    def extract_websocket_info(self):
        """Extraer información de WebSockets"""
        try:
            logging.info("🌐 EXTRAYENDO INFORMACIÓN DE WEBSOCKETS...")
            
            # JavaScript para obtener info de WebSockets
            js_code = """
            try {
                let wsInfo = {
                    websockets: [],
                    eventSources: [],
                    networkConnections: []
                };
                
                // Interceptar WebSocket
                if (window.WebSocket) {
                    let originalWS = window.WebSocket;
                    window.WebSocket = function(url, protocols) {
                        console.log('WebSocket created:', url);
                        wsInfo.websockets.push({
                            url: url,
                            protocols: protocols,
                            timestamp: Date.now()
                        });
                        return new originalWS(url, protocols);
                    };
                }
                
                // Buscar conexiones existentes
                if (window.performance && window.performance.getEntriesByType) {
                    let resources = window.performance.getEntriesByType('resource');
                    for (let resource of resources) {
                        if (resource.name.includes('ws://') || resource.name.includes('wss://')) {
                            wsInfo.networkConnections.push({
                                url: resource.name,
                                type: resource.initiatorType,
                                duration: resource.duration
                            });
                        }
                    }
                }
                
                return wsInfo;
                
            } catch (error) {
                return { error: error.message };
            }
            """
            
            result = self.driver.execute_script(js_code)
            
            if result and not result.get('error'):
                logging.info("✅ Información de WebSockets extraída:")
                
                if result.get('websockets'):
                    logging.info(f"🔌 WebSockets creados: {len(result['websockets'])}")
                    for ws in result['websockets']:
                        logging.info(f"   🌐 {ws['url']}")
                
                if result.get('networkConnections'):
                    logging.info(f"🌐 Conexiones WS en red: {len(result['networkConnections'])}")
                    for conn in result['networkConnections']:
                        logging.info(f"   🔗 {conn['url']}")
            
            return result
            
        except Exception as e:
            logging.error(f"❌ Error extrayendo WebSockets: {e}")
            return None
    
    def run_discovery(self):
        """Ejecutar descubrimiento completo"""
        try:
            logging.info("🕵️ INICIANDO DESCUBRIMIENTO DE API DE QUOTEX")
            logging.info("=" * 80)
            
            # 1. Configurar Chrome
            if not self.setup_chrome_with_logging():
                return False
            
            # 2. Abrir Quotex e interceptar
            if not self.open_quotex_and_login():
                return False
            
            # 3. Extraer WebSockets
            self.extract_websocket_info()
            
            # 4. Analizar tráfico
            self.analyze_network_traffic()
            
            # 5. Mantener abierto para inspección
            logging.info("🔍 VENTANA ABIERTA PARA INSPECCIÓN ADICIONAL")
            logging.info("   Presiona ENTER para finalizar...")
            input()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error en descubrimiento: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Función principal"""
    discovery = QuotexAPIDiscovery()
    discovery.run_discovery()

if __name__ == "__main__":
    main()
