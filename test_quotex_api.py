#!/usr/bin/env python3
"""
Script de prueba para verificar la API de Quotex
Verifica que podemos obtener datos reales de precios OTC
"""

import sys
import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexAPITester:
    def __init__(self):
        self.driver = None
        self.test_pairs = ["UK BRENT", "MICROSOFT", "ADA", "ETH"]
    
    def setup_chrome(self):
        """Configurar Chrome para pruebas"""
        try:
            logging.info("🛡️ Configurando Chrome para pruebas...")
            
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-extensions")
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.maximize_window()
            
            logging.info("✅ Chrome configurado para pruebas")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome: {e}")
            return False
    
    def open_quotex(self):
        """Abrir Quotex"""
        try:
            logging.info("🌐 Abriendo Quotex...")
            self.driver.get("https://qxbroker.com/")
            time.sleep(5)
            
            logging.info("👤 HAZ LOGIN MANUAL - 60 segundos")
            logging.info("   📧 Email: arnolbrom634@gmail.com")
            logging.info("   🔑 Password: 7decadames")
            
            time.sleep(60)
            
            # Navegar a trading
            try:
                logging.info("🔄 Navegando a plataforma de trading...")
                self.driver.get("https://qxbroker.com/trade")
                time.sleep(5)
            except:
                pass
            
            logging.info("✅ Quotex abierto y listo para pruebas")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error abriendo Quotex: {e}")
            return False
    
    def test_javascript_data_extraction(self):
        """Probar extracción de datos con JavaScript"""
        try:
            logging.info("🧪 PROBANDO EXTRACCIÓN DE DATOS CON JAVASCRIPT...")
            
            # JavaScript mejorado para extraer datos
            js_code = """
            try {
                console.log('=== QUOTEX API TEST ===');
                
                let results = {
                    prices: [],
                    elements: [],
                    objects: [],
                    websockets: [],
                    errors: []
                };
                
                // 1. Buscar elementos de precio en el DOM
                console.log('1. Buscando elementos de precio...');
                let priceSelectors = [
                    '[class*="price"]',
                    '[class*="rate"]', 
                    '[class*="quote"]',
                    '[class*="asset"]',
                    '[class*="value"]',
                    '[class*="amount"]',
                    '[class*="number"]',
                    '[class*="digit"]',
                    '[class*="currency"]',
                    '[class*="money"]',
                    '[data-price]',
                    '[data-rate]',
                    '[data-value]',
                    'span:contains(".")',
                    'div:contains(".")',
                    '[class*="trading"]',
                    '[class*="chart"]',
                    '[class*="market"]'
                ];
                
                for (let selector of priceSelectors) {
                    let elements = document.querySelectorAll(selector);
                    for (let element of elements) {
                        let text = element.textContent || element.innerText || '';
                        let classes = element.className || '';
                        
                        if (text && /\\d+\\.\\d+/.test(text)) {
                            let matches = text.match(/\\d+\\.\\d+/g);
                            if (matches) {
                                results.elements.push({
                                    selector: selector,
                                    text: text.trim(),
                                    classes: classes,
                                    prices: matches.map(p => parseFloat(p))
                                });
                                
                                matches.forEach(price => {
                                    results.prices.push(parseFloat(price));
                                });
                            }
                        }
                    }
                }
                
                // 2. Buscar objetos JavaScript globales
                console.log('2. Buscando objetos JavaScript...');
                let globalObjects = [
                    'quotexData', 'marketData', 'priceData', 'assetData',
                    'tradingData', 'socketData', 'apiData', 'chartData'
                ];
                
                for (let objName of globalObjects) {
                    if (window[objName]) {
                        results.objects.push({
                            name: objName,
                            type: typeof window[objName],
                            data: JSON.stringify(window[objName]).substring(0, 200)
                        });
                    }
                }
                
                // 3. Verificar WebSockets activos
                console.log('3. Verificando WebSockets...');
                if (window.WebSocket && window.WebSocket.prototype) {
                    results.websockets.push({
                        available: true,
                        prototype: Object.getOwnPropertyNames(window.WebSocket.prototype)
                    });
                }
                
                // 4. Buscar en localStorage y sessionStorage
                console.log('4. Verificando storage...');
                try {
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        if (key && (key.includes('price') || key.includes('asset') || key.includes('quotex'))) {
                            results.objects.push({
                                name: 'localStorage.' + key,
                                data: localStorage.getItem(key).substring(0, 100)
                            });
                        }
                    }
                } catch (e) {
                    results.errors.push('localStorage: ' + e.message);
                }
                
                // 5. Buscar eventos de red
                console.log('5. Verificando eventos...');
                if (window.performance && window.performance.getEntriesByType) {
                    let networkEntries = window.performance.getEntriesByType('resource');
                    let apiCalls = networkEntries.filter(entry => 
                        entry.name.includes('api') || 
                        entry.name.includes('socket') || 
                        entry.name.includes('price')
                    );
                    
                    results.objects.push({
                        name: 'networkCalls',
                        count: apiCalls.length,
                        urls: apiCalls.slice(0, 5).map(entry => entry.name)
                    });
                }
                
                // 6. ANÁLISIS EXHAUSTIVO - Buscar TODOS los elementos con números
                console.log('6. Análisis exhaustivo de elementos...');
                let allElements = document.querySelectorAll('*');
                let elementsWithNumbers = [];
                
                for (let element of allElements) {
                    let text = element.textContent || element.innerText || '';
                    if (text && /\\d+\\.\\d{2,}/.test(text) && text.length < 50) {
                        let matches = text.match(/\\d+\\.\\d{2,}/g);
                        if (matches) {
                            elementsWithNumbers.push({
                                tagName: element.tagName,
                                className: element.className,
                                id: element.id,
                                text: text.trim(),
                                matches: matches,
                                parent: element.parentElement ? element.parentElement.className : ''
                            });
                        }
                    }
                }
                
                results.allNumberElements = elementsWithNumbers.slice(0, 20); // Top 20
                
                console.log('=== RESULTS ===', results);
                return results;
                
            } catch (error) {
                console.error('JavaScript error:', error);
                return {
                    success: false,
                    error: error.message,
                    stack: error.stack
                };
            }
            """
            
            # Ejecutar JavaScript
            result = self.driver.execute_script(js_code)
            
            logging.info("📊 RESULTADOS DE LA PRUEBA:")
            logging.info("=" * 60)
            
            if result:
                # Mostrar precios encontrados
                if result.get("prices"):
                    prices = result["prices"]
                    logging.info(f"💰 PRECIOS ENCONTRADOS: {len(prices)}")
                    for i, price in enumerate(prices[:10]):  # Mostrar primeros 10
                        logging.info(f"   💵 Precio {i+1}: {price}")
                
                # Mostrar elementos encontrados
                if result.get("elements"):
                    elements = result["elements"]
                    logging.info(f"🔍 ELEMENTOS ENCONTRADOS: {len(elements)}")
                    for i, elem in enumerate(elements[:5]):  # Mostrar primeros 5
                        logging.info(f"   📋 Elemento {i+1}:")
                        logging.info(f"      Selector: {elem.get('selector', 'N/A')}")
                        logging.info(f"      Texto: {elem.get('text', 'N/A')[:50]}...")
                        logging.info(f"      Precios: {elem.get('prices', [])}")
                
                # Mostrar objetos JavaScript
                if result.get("objects"):
                    objects = result["objects"]
                    logging.info(f"🧠 OBJETOS JAVASCRIPT: {len(objects)}")
                    for obj in objects:
                        logging.info(f"   🔧 {obj.get('name', 'N/A')}: {obj.get('type', 'N/A')}")
                        if obj.get('data'):
                            logging.info(f"      Data: {obj['data'][:100]}...")
                
                # Mostrar WebSockets
                if result.get("websockets"):
                    logging.info("🌐 WEBSOCKETS DISPONIBLES: ✅")
                
                # Mostrar errores
                if result.get("errors"):
                    logging.info(f"⚠️ ERRORES: {len(result['errors'])}")
                    for error in result["errors"]:
                        logging.info(f"   ❌ {error}")
                
                # Mostrar análisis exhaustivo
                if result.get("allNumberElements"):
                    elements = result["allNumberElements"]
                    logging.info(f"🔢 ELEMENTOS CON NÚMEROS: {len(elements)}")
                    for i, elem in enumerate(elements[:10]):  # Mostrar primeros 10
                        logging.info(f"   📋 Elemento {i+1}:")
                        logging.info(f"      Tag: {elem.get('tagName', 'N/A')}")
                        logging.info(f"      Clase: {elem.get('className', 'N/A')[:50]}...")
                        logging.info(f"      ID: {elem.get('id', 'N/A')}")
                        logging.info(f"      Texto: {elem.get('text', 'N/A')}")
                        logging.info(f"      Números: {elem.get('matches', [])}")
                        logging.info(f"      Padre: {elem.get('parent', 'N/A')[:30]}...")
            
            logging.info("=" * 60)
            return result
            
        except Exception as e:
            logging.error(f"❌ Error en prueba JavaScript: {e}")
            return None
    
    def test_dom_price_extraction(self):
        """Probar extracción directa del DOM"""
        try:
            logging.info("🧪 PROBANDO EXTRACCIÓN DIRECTA DEL DOM...")
            
            # Selectores específicos para Quotex
            price_selectors = [
                "//div[contains(@class, 'asset-price')]",
                "//span[contains(@class, 'current-price')]",
                "//div[contains(@class, 'quote-value')]",
                "//*[contains(@class, 'price-display')]",
                "//*[contains(@class, 'rate-value')]",
                "//*[contains(@class, 'price')]",
                "//*[contains(@class, 'rate')]",
                "//*[contains(@class, 'quote')]",
                "//*[contains(text(), '$')]",
                "//*[contains(text(), '€')]",
                "//*[contains(text(), '.')]"
            ]
            
            found_prices = []
            
            for selector in price_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    logging.info(f"🔍 Selector '{selector}': {len(elements)} elementos")
                    
                    for i, element in enumerate(elements[:3]):  # Solo primeros 3
                        try:
                            text = element.text.strip()
                            if text and any(char.isdigit() for char in text):
                                import re
                                numbers = re.findall(r'\d+\.?\d+', text)
                                if numbers:
                                    for num in numbers:
                                        price = float(num)
                                        if price > 0.01:  # Filtrar precios válidos
                                            found_prices.append({
                                                "selector": selector,
                                                "element_index": i,
                                                "text": text[:50],
                                                "price": price
                                            })
                                            logging.info(f"   💰 Precio: {price} | Texto: '{text[:30]}...'")
                        except:
                            continue
                except:
                    continue
            
            logging.info(f"📊 TOTAL PRECIOS ENCONTRADOS: {len(found_prices)}")
            return found_prices
            
        except Exception as e:
            logging.error(f"❌ Error en extracción DOM: {e}")
            return []
    
    def run_full_test(self):
        """Ejecutar prueba completa"""
        try:
            logging.info("🚀 INICIANDO PRUEBA COMPLETA DE API QUOTEX")
            logging.info("=" * 60)
            
            # 1. Configurar Chrome
            if not self.setup_chrome():
                return False
            
            # 2. Abrir Quotex
            if not self.open_quotex():
                return False
            
            # 3. Probar JavaScript
            js_result = self.test_javascript_data_extraction()
            
            # 4. Probar DOM
            dom_result = self.test_dom_price_extraction()
            
            # 5. Resumen final
            logging.info("🎯 RESUMEN FINAL:")
            logging.info("=" * 60)
            
            if js_result and js_result.get("prices"):
                logging.info(f"✅ JavaScript: {len(js_result['prices'])} precios encontrados")
            else:
                logging.info("❌ JavaScript: No se encontraron precios")
            
            if dom_result:
                logging.info(f"✅ DOM: {len(dom_result)} precios encontrados")
            else:
                logging.info("❌ DOM: No se encontraron precios")
            
            # Mantener ventana abierta para inspección manual
            logging.info("🔍 VENTANA ABIERTA PARA INSPECCIÓN MANUAL")
            logging.info("   Presiona ENTER para cerrar...")
            input()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error en prueba completa: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Función principal"""
    tester = QuotexAPITester()
    tester.run_full_test()

if __name__ == "__main__":
    main()
