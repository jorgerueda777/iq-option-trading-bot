#!/usr/bin/env python3
"""
IQ Option Blitz Smart - Busca botones por texto, no por coordenadas
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

class IQOptionBlitzSmart:
    def __init__(self):
        self.driver = None
        
    def setup_chrome(self):
        """Configurar Chrome nuevo"""
        try:
            logging.info("🔧 Configurando Chrome...")
            
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ Chrome configurado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome: {e}")
            return False
    
    def open_blitz(self):
        """Abrir IQ Option y navegar a Blitz"""
        try:
            logging.info("🌐 Abriendo IQ Option...")
            self.driver.get("https://iqoption.com/")
            
            logging.info("👤 HAZ LOGIN MANUALMENTE - Tienes 30 segundos")
            time.sleep(30)
            
            logging.info("🎯 NAVEGA A BLITZ MANUALMENTE - Tienes 30 segundos")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error abriendo Blitz: {e}")
            return False
    
    def find_blitz_buttons(self):
        """Buscar botones de Blitz por texto"""
        try:
            logging.info("🔍 Buscando botones de Blitz...")
            
            # Lista de posibles textos para botones de compra/venta
            buy_texts = [
                "Higher", "HIGHER", "Compra", "COMPRA", "Call", "CALL", 
                "Up", "UP", "Arriba", "ARRIBA", "Buy", "BUY", "Más alto"
            ]
            
            sell_texts = [
                "Lower", "LOWER", "Venta", "VENTA", "Put", "PUT",
                "Down", "DOWN", "Abajo", "ABAJO", "Sell", "SELL", "Más bajo"
            ]
            
            found_buttons = {"buy": None, "sell": None}
            
            # Buscar todos los botones en la página
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logging.info(f"📊 Encontrados {len(buttons)} botones en total")
            
            for button in buttons:
                try:
                    button_text = button.text.strip()
                    if button_text:
                        logging.info(f"   - Botón: '{button_text}'")
                        
                        # Verificar si es botón de compra
                        if any(text in button_text for text in buy_texts):
                            found_buttons["buy"] = button
                            logging.info(f"✅ Botón COMPRA encontrado: '{button_text}'")
                        
                        # Verificar si es botón de venta
                        elif any(text in button_text for text in sell_texts):
                            found_buttons["sell"] = button
                            logging.info(f"✅ Botón VENTA encontrado: '{button_text}'")
                            
                except Exception as e:
                    continue
            
            return found_buttons
            
        except Exception as e:
            logging.error(f"❌ Error buscando botones: {e}")
            return {"buy": None, "sell": None}
    
    def execute_blitz_trade(self, direction):
        """Ejecutar operación Blitz buscando por texto"""
        try:
            logging.info(f"🎯 Ejecutando Blitz {direction.upper()} buscando por texto")
            
            # Buscar botones
            buttons = self.find_blitz_buttons()
            
            # Seleccionar botón según dirección
            if direction.upper() in ["CALL", "COMPRA", "BUY", "HIGHER"]:
                target_button = buttons["buy"]
                action = "COMPRA"
            else:
                target_button = buttons["sell"] 
                action = "VENTA"
            
            if target_button:
                logging.info(f"🖱️ Haciendo clic en botón {action}: '{target_button.text}'")
                target_button.click()
                
                logging.info(f"✅ Operación {action} ejecutada exitosamente")
                return {
                    "success": True, 
                    "message": f"Blitz {action} ejecutado - Botón: '{target_button.text}'"
                }
            else:
                logging.error(f"❌ No se encontró botón para {action}")
                return {
                    "success": False, 
                    "message": f"No se encontró botón de {action}"
                }
                
        except Exception as e:
            logging.error(f"❌ Error ejecutando Blitz: {e}")
            return {"success": False, "message": str(e)}
    
    def debug_page(self):
        """Mostrar todos los elementos de la página para debug"""
        try:
            logging.info("🔍 DEBUG - Analizando página actual...")
            
            # Esperar a que la página cargue completamente
            logging.info("⏳ Esperando 5 segundos para que cargue completamente...")
            time.sleep(5)
            
            # URL y título
            logging.info(f"📄 URL: {self.driver.current_url}")
            logging.info(f"📄 Título: {self.driver.title}")
            
            # TODOS los elementos con texto (más amplio)
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            logging.info(f"📝 Elementos con texto: {len(all_elements)}")
            for i, elem in enumerate(all_elements[:20]):
                text = elem.text.strip()
                tag = elem.tag_name
                classes = elem.get_attribute("class")
                if text and len(text) < 50:
                    logging.info(f"   {i+1}. [{tag}] '{text}' | Clases: {classes}")
            
            # Buscar específicamente elementos que contengan palabras clave
            keywords = ["higher", "lower", "call", "put", "compra", "venta", "up", "down"]
            logging.info("🔍 Buscando elementos con palabras clave...")
            
            for keyword in keywords:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                if elements:
                    logging.info(f"   🎯 '{keyword}': {len(elements)} elementos encontrados")
                    for elem in elements[:3]:
                        logging.info(f"      - [{elem.tag_name}] '{elem.text.strip()}'")
            
            # Buscar botones específicamente
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logging.info(f"🔘 Botones encontrados: {len(buttons)}")
            for i, btn in enumerate(buttons[:10]):
                text = btn.text.strip()
                classes = btn.get_attribute("class")
                onclick = btn.get_attribute("onclick")
                if text or classes or onclick:
                    logging.info(f"   {i+1}. Texto: '{text}' | Clases: '{classes}' | OnClick: '{onclick}'")
            
            # Buscar elementos clickeables
            clickable = self.driver.find_elements(By.XPATH, "//*[@onclick or @role='button' or contains(@class, 'btn') or contains(@class, 'button')]")
            logging.info(f"🖱️ Elementos clickeables: {len(clickable)}")
            for i, elem in enumerate(clickable[:10]):
                text = elem.text.strip()[:30]
                tag = elem.tag_name
                classes = elem.get_attribute("class")
                if text:
                    logging.info(f"   {i+1}. [{tag}] '{text}' | Clases: '{classes}'")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error en debug: {e}")
            return False
    
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
    blitz = IQOptionBlitzSmart()
    
    try:
        if command == "buy":
            if len(sys.argv) < 3:
                print(json.dumps({"success": False, "message": "Dirección requerida (call/put)"}))
                return
            
            direction = sys.argv[2]
            
            if not blitz.setup_chrome():
                print(json.dumps({"success": False, "message": "Error configurando Chrome"}))
                return
            
            if not blitz.open_blitz():
                print(json.dumps({"success": False, "message": "Error abriendo Blitz"}))
                return
            
            result = blitz.execute_blitz_trade(direction)
            print(json.dumps(result))
            
        elif command == "debug":
            if not blitz.setup_chrome():
                print(json.dumps({"success": False, "message": "Error configurando Chrome"}))
                return
            
            if not blitz.open_blitz():
                print(json.dumps({"success": False, "message": "Error abriendo Blitz"}))
                return
            
            success = blitz.debug_page()
            print(json.dumps({"success": success, "message": "Debug completado"}))
            
        else:
            print(json.dumps({"success": False, "message": f"Comando desconocido: {command}"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))
    finally:
        blitz.close()

if __name__ == "__main__":
    main()
