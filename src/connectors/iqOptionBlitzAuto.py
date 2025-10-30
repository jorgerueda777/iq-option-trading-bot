#!/usr/bin/env python3
"""
IQ Option Blitz Automático - Hace clics reales en la interfaz
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

class IQOptionBlitzAuto:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Configurar el driver de Chrome"""
        try:
            logging.info("🔧 Configurando ChromeDriver...")
            
            chrome_options = Options()
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
            
            logging.info("✅ ChromeDriver configurado exitosamente")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando ChromeDriver: {e}")
            return False
    
    def open_iqoption_blitz(self):
        """Abrir IQ Option y navegar a Blitz"""
        try:
            logging.info("🌐 Abriendo IQ Option...")
            self.driver.get("https://iqoption.com/")
            
            logging.info("👤 HAZ LOGIN MANUALMENTE - Tienes 60 segundos")
            time.sleep(60)  # Dar tiempo para login manual
            
            logging.info("🎯 Navegando automáticamente a Blitz...")
            
            # Intentar múltiples formas de llegar a Blitz
            try:
                # Método 1: Buscar botón + o similar
                plus_selectors = [
                    "//button[contains(@class, 'plus')]",
                    "//button[contains(text(), '+')]",
                    "//div[contains(@class, 'add')]",
                    "//button[contains(@aria-label, 'add')]"
                ]
                
                plus_btn = None
                for selector in plus_selectors:
                    try:
                        plus_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except:
                        continue
                
                if plus_btn:
                    plus_btn.click()
                    logging.info("✅ Botón + clickeado")
                    time.sleep(2)
                
                # Método 2: Buscar "Options" o "Opciones"
                options_selectors = [
                    "//span[contains(text(), 'Options')]",
                    "//span[contains(text(), 'Opciones')]",
                    "//div[contains(text(), 'Options')]",
                    "//button[contains(text(), 'Options')]"
                ]
                
                options_btn = None
                for selector in options_selectors:
                    try:
                        options_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except:
                        continue
                
                if options_btn:
                    options_btn.click()
                    logging.info("✅ Opciones clickeado")
                    time.sleep(2)
                
                # Método 3: Buscar "Blitz"
                blitz_selectors = [
                    "//span[contains(text(), 'Blitz')]",
                    "//div[contains(text(), 'Blitz')]",
                    "//button[contains(text(), 'Blitz')]"
                ]
                
                blitz_btn = None
                for selector in blitz_selectors:
                    try:
                        blitz_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except:
                        continue
                
                if blitz_btn:
                    blitz_btn.click()
                    logging.info("✅ Blitz clickeado")
                    time.sleep(3)
                
                logging.info("✅ Navegación a Blitz completada")
                return True
                
            except Exception as nav_error:
                logging.error(f"❌ Error navegando: {nav_error}")
                logging.info("💡 NAVEGA MANUALMENTE A BLITZ - Tienes 30 segundos")
                time.sleep(30)
                return True
                
        except Exception as e:
            logging.error(f"❌ Error abriendo IQ Option: {e}")
            return False
    
    def execute_blitz_trade(self, direction, amount=1):
        """Ejecutar operación Blitz automáticamente"""
        try:
            logging.info(f"🎯 Ejecutando Blitz {direction.upper()} ${amount}")
            
            # Buscar botones Higher/Lower con múltiples selectores
            if direction.upper() == "CALL":
                button_selectors = [
                    "//button[contains(text(), 'Higher')]",
                    "//button[contains(text(), 'HIGHER')]", 
                    "//button[contains(text(), 'Call')]",
                    "//button[contains(text(), 'CALL')]",
                    "//button[contains(@class, 'call')]",
                    "//button[contains(@class, 'higher')]",
                    "//div[contains(@class, 'call')]//button",
                    "//div[contains(text(), 'Higher')]//button",
                    "//button[contains(@aria-label, 'higher')]",
                    "//button[contains(@aria-label, 'call')]"
                ]
            else:
                button_selectors = [
                    "//button[contains(text(), 'Lower')]",
                    "//button[contains(text(), 'LOWER')]",
                    "//button[contains(text(), 'Put')]", 
                    "//button[contains(text(), 'PUT')]",
                    "//button[contains(@class, 'put')]",
                    "//button[contains(@class, 'lower')]",
                    "//div[contains(@class, 'put')]//button",
                    "//div[contains(text(), 'Lower')]//button",
                    "//button[contains(@aria-label, 'lower')]",
                    "//button[contains(@aria-label, 'put')]"
                ]
            
            # Intentar encontrar y hacer clic en el botón
            button_clicked = False
            for selector in button_selectors:
                try:
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    logging.info(f"✅ Botón {direction.upper()} clickeado con selector: {selector}")
                    button_clicked = True
                    break
                except:
                    continue
            
            if not button_clicked:
                # Si no encuentra botones, mostrar elementos disponibles
                logging.error("❌ No se encontraron botones Higher/Lower")
                self.debug_page_elements()
                return {"success": False, "message": "No se encontraron botones de operación"}
            
            # Esperar un momento para que se procese
            time.sleep(2)
            
            return {
                "success": True, 
                "message": f"Operación Blitz {direction.upper()} ejecutada automáticamente"
            }
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando Blitz: {e}")
            return {"success": False, "message": str(e)}
    
    def debug_page_elements(self):
        """Mostrar elementos de la página para debug"""
        try:
            logging.info("🔍 DEBUG - Elementos encontrados en la página:")
            
            # Mostrar URL actual
            logging.info(f"📄 URL: {self.driver.current_url}")
            
            # Mostrar botones
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logging.info(f"🔘 Botones encontrados: {len(buttons)}")
            for i, btn in enumerate(buttons[:10]):
                text = btn.text.strip()
                classes = btn.get_attribute("class")
                if text or classes:
                    logging.info(f"   {i+1}. Texto: '{text}' | Clases: '{classes}'")
            
            # Mostrar divs con texto
            divs = self.driver.find_elements(By.TAG_NAME, "div")
            relevant_divs = [div for div in divs[:20] if div.text.strip()]
            logging.info(f"📦 Divs con texto: {len(relevant_divs)}")
            for i, div in enumerate(relevant_divs[:5]):
                text = div.text.strip()[:50]
                logging.info(f"   {i+1}. '{text}'")
                
        except Exception as e:
            logging.error(f"❌ Error en debug: {e}")
    
    def close(self):
        """Cerrar el navegador"""
        if self.driver:
            self.driver.quit()

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Comando requerido"}))
        return
    
    command = sys.argv[1]
    blitz = IQOptionBlitzAuto()
    
    try:
        if command == "start":
            # Iniciar y mantener abierto para operaciones
            if not blitz.setup_driver():
                print(json.dumps({"success": False, "message": "Error configurando driver"}))
                return
                
            if not blitz.open_iqoption_blitz():
                print(json.dumps({"success": False, "message": "Error abriendo Blitz"}))
                return
            
            print(json.dumps({"success": True, "message": "Blitz listo para operaciones"}))
            
            # Mantener abierto para comandos
            logging.info("🎉 Bot Blitz listo - Usa 'python script.py buy call/put' para operar")
            input("Presiona ENTER para cerrar...")
            
        elif command == "buy":
            if len(sys.argv) < 3:
                print(json.dumps({"success": False, "message": "Dirección requerida (call/put)"}))
                return
            
            direction = sys.argv[2]
            amount = float(sys.argv[3]) if len(sys.argv) > 3 else 1
            
            if not blitz.setup_driver():
                print(json.dumps({"success": False, "message": "Error configurando driver"}))
                return
            
            # Asumir que ya está en Blitz
            result = blitz.execute_blitz_trade(direction, amount)
            print(json.dumps(result))
            
        elif command == "debug":
            if not blitz.setup_driver():
                print(json.dumps({"success": False, "message": "Error configurando driver"}))
                return
            
            blitz.driver.get("https://iqoption.com/")
            time.sleep(5)
            blitz.debug_page_elements()
            print(json.dumps({"success": True, "message": "Debug completado"}))
            
        else:
            print(json.dumps({"success": False, "message": f"Comando desconocido: {command}"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))
    finally:
        blitz.close()

if __name__ == "__main__":
    main()
