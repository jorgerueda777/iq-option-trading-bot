#!/usr/bin/env python3
"""
Quotex Bot - Estilo Main de IQ Option
Replica exactamente el método de login y extracción de precios de IQ Option pero para Quotex
"""

import sys
import json
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        self.logged_in = False
        self.session = requests.Session()
        self.base_url = "https://qxbroker.com"
        
    def setup_driver_existing(self):
        """Conectar a una instancia existente de Chrome con debug habilitado"""
        try:
            logging.info("🔧 Intentando conectar a Chrome existente...")
            
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Usar webdriver-manager para descargar ChromeDriver automáticamente
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ Conectado a Chrome existente")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error conectando a Chrome existente: {e}")
            return self.setup_driver_new()
    
    def setup_driver_new(self):
        """Crear nueva instancia de Chrome si no hay una existente"""
        try:
            logging.info("🔧 Creando nueva instancia de Chrome...")
            
            chrome_options = Options()
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # User agent realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.125 Safari/537.36")
            
            # Usar webdriver-manager para descargar ChromeDriver automáticamente
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ Nueva instancia de Chrome creada")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error creando nueva instancia: {e}")
            return False
    
    def open_quotex(self):
        """Abrir Quotex y hacer login automático"""
        try:
            logging.info("🌐 Abriendo Quotex...")
            self.driver.get(f"{self.base_url}/")
            time.sleep(3)
            
            # Intentar login automático
            if self.auto_login():
                return True
            
            # Si falla, login manual
            logging.info("👤 POR FAVOR, HAZ LOGIN MANUALMENTE EN EL NAVEGADOR")
            logging.info("⏳ Esperando que hagas login... (tienes 2 minutos)")
            
            # Esperar hasta 2 minutos para que el usuario haga login manualmente
            try:
                # Esperar a que aparezca algún elemento que indique que está logueado
                WebDriverWait(self.driver, 120).until(
                    lambda driver: "qxbroker.com/trade" in driver.current_url or 
                                  "dashboard" in driver.current_url.lower() or
                                  len(driver.find_elements(By.XPATH, "//div[contains(@class, 'trading') or contains(@class, 'platform')]")) > 0
                )
                logging.info("✅ Login detectado exitosamente")
                self.logged_in = True
                return True
                
            except TimeoutException:
                logging.error("⏰ Timeout: No se detectó login en 2 minutos")
                return False
            
        except Exception as e:
            logging.error(f"❌ Error abriendo Quotex: {e}")
            return False
    
    def auto_login(self):
        """Intentar login automático como en IQ Option"""
        try:
            logging.info("🔐 Intentando login automático...")
            
            # Buscar formulario de login
            login_selectors = [
                "input[type='email'], input[name='email'], input[name='username']",
                "input[type='password'], input[name='password']",
                "button[type='submit'], button:contains('Login'), button:contains('Sign in')"
            ]
            
            # Buscar campo de email
            email_field = None
            for selector in ["input[type='email']", "input[name='email']", "input[name='username']"]:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not email_field:
                logging.info("❌ No se encontró campo de email")
                return False
            
            # Buscar campo de password
            password_field = None
            for selector in ["input[type='password']", "input[name='password']"]:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not password_field:
                logging.info("❌ No se encontró campo de password")
                return False
            
            # Llenar formulario
            logging.info("📝 Llenando formulario de login...")
            email_field.clear()
            email_field.send_keys(self.email)
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)
            
            # Buscar y hacer clic en botón de login
            login_button = None
            for selector in ["button[type='submit']", "input[type='submit']", "button"]:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if any(text in btn.text.lower() for text in ['login', 'sign in', 'entrar', 'iniciar']):
                            login_button = btn
                            break
                    if login_button:
                        break
                except:
                    continue
            
            if login_button:
                login_button.click()
                logging.info("🔘 Botón de login clickeado")
            else:
                password_field.send_keys("\n")
                logging.info("⌨️ Enter presionado")
            
            # Esperar respuesta
            time.sleep(5)
            
            # Verificar si el login fue exitoso
            current_url = self.driver.current_url
            if "trade" in current_url or "dashboard" in current_url:
                logging.info("✅ Login automático exitoso")
                self.logged_in = True
                return True
            else:
                logging.info("❌ Login automático falló")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error en login automático: {e}")
            return False
    
    def get_real_prices(self):
        """Extraer precios reales como en IQ Option"""
        try:
            logging.info("💰 Extrayendo precios reales...")
            
            # Método 1: JavaScript injection (como IQ Option)
            prices_script = """
            try {
                let prices = {};
                
                // Buscar precios en variables globales
                if (window.quotexData && window.quotexData.prices) {
                    prices.quotex_global = window.quotexData.prices;
                }
                
                // Buscar precios en WebSocket data
                if (window.wsData && window.wsData.quotes) {
                    prices.websocket = window.wsData.quotes;
                }
                
                // Buscar precios en DOM
                let priceElements = document.querySelectorAll('[class*="price"], [class*="rate"], [class*="quote"]');
                let domPrices = [];
                
                for (let el of priceElements) {
                    let text = el.textContent || el.innerText;
                    if (text && /\\d+\\.\\d+/.test(text)) {
                        let matches = text.match(/\\d+\\.\\d+/g);
                        if (matches) {
                            for (let match of matches) {
                                let price = parseFloat(match);
                                if (price > 0.01 && price < 100000) {
                                    domPrices.push({
                                        price: price,
                                        element: el.className,
                                        text: text.substring(0, 50)
                                    });
                                }
                            }
                        }
                    }
                }
                
                prices.dom_prices = domPrices;
                prices.timestamp = Date.now();
                
                return prices;
                
            } catch (error) {
                return {error: error.message};
            }
            """
            
            result = self.driver.execute_script(prices_script)
            
            if result and not result.get('error'):
                logging.info("✅ Precios extraídos exitosamente")
                
                # Mostrar precios encontrados
                if result.get('dom_prices'):
                    logging.info(f"📊 Precios DOM encontrados: {len(result['dom_prices'])}")
                    for i, price_data in enumerate(result['dom_prices'][:5]):
                        logging.info(f"   💰 Precio {i+1}: {price_data['price']} ({price_data['text']})")
                
                if result.get('websocket'):
                    logging.info("🌐 Datos WebSocket encontrados")
                
                if result.get('quotex_global'):
                    logging.info("🌍 Datos globales encontrados")
                
                return result
            else:
                logging.error(f"❌ Error extrayendo precios: {result.get('error', 'Unknown')}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error extrayendo precios: {e}")
            return None
    
    def detect_trading_interface(self):
        """Detectar si ya estamos en la interfaz de trading"""
        try:
            logging.info("🔍 Detectando interfaz de trading...")
            
            # Obtener información de la página actual
            current_url = self.driver.current_url
            page_title = self.driver.title
            logging.info(f"📄 URL actual: {current_url}")
            logging.info(f"📄 Título: {page_title}")
            
            # Buscar múltiples indicadores de trading
            trading_indicators = [
                "//button[contains(text(), 'UP')]",
                "//button[contains(text(), 'DOWN')]", 
                "//button[contains(text(), 'CALL')]",
                "//button[contains(text(), 'PUT')]",
                "//div[contains(text(), 'Trading')]",
                "//span[contains(text(), 'Trading')]",
                "//*[contains(@class, 'trading')]",
                "//button[contains(@class, 'call')]",
                "//button[contains(@class, 'put')]",
                "//div[contains(text(), 'Profit')]",
                "//div[contains(text(), 'Payout')]",
                "//*[contains(@class, 'asset')]",
                "//*[contains(@class, 'chart')]"
            ]
            
            found_elements = []
            for indicator in trading_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if elements:
                    found_elements.append(f"{indicator}: {len(elements)} elementos")
            
            if found_elements:
                logging.info("✅ INTERFAZ DE TRADING DETECTADA! Elementos encontrados:")
                for element in found_elements:
                    logging.info(f"   - {element}")
                return True
            else:
                logging.info("❌ No se detectó interfaz de trading. Elementos de la página:")
                # Mostrar algunos elementos para debug
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for i, btn in enumerate(buttons[:5]):
                    if btn.text.strip():
                        logging.info(f"   - Botón {i+1}: '{btn.text.strip()}'")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error detectando interfaz: {e}")
            return False
    
    def execute_trade(self, asset, amount, direction, duration=60):
        """Ejecutar operación como en IQ Option"""
        try:
            logging.info(f"🎯 Ejecutando operación: {asset} {direction} ${amount} por {duration}s")
            
            # Buscar botones de dirección
            if direction.upper() in ["CALL", "UP"]:
                button_selectors = [
                    "//button[contains(text(), 'UP')]",
                    "//button[contains(text(), 'CALL')]",
                    "//button[contains(@class, 'call')]",
                    "//button[contains(@class, 'up')]"
                ]
            else:
                button_selectors = [
                    "//button[contains(text(), 'DOWN')]",
                    "//button[contains(text(), 'PUT')]",
                    "//button[contains(@class, 'put')]",
                    "//button[contains(@class, 'down')]"
                ]
            
            # Buscar y hacer clic en botón
            trade_button = None
            for selector in button_selectors:
                try:
                    trade_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except:
                    continue
            
            if trade_button:
                trade_button.click()
                logging.info(f"✅ Operación {direction} ejecutada")
                return {"success": True, "message": f"Operación {direction} ejecutada exitosamente"}
            else:
                logging.error(f"❌ No se encontró botón {direction}")
                return {"success": False, "message": f"No se encontró botón {direction}"}
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando operación: {e}")
            return {"success": False, "message": str(e)}
    
    def close(self):
        """Cerrar el navegador"""
        if self.driver:
            self.driver.quit()

def main():
    """Función principal para comunicación con Node.js (como IQ Option)"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Comando requerido"}))
        return
    
    command = sys.argv[1]
    
    # Credenciales (como en IQ Option)
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    quotex = QuotexAPI(email, password)
    
    try:
        if command == "connect":
            if not quotex.setup_driver_existing():
                print(json.dumps({"success": False, "message": "Error configurando ChromeDriver"}))
                return
            
            if not quotex.open_quotex():
                print(json.dumps({"success": False, "message": "Error abriendo Quotex"}))
                return
                
            # Detectar si ya estamos en trading
            success = quotex.detect_trading_interface()
            
            result = {"success": success, "message": "Conectado a Quotex" if success else "No se detectó interfaz de trading"}
            print(json.dumps(result))
            
            # MANTENER EL NAVEGADOR ABIERTO (como IQ Option)
            if success:
                logging.info("🎉 ¡Bot conectado y listo para operaciones Quotex!")
                logging.info("💡 El navegador se mantendrá abierto para futuras operaciones")
                
                # Extraer precios reales
                prices = quotex.get_real_prices()
                if prices:
                    logging.info("💰 Precios reales extraídos exitosamente")
                
                input("Presiona ENTER para cerrar el navegador...")
            else:
                logging.info("💡 Asegúrate de estar en la página de trading de Quotex")
                
        elif command == "detect":
            # Comando para solo detectar sin mantener abierto
            if not quotex.setup_driver_existing():
                print(json.dumps({"success": False, "message": "Error configurando ChromeDriver"}))
                return
                
            success = quotex.detect_trading_interface()
            result = {"success": success, "message": "Trading detectado" if success else "Trading no detectado"}
            print(json.dumps(result))
            
        elif command == "prices":
            # Comando para extraer precios
            if not quotex.setup_driver_existing():
                print(json.dumps({"success": False, "message": "Error configurando ChromeDriver"}))
                return
            
            prices = quotex.get_real_prices()
            if prices:
                result = {"success": True, "data": prices}
            else:
                result = {"success": False, "message": "No se pudieron extraer precios"}
            
            print(json.dumps(result))
            
        elif command == "buy":
            if len(sys.argv) < 5:
                print(json.dumps({"success": False, "message": "Parámetros insuficientes"}))
                return
            
            asset = sys.argv[2] if len(sys.argv) > 2 else "UK BRENT"
            amount = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
            direction = sys.argv[4] if len(sys.argv) > 4 else "UP"
            
            if not quotex.setup_driver_existing():
                print(json.dumps({"success": False, "message": "Error configurando ChromeDriver"}))
                return
            
            result = quotex.execute_trade(asset, amount, direction)
            print(json.dumps(result))
            
        else:
            print(json.dumps({"success": False, "message": "Comando no reconocido"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))
    finally:
        if command != "connect":  # No cerrar si es connect para mantener abierto
            quotex.close()

if __name__ == "__main__":
    main()
