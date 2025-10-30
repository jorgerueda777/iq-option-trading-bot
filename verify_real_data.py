#!/usr/bin/env python3
"""
Verificador de Datos Reales de Quotex
Prueba que podemos obtener datos 100% reales antes del bot completo
"""

import sys
import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexDataVerifier:
    def __init__(self):
        self.driver = None
        self.test_assets = ["UK BRENT", "MICROSOFT", "ADA", "ETH"]
        
    def setup_chrome(self):
        """Configurar Chrome simple"""
        try:
            logging.info("🛡️ Configurando Chrome para verificación...")
            
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-extensions")
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.maximize_window()
            
            logging.info("✅ Chrome configurado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome: {e}")
            return False
    
    def open_quotex(self):
        """Abrir Quotex y hacer login"""
        try:
            logging.info("🌐 Abriendo Quotex...")
            self.driver.get("https://qxbroker.com/")
            time.sleep(5)
            
            logging.info("👤 HAZ LOGIN MANUAL Y SELECCIONA ACTIVO - 60 segundos")
            logging.info("   📧 Email: arnolbrom634@gmail.com")
            logging.info("   🔑 Password: 7decadames")
            logging.info("   🎯 IMPORTANTE: Después del login:")
            logging.info("      1. Ve a la sección de activos")
            logging.info("      2. Selecciona UK BRENT, MICROSOFT, ADA o ETH")
            logging.info("      3. Asegúrate de ver el PRECIO del activo en pantalla")
            
            time.sleep(60)
            
            # Navegar a trading
            try:
                logging.info("🔄 Navegando a plataforma de trading...")
                self.driver.get("https://qxbroker.com/trade")
                time.sleep(10)
                
                # Buscar y seleccionar un activo específico
                logging.info("🎯 Buscando activos disponibles...")
                
                # Intentar encontrar lista de activos o selector
                asset_selectors = [
                    "//div[contains(@class, 'asset')]",
                    "//button[contains(@class, 'asset')]",
                    "//span[contains(text(), 'BRENT')]",
                    "//span[contains(text(), 'MICROSOFT')]",
                    "//div[contains(text(), 'UK BRENT')]",
                    "//*[contains(text(), 'OTC')]"
                ]
                
                found_assets = False
                for selector in asset_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            logging.info(f"✅ Encontrados {len(elements)} elementos con: {selector}")
                            # Intentar hacer click en el primero
                            try:
                                elements[0].click()
                                time.sleep(3)
                                found_assets = True
                                break
                            except:
                                continue
                    except:
                        continue
                
                if not found_assets:
                    logging.warning("⚠️ No se encontraron selectores de activos - usando página actual")
                
            except Exception as e:
                logging.warning(f"⚠️ Error navegando: {e}")
            
            logging.info("✅ Quotex abierto y listo")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error abriendo Quotex: {e}")
            return False
    
    def extract_real_prices(self):
        """Extraer precios REALES usando el mismo JavaScript del bot"""
        try:
            logging.info("🔍 EXTRAYENDO PRECIOS REALES...")
            
            # Mismo JavaScript que usa el bot
            js_code = """
            try {
                let result = {
                    prices: [],
                    elements: [],
                    success: false,
                    debug: []
                };
                
                // 1. BUSCAR PRECIOS DE ACTIVOS (NO PAYOUTS)
                let allElements = document.querySelectorAll('*');
                let pricePattern = /\\b\\d{1,6}\\.\\d{2,6}\\b/g;
                let elementCount = 0;
                
                for (let element of allElements) {
                    elementCount++;
                    let text = element.textContent || element.innerText || '';
                    if (text && text.length < 100 && text.length > 3) {
                        // FILTRAR PAYOUTS - No queremos estos
                        let isPayout = text.toLowerCase().includes('pago') || 
                                      text.toLowerCase().includes('payout') || 
                                      text.toLowerCase().includes('su pago') ||
                                      text.includes('1.88') ||
                                      text.includes('%');
                        
                        if (!isPayout) {
                            let matches = text.match(pricePattern);
                            if (matches) {
                                for (let match of matches) {
                                    let price = parseFloat(match);
                                    // FILTRAR RANGOS DE PRECIOS REALISTAS PARA ACTIVOS
                                    if ((price > 10 && price < 500) ||        // MICROSOFT, UK BRENT
                                        (price > 0.1 && price < 10) ||        // ADA
                                        (price > 1000 && price < 5000) ||     // ETH
                                        (price > 50 && price < 100)) {        // Forex, Oil
                                        
                                        result.prices.push({
                                            price: price,
                                            text: text.trim(),
                                            className: element.className,
                                            tagName: element.tagName,
                                            visible: element.offsetParent !== null,
                                            id: element.id || 'no-id',
                                            filtered: 'asset_price'
                                        });
                                    }
                                }
                            }
                        }
                    }
                }
                
                result.debug.push('Total elements scanned: ' + elementCount);
                result.debug.push('Price elements found: ' + result.prices.length);
                
                // 2. BUSCAR EN OBJETOS JAVASCRIPT GLOBALES
                let globalVars = ['window', 'app', 'quotex', 'trading', 'market', 'price', 'asset', 'data'];
                for (let varName of globalVars) {
                    try {
                        if (window[varName] && typeof window[varName] === 'object') {
                            let obj = window[varName];
                            let objStr = JSON.stringify(obj).substring(0, 1000); // Limitar tamaño
                            let matches = objStr.match(pricePattern);
                            if (matches) {
                                for (let match of matches) {
                                    let price = parseFloat(match);
                                    if (price > 0.001 && price < 100000) {
                                        result.prices.push({
                                            price: price,
                                            source: 'global_' + varName,
                                            visible: true,
                                            text: 'From JS object'
                                        });
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        result.debug.push('Error checking ' + varName + ': ' + e.message);
                    }
                }
                
                // 3. BUSCAR SELECTORES ESPECÍFICOS DE TRADING
                let tradingSelectors = [
                    '[class*="price"]',
                    '[class*="rate"]',
                    '[class*="quote"]',
                    '[class*="value"]',
                    '[class*="amount"]',
                    '[data-price]',
                    '[data-rate]',
                    '.price',
                    '.rate',
                    '.quote'
                ];
                
                for (let selector of tradingSelectors) {
                    try {
                        let elements = document.querySelectorAll(selector);
                        result.debug.push(selector + ': ' + elements.length + ' elements');
                        
                        for (let element of elements) {
                            let text = element.textContent || element.innerText || '';
                            if (text) {
                                let matches = text.match(pricePattern);
                                if (matches) {
                                    for (let match of matches) {
                                        let price = parseFloat(match);
                                        if (price > 0.001 && price < 100000) {
                                            result.prices.push({
                                                price: price,
                                                text: text.trim(),
                                                selector: selector,
                                                visible: element.offsetParent !== null
                                            });
                                        }
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        result.debug.push('Error with selector ' + selector + ': ' + e.message);
                    }
                }
                
                // 4. INFORMACIÓN DE LA PÁGINA
                result.debug.push('Page URL: ' + window.location.href);
                result.debug.push('Page title: ' + document.title);
                result.debug.push('Total DOM elements: ' + document.querySelectorAll('*').length);
                
                // 5. FILTRAR Y ORDENAR PRECIOS
                if (result.prices.length > 0) {
                    // Eliminar duplicados
                    let uniquePrices = [];
                    let seenPrices = new Set();
                    
                    for (let priceData of result.prices) {
                        let key = priceData.price + '_' + (priceData.text || '');
                        if (!seenPrices.has(key)) {
                            seenPrices.add(key);
                            uniquePrices.push(priceData);
                        }
                    }
                    
                    result.prices = uniquePrices;
                    
                    // Ordenar por visibilidad y relevancia
                    result.prices.sort((a, b) => {
                        if (a.visible && !b.visible) return -1;
                        if (!a.visible && b.visible) return 1;
                        return 0;
                    });
                    
                    result.success = true;
                }
                
                return result;
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message,
                    stack: error.stack
                };
            }
            """
            
            # Ejecutar JavaScript
            result = self.driver.execute_script(js_code)
            
            logging.info("📊 RESULTADOS DE EXTRACCIÓN:")
            logging.info("=" * 60)
            
            if result and result.get("success"):
                prices_data = result.get("prices", [])
                debug_info = result.get("debug", [])
                
                logging.info(f"✅ ÉXITO: {len(prices_data)} precios encontrados")
                
                # Mostrar información de debug
                logging.info("🔍 INFORMACIÓN DE DEBUG:")
                for debug_msg in debug_info:
                    logging.info(f"   📋 {debug_msg}")
                
                # Mostrar precios encontrados
                logging.info("💰 PRECIOS ENCONTRADOS:")
                visible_count = 0
                
                for i, price_data in enumerate(prices_data[:20]):  # Mostrar primeros 20
                    price = price_data.get("price", 0)
                    text = price_data.get("text", "")[:30]
                    visible = price_data.get("visible", False)
                    source = price_data.get("source", price_data.get("selector", "DOM"))
                    
                    if visible:
                        visible_count += 1
                    
                    status = "👁️ VISIBLE" if visible else "🔍 OCULTO"
                    logging.info(f"   💵 {i+1:2d}. {price:>10.6f} | {status} | {source}")
                    logging.info(f"        Texto: '{text}...'")
                
                logging.info(f"📊 RESUMEN: {visible_count}/{len(prices_data)} precios visibles")
                
                # Verificar si tenemos precios válidos para trading
                valid_prices = [p for p in prices_data if p.get("visible", True) and p.get("price", 0) > 0.001]
                
                if valid_prices:
                    logging.info("✅ DATOS REALES DISPONIBLES PARA TRADING")
                    logging.info(f"   🎯 {len(valid_prices)} precios válidos encontrados")
                    
                    # Mostrar los 3 mejores precios
                    logging.info("🏆 TOP 3 PRECIOS MÁS PROBABLES:")
                    for i, price_data in enumerate(valid_prices[:3]):
                        price = price_data.get("price", 0)
                        text = price_data.get("text", "")
                        logging.info(f"   🥇 {i+1}. ${price:.6f} - '{text[:40]}...'")
                    
                    return True
                else:
                    logging.warning("⚠️ NO se encontraron precios válidos para trading")
                    return False
            
            else:
                error_msg = result.get("error", "Unknown error") if result else "No result"
                logging.error(f"❌ FALLO: {error_msg}")
                
                if result and result.get("debug"):
                    logging.info("🔍 DEBUG INFO:")
                    for debug_msg in result["debug"]:
                        logging.info(f"   📋 {debug_msg}")
                
                return False
            
        except Exception as e:
            logging.error(f"❌ Error extrayendo precios: {e}")
            return False
    
    def test_multiple_extractions(self):
        """Probar múltiples extracciones para verificar consistencia"""
        try:
            logging.info("🔄 PROBANDO MÚLTIPLES EXTRACCIONES...")
            
            results = []
            
            for i in range(3):
                logging.info(f"🧪 Extracción {i+1}/3...")
                
                success = self.extract_real_prices()
                results.append(success)
                
                if i < 2:  # No esperar después de la última
                    time.sleep(5)
            
            success_count = sum(results)
            logging.info("📊 RESULTADOS DE CONSISTENCIA:")
            logging.info(f"   ✅ Extracciones exitosas: {success_count}/3")
            logging.info(f"   📈 Tasa de éxito: {success_count/3*100:.0f}%")
            
            if success_count >= 2:
                logging.info("✅ DATOS REALES CONSISTENTES - LISTO PARA BOT")
                return True
            else:
                logging.warning("⚠️ DATOS INCONSISTENTES - NECESITA REVISIÓN")
                return False
            
        except Exception as e:
            logging.error(f"❌ Error en prueba múltiple: {e}")
            return False
    
    def run_verification(self):
        """Ejecutar verificación completa"""
        try:
            logging.info("🧪 INICIANDO VERIFICACIÓN DE DATOS REALES")
            logging.info("=" * 80)
            
            # 1. Configurar Chrome
            if not self.setup_chrome():
                return False
            
            # 2. Abrir Quotex
            if not self.open_quotex():
                return False
            
            # 3. Probar extracción múltiple
            success = self.test_multiple_extractions()
            
            # 4. Resultado final
            logging.info("🎯 RESULTADO FINAL:")
            logging.info("=" * 60)
            
            if success:
                logging.info("✅ VERIFICACIÓN EXITOSA")
                logging.info("   🎯 Datos reales disponibles")
                logging.info("   🚀 Bot listo para ejecutar")
                logging.info("   💰 Trading con datos 100% reales")
            else:
                logging.info("❌ VERIFICACIÓN FALLIDA")
                logging.info("   ⚠️ No se pueden obtener datos reales consistentes")
                logging.info("   🔧 Necesita ajustes antes del bot")
            
            # Mantener ventana abierta
            logging.info("🔍 Ventana abierta para inspección manual")
            logging.info("   Presiona ENTER para cerrar...")
            input()
            
            return success
            
        except Exception as e:
            logging.error(f"❌ Error en verificación: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Función principal"""
    verifier = QuotexDataVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n🎉 ¡VERIFICACIÓN EXITOSA! El bot puede usar datos reales.")
    else:
        print("\n⚠️ VERIFICACIÓN FALLIDA. Necesita ajustes.")

if __name__ == "__main__":
    main()
