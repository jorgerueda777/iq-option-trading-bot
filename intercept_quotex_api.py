#!/usr/bin/env python3
"""
Interceptor de API Real de Quotex
Captura las requests reales que hace la plataforma
"""

import time
import logging
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def intercept_quotex_requests():
    """Interceptar requests reales de Quotex"""
    try:
        logging.info("🕵️ INICIANDO INTERCEPTOR DE API QUOTEX")
        
        # Configurar Chrome ULTRA SIMPLE
        options = uc.ChromeOptions()
        options.add_argument("--no-first-run")
        
        driver = uc.Chrome(options=options, version_main=None)
        
        # Método simplificado - usar JavaScript para capturar requests
        captured_requests = []
        
        # Abrir Quotex
        logging.info("🌐 Abriendo Quotex...")
        driver.get("https://qxbroker.com/")
        time.sleep(5)
        
        logging.info("👤 HAZ LOGIN MANUAL - 60 segundos")
        logging.info("   📧 Email: arnolbrom634@gmail.com")
        logging.info("   🔑 Password: 7decadames")
        logging.info("   🎯 Después del login, navega por la plataforma")
        logging.info("   📊 Selecciona diferentes activos")
        logging.info("   ⏰ Deja que carguen los precios")
        
        # Inyectar JavaScript para interceptar requests
        js_interceptor = """
        window.capturedRequests = [];
        
        // Interceptar fetch
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            if (typeof url === 'string' && (url.includes('api') || url.includes('price') || url.includes('quote') || url.includes('asset'))) {
                console.log('FETCH INTERCEPTED:', url);
                window.capturedRequests.push({
                    url: url,
                    method: 'FETCH',
                    timestamp: Date.now()
                });
            }
            return originalFetch.apply(this, args);
        };
        
        // Interceptar XMLHttpRequest
        const originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXHR();
            const originalOpen = xhr.open;
            xhr.open = function(method, url) {
                if (typeof url === 'string' && (url.includes('api') || url.includes('price') || url.includes('quote') || url.includes('asset'))) {
                    console.log('XHR INTERCEPTED:', method, url);
                    window.capturedRequests.push({
                        url: url,
                        method: method,
                        timestamp: Date.now()
                    });
                }
                return originalOpen.apply(this, arguments);
            };
            return xhr;
        };
        
        console.log('REQUEST INTERCEPTOR INSTALLED');
        """
        
        driver.execute_script(js_interceptor)
        logging.info("🕵️ Interceptor JavaScript instalado")
        
        time.sleep(60)
        
        logging.info("🔍 CAPTURANDO REQUESTS POR 2 MINUTOS...")
        logging.info("   📈 Cambia entre activos para capturar más requests")
        
        # Capturar requests cada 10 segundos
        for i in range(12):  # 2 minutos = 12 x 10 segundos
            time.sleep(10)
            
            # Obtener requests capturadas
            try:
                new_requests = driver.execute_script("return window.capturedRequests || [];")
                
                for req in new_requests:
                    if req not in captured_requests:
                        captured_requests.append(req)
                        logging.info(f"📡 API REQUEST: {req['url']}")
                
                # Limpiar array para evitar duplicados
                driver.execute_script("window.capturedRequests = [];")
                
            except Exception as e:
                logging.warning(f"⚠️ Error capturando: {e}")
                
            logging.info(f"🔄 Capturando... {i+1}/12 ({len(captured_requests)} requests)")
        
        # Captura final
        try:
            final_requests = driver.execute_script("return window.capturedRequests || [];")
            captured_requests.extend(final_requests)
        except:
            pass
        
        # Mostrar requests capturadas
        logging.info("📊 REQUESTS CAPTURADAS:")
        logging.info("=" * 80)
        
        unique_requests = {}
        for req in captured_requests:
            url_base = req['url'].split('?')[0]  # Quitar parámetros
            if url_base not in unique_requests:
                unique_requests[url_base] = req
        
        for i, (url, req) in enumerate(unique_requests.items(), 1):
            logging.info(f"🔗 {i:2d}. {req['method']} {url}")
            logging.info(f"      Status: {req['status']}")
        
        # Guardar en archivo
        output_file = "D:/iq_quot/captured_quotex_requests.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(list(unique_requests.values()), f, indent=2, ensure_ascii=False)
        
        logging.info(f"💾 Requests guardadas en: {output_file}")
        logging.info(f"📊 Total requests únicas: {len(unique_requests)}")
        
        # Mantener navegador abierto para inspección
        logging.info("🔍 Navegador abierto para inspección manual")
        logging.info("   Presiona ENTER para cerrar...")
        input()
        
        driver.quit()
        
        return list(unique_requests.values())
        
    except Exception as e:
        logging.error(f"❌ Error interceptando: {e}")
        return []

def analyze_captured_requests():
    """Analizar requests capturadas"""
    try:
        with open("D:/iq_quot/captured_quotex_requests.json", 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        logging.info("🔍 ANÁLISIS DE REQUESTS CAPTURADAS:")
        logging.info("=" * 60)
        
        # Categorizar requests
        categories = {
            'price_endpoints': [],
            'asset_endpoints': [],
            'auth_endpoints': [],
            'trade_endpoints': [],
            'other_endpoints': []
        }
        
        for req in requests:
            url = req['url'].lower()
            
            if any(keyword in url for keyword in ['price', 'quote', 'rate']):
                categories['price_endpoints'].append(req)
            elif any(keyword in url for keyword in ['asset', 'instrument', 'symbol']):
                categories['asset_endpoints'].append(req)
            elif any(keyword in url for keyword in ['auth', 'login', 'token']):
                categories['auth_endpoints'].append(req)
            elif any(keyword in url for keyword in ['trade', 'order', 'buy', 'sell']):
                categories['trade_endpoints'].append(req)
            else:
                categories['other_endpoints'].append(req)
        
        for category, reqs in categories.items():
            if reqs:
                logging.info(f"📂 {category.upper()}: {len(reqs)} requests")
                for req in reqs[:3]:  # Mostrar primeros 3
                    logging.info(f"   🔗 {req['url']}")
        
        return categories
        
    except Exception as e:
        logging.error(f"❌ Error analizando: {e}")
        return {}

def main():
    """Función principal"""
    logging.info("🚀 INTERCEPTOR DE API QUOTEX")
    logging.info("=" * 80)
    
    # Interceptar requests
    requests = intercept_quotex_requests()
    
    if requests:
        # Analizar requests
        categories = analyze_captured_requests()
        
        logging.info("✅ INTERCEPTACIÓN COMPLETADA")
        logging.info("   Ahora podemos usar estos endpoints reales")
    else:
        logging.warning("⚠️ No se capturaron requests")

if __name__ == "__main__":
    main()
