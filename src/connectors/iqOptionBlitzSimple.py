#!/usr/bin/env python3
"""
IQ Option Blitz Simple - Solo ejecuta operaciones
Asume que ya estás en Blitz y ejecuta operaciones directamente
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

class IQOptionBlitzSimple:
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
    
    def execute_blitz_trade(self, asset, amount, direction):
        """Ejecutar operación Blitz (asume que ya estás en la página de Blitz)"""
        try:
            logging.info(f"🎯 Ejecutando Blitz: {asset} {direction} ${amount}")
            
            # Método 1: Buscar botones Higher/Lower directamente
            try:
                if direction.upper() == "CALL":
                    # Buscar botón Higher/Call
                    call_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Higher') or contains(text(), 'Call') or contains(@class, 'call') or contains(@class, 'higher')]"))
                    )
                    call_btn.click()
                    logging.info("✅ Botón CALL/Higher clickeado")
                else:
                    # Buscar botón Lower/Put
                    put_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Lower') or contains(text(), 'Put') or contains(@class, 'put') or contains(@class, 'lower')]"))
                    )
                    put_btn.click()
                    logging.info("✅ Botón PUT/Lower clickeado")
                
                return {"success": True, "message": f"Operación Blitz {direction} ejecutada"}
                
            except TimeoutException:
                logging.error("❌ No se encontraron botones Higher/Lower")
                return {"success": False, "message": "No se encontraron botones de operación"}
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando Blitz: {e}")
            return {"success": False, "message": str(e)}
    
    def get_page_info(self):
        """Obtener información de la página actual para debug"""
        try:
            url = self.driver.current_url
            title = self.driver.title
            
            # Buscar elementos relevantes
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            button_texts = [btn.text for btn in buttons[:10] if btn.text.strip()]
            
            return {
                "url": url,
                "title": title,
                "buttons": button_texts
            }
        except Exception as e:
            return {"error": str(e)}
    
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
    blitz = IQOptionBlitzSimple()
    
    try:
        if command == "info":
            # Conectar a una ventana de Chrome existente
            blitz.setup_driver()
            info = blitz.get_page_info()
            print(json.dumps({"success": True, "info": info}))
            
        elif command == "buy":
            if len(sys.argv) < 5:
                print(json.dumps({"success": False, "message": "Parámetros insuficientes: asset amount direction"}))
                return
            
            asset = sys.argv[2]
            amount = float(sys.argv[3])
            direction = sys.argv[4]
            
            blitz.setup_driver()
            result = blitz.execute_blitz_trade(asset, amount, direction)
            print(json.dumps(result))
            
        else:
            print(json.dumps({"success": False, "message": f"Comando desconocido: {command}"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))
    finally:
        blitz.close()

if __name__ == "__main__":
    main()
