#!/usr/bin/env python3
"""
IQ Option Blitz Automation
Automatiza las Opciones Blitz usando Selenium WebDriver
"""

import sys
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class IQOptionBlitz:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        self.logged_in = False
        
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
            
            # Usar webdriver-manager para descargar ChromeDriver automáticamente
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ Nueva instancia de Chrome creada")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error creando nueva instancia: {e}")
            return False
        
    def open_iqoption(self):
        """Abrir IQ Option y hacer login automático"""
        try:
            logging.info("🌐 Abriendo IQ Option...")
            self.driver.get("https://iqoption.com/")
            time.sleep(3)
            
            # Intentar login automático
            if self.auto_login():
                return True
            
            logging.info("👤 Login automático falló, esperando login manual...")
            logging.info("⏳ Esperando que hagas login... (tienes 2 minutos)")
            
            # Esperar hasta 2 minutos para que el usuario haga login manualmente
            try:
                # Esperar a que aparezca algún elemento que indique que está logueado
                WebDriverWait(self.driver, 120).until(
                    lambda driver: "iqoption.com/traderoom" in driver.current_url or 
                                  "platform" in driver.current_url.lower() or
                                  len(driver.find_elements(By.XPATH, "//div[contains(@class, 'trading') or contains(@class, 'platform')]")) > 0
                )
                logging.info("✅ Login detectado exitosamente")
                self.logged_in = True
                return True
                
            except TimeoutException:
                logging.error("⏰ Timeout: No se detectó login en 2 minutos")
                return False
            
        except Exception as e:
            logging.error(f"❌ Error abriendo IQ Option: {e}")
            return False
    
    def auto_login(self):
        """Hacer login automático con credenciales"""
        try:
            logging.info("🔐 Intentando login automático...")
            
            # Buscar botón de login
            try:
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Login') or contains(text(), 'Sign in') or contains(@href, 'login')]"))
                )
                login_button.click()
                time.sleep(2)
            except:
                # Tal vez ya estamos en la página de login
                pass
            
            # Buscar campos de login
            try:
                # Email
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username']"))
                )
                email_field.clear()
                email_field.send_keys(self.email)
                time.sleep(1)
                
                # Password
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
                password_field.clear()
                password_field.send_keys(self.password)
                time.sleep(1)
                
                # Submit
                submit_selectors = [
                    "button[type='submit']",
                    "input[type='submit']", 
                    "button:contains('Login')",
                    "button:contains('Sign in')",
                    ".login-button",
                    ".submit-button"
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if submit_button:
                    submit_button.click()
                else:
                    # Presionar Enter en el campo de password
                    password_field.send_keys("\n")
                
                logging.info("🔘 Formulario de login enviado")
                time.sleep(5)
                
                # Verificar si el login fue exitoso
                current_url = self.driver.current_url
                if "traderoom" in current_url or "platform" in current_url or "dashboard" in current_url:
                    logging.info("✅ Login automático exitoso")
                    self.logged_in = True
                    return True
                else:
                    logging.info("❌ Login automático falló")
                    return False
                    
            except Exception as e:
                logging.error(f"❌ Error llenando formulario: {e}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error en login automático: {e}")
            return False
    
    def detect_blitz_now(self):
        """Detectar si ya estamos en Blitz ahora mismo"""
        try:
            logging.info("🔍 Detectando si ya estás en Blitz...")
            
            # Obtener información de la página actual
            current_url = self.driver.current_url
            page_title = self.driver.title
            logging.info(f"📄 URL actual: {current_url}")
            logging.info(f"📄 Título: {page_title}")
            
            # Buscar múltiples indicadores de Blitz
            blitz_indicators = [
                "//button[contains(text(), 'Higher')]",
                "//button[contains(text(), 'Lower')]", 
                "//div[contains(text(), 'Blitz')]",
                "//span[contains(text(), 'Blitz')]",
                "//*[contains(@class, 'blitz')]",
                "//button[contains(@class, 'call')]",
                "//button[contains(@class, 'put')]",
                "//div[contains(text(), 'Profit')]",
                "//div[contains(text(), 'Payout')]"
            ]
            
            found_elements = []
            for indicator in blitz_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if elements:
                    found_elements.append(f"{indicator}: {len(elements)} elementos")
            
            if found_elements:
                logging.info("✅ BLITZ DETECTADO! Elementos encontrados:")
                for element in found_elements:
                    logging.info(f"   - {element}")
                return True
            else:
                logging.info("❌ No se detectó Blitz. Elementos de la página:")
                # Mostrar algunos elementos para debug
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for i, btn in enumerate(buttons[:5]):
                    if btn.text.strip():
                        logging.info(f"   - Botón {i+1}: '{btn.text.strip()}'")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error detectando Blitz: {e}")
            return False
    
    def execute_blitz_trade(self, asset, amount, direction, duration):
        """Ejecutar operación Blitz"""
        try:
            logging.info(f"🎯 Ejecutando Blitz: {asset} {direction} ${amount} por {duration}s")
            
            # Seleccionar asset
            asset_selector = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{asset}')]"))
            )
            asset_selector.click()
            
            # Configurar cantidad
            amount_input = self.driver.find_element(By.XPATH, "//input[@type='number' or contains(@class, 'amount')]")
            amount_input.clear()
            amount_input.send_keys(str(amount))
            
            # Seleccionar dirección (CALL/PUT)
            if direction.upper() == "CALL":
                call_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'call') or contains(text(), 'Higher')]")
                call_btn.click()
            else:
                put_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'put') or contains(text(), 'Lower')]")
                put_btn.click()
            
            # Configurar duración si es necesario
            # (Blitz suele tener duraciones predefinidas)
            
            # Ejecutar operación
            trade_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Trade') or contains(text(), 'Apply')]")
            trade_btn.click()
            
            logging.info("✅ Operación Blitz ejecutada")
            return {"success": True, "message": "Operación Blitz ejecutada exitosamente"}
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando Blitz: {e}")
            return {"success": False, "message": str(e)}
    
    def close(self):
        """Cerrar el navegador"""
        if self.driver:
            self.driver.quit()

def main():
    """Función principal para comunicación con Node.js"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Comando requerido"}))
        return
    
    command = sys.argv[1]
    
    # Credenciales (deberían venir como parámetros)
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    blitz = IQOptionBlitz(email, password)
    
    try:
        if command == "connect":
            if not blitz.setup_driver_existing():
                print(json.dumps({"success": False, "message": "Error configurando ChromeDriver"}))
                return
                
            # Detectar si ya estamos en Blitz
            success = blitz.detect_blitz_now()
            
            result = {"success": success, "message": "Conectado a Blitz" if success else "No se detectó Blitz"}
            print(json.dumps(result))
            
            # MANTENER EL NAVEGADOR ABIERTO
            if success:
                logging.info("🎉 ¡Bot conectado y listo para operaciones Blitz!")
                logging.info("💡 El navegador se mantendrá abierto para futuras operaciones")
                input("Presiona ENTER para cerrar el navegador...")
            else:
                logging.info("💡 Asegúrate de estar en la página de Opciones Blitz")
                
        elif command == "detect":
            # Comando para solo detectar sin mantener abierto
            if not blitz.setup_driver_existing():
                print(json.dumps({"success": False, "message": "Error configurando ChromeDriver"}))
                return
                
            success = blitz.detect_blitz_now()
            result = {"success": success, "message": "Blitz detectado" if success else "Blitz no detectado"}
            print(json.dumps(result))
            
        elif command == "buy":
            if len(sys.argv) < 6:
                print(json.dumps({"success": False, "message": "Parámetros insuficientes"}))
                return
            
            asset = sys.argv[2]
            amount = float(sys.argv[3])
            direction = sys.argv[4]
            duration = int(sys.argv[5])
            
            if not blitz.setup_driver_existing():
                result = {"success": False, "message": "Error configurando ChromeDriver"}
            else:
                if not blitz.open_iqoption():
                    result = {"success": False, "message": "Error abriendo IQ Option"}
                else:
                    result = blitz.execute_blitz_trade(asset, amount, direction, duration)
            
            print(json.dumps(result))
            
        else:
            print(json.dumps({"success": False, "message": f"Comando desconocido: {command}"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))
    finally:
        blitz.close()

if __name__ == "__main__":
    main()
