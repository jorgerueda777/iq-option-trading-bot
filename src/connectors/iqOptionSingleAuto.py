#!/usr/bin/env python3
"""
IQ Option Single Auto - Prueba con 1 operación automática
"""

import sys
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class IQOptionSingleAuto:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        
    def setup_chrome(self):
        """Configurar Chrome"""
        try:
            logging.info("🔧 Configurando Chrome...")
            
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ Chrome configurado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome: {e}")
            return False
    
    def open_iqoption(self):
        """Abrir IQ Option"""
        try:
            logging.info("🌐 Abriendo IQ Option...")
            self.driver.get("https://iqoption.com/")
            
            logging.info("👤 HAZ LOGIN MANUALMENTE - Tienes 30 segundos")
            time.sleep(30)
            
            logging.info("📊 NAVEGA A OPCIONES BINARIAS - Tienes 60 segundos")
            logging.info("   1. Haz clic en '+' (añadir operación)")
            logging.info("   2. Selecciona 'Opciones Binarias'") 
            logging.info("   3. Elige cualquier asset (EURUSD, etc.)")
            logging.info("   4. Asegúrate de ver los botones 'Más alto' y 'Más bajo'")
            time.sleep(60)
            
            # Verificar URL actual
            current_url = self.driver.current_url
            logging.info(f"📄 URL actual: {current_url}")
            
            # NAVEGAR AUTOMÁTICAMENTE A OPCIONES BINARIAS
            if "traderoom" in current_url:
                logging.info("🎯 Navegando automáticamente a opciones binarias...")
                try:
                    # Buscar y hacer clic en opciones binarias
                    binary_selectors = [
                        "//span[contains(text(), 'Binarias')]",
                        "//span[contains(text(), 'Binary')]", 
                        "//div[contains(text(), 'Binarias')]",
                        "//button[contains(text(), 'Binarias')]",
                        "//a[contains(@href, 'binary')]",
                        "//div[contains(@class, 'binary')]"
                    ]
                    
                    for selector in binary_selectors:
                        try:
                            element = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            element.click()
                            logging.info(f"✅ Navegación automática exitosa: {selector}")
                            time.sleep(3)  # Esperar que cargue
                            break
                        except:
                            continue
                            
                except Exception as nav_error:
                    logging.warning(f"⚠️ No se pudo navegar automáticamente: {nav_error}")
                    logging.info("💡 Navega manualmente a opciones binarias")
            
            self.logged_in = True
            return True
            
        except Exception as e:
            logging.error(f"❌ Error abriendo IQ Option: {e}")
            return False
    
    def wait_for_exact_minute(self):
        """Esperar hasta el próximo minuto exacto"""
        try:
            now = datetime.now()
            next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
            wait_seconds = (next_minute - now).total_seconds()
            
            logging.info(f"⏰ Esperando {wait_seconds:.1f} segundos hasta {next_minute.strftime('%H:%M:%S')}")
            time.sleep(wait_seconds - 0.2)  # -200ms para preparar
            
            # Esperar hasta el segundo exacto
            while datetime.now().second != 0:
                time.sleep(0.001)
                
            return True
            
        except Exception as e:
            logging.error(f"❌ Error esperando minuto exacto: {e}")
            return False
    
    def execute_single_trade(self, direction="call"):
        """Ejecutar 1 operación automática"""
        try:
            logging.info(f"🎯 Preparando operación {direction.upper()}...")
            
            # ESPERAR A QUE LA PÁGINA CARGUE COMPLETAMENTE
            logging.info("⏳ Esperando 10 segundos para que carguen los elementos JavaScript...")
            time.sleep(10)
            
            # Buscar botón según dirección (ESPAÑOL + INGLÉS)
            if direction.lower() == "call":
                button_selectors = [
                    # ESPAÑOL - LOS CORRECTOS
                    "//button[contains(text(), 'SUBE')]",
                    "//button[contains(text(), 'Sube')]",
                    "//span[contains(text(), 'SUBE')]//parent::button",
                    "//span[contains(text(), 'Sube')]//parent::button",
                    # OTROS ESPAÑOL
                    "//button[contains(text(), 'Más alto')]",
                    "//button[contains(text(), 'ALTO')]",
                    "//button[contains(text(), 'Arriba')]",
                    "//button[contains(text(), 'Subir')]",
                    # INGLÉS (fallback)
                    "//button[contains(text(), 'Higher')]",
                    "//button[contains(text(), 'Call')]", 
                    "//button[contains(text(), 'UP')]",
                    # POR CLASES
                    "//div[contains(@class, 'call')]//button",
                    "//button[contains(@class, 'call')]",
                    "//button[contains(@class, 'higher')]"
                ]
            else:
                button_selectors = [
                    # ESPAÑOL - LOS CORRECTOS
                    "//button[contains(text(), 'BAJA')]",
                    "//button[contains(text(), 'Baja')]",
                    "//span[contains(text(), 'BAJA')]//parent::button",
                    "//span[contains(text(), 'Baja')]//parent::button",
                    # OTROS ESPAÑOL
                    "//button[contains(text(), 'Más bajo')]",
                    "//button[contains(text(), 'BAJO')]", 
                    "//button[contains(text(), 'Abajo')]",
                    "//button[contains(text(), 'Bajar')]",
                    # INGLÉS (fallback)
                    "//button[contains(text(), 'Lower')]",
                    "//button[contains(text(), 'Put')]",
                    "//button[contains(text(), 'DOWN')]", 
                    # POR CLASES
                    "//div[contains(@class, 'put')]//button",
                    "//button[contains(@class, 'put')]",
                    "//button[contains(@class, 'lower')]"
                ]
            
            # Buscar el botón
            button = None
            for selector in button_selectors:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logging.info(f"✅ Botón encontrado: {selector}")
                    break
                except:
                    continue
            
            if not button:
                logging.error("❌ No se encontró botón de operación")
                
                # DEBUG COMPLETO: Ver exactamente qué está viendo el bot
                logging.info("🔍 DEBUG COMPLETO - ¿Qué ve el bot?")
                try:
                    # URL actual
                    current_url = self.driver.current_url
                    logging.info(f"📄 URL: {current_url}")
                    
                    # Título de la página
                    page_title = self.driver.title
                    logging.info(f"📄 Título: {page_title}")
                    
                    # TODOS los elementos con texto
                    all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
                    logging.info(f"📝 Total elementos con texto: {len(all_elements)}")
                    
                    # Mostrar TODOS los elementos con texto (para ver qué hay)
                    logging.info("📝 TODOS los elementos encontrados:")
                    for i, elem in enumerate(all_elements):
                        text = elem.text.strip()
                        tag = elem.tag_name
                        if text:
                            logging.info(f"   {i+1}. [{tag}] '{text}'")
                    
                    # Buscar específicamente "SUBE" y "BAJA"
                    sube_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'SUBE')]")
                    baja_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'BAJA')]")
                    logging.info(f"🔍 Elementos con 'SUBE': {len(sube_elements)}")
                    logging.info(f"🔍 Elementos con 'BAJA': {len(baja_elements)}")
                    
                    # Si encuentra SUBE/BAJA, mostrar detalles
                    for elem in sube_elements:
                        logging.info(f"   SUBE encontrado: [{elem.tag_name}] '{elem.text}' | Clickeable: {elem.is_enabled()}")
                    for elem in baja_elements:
                        logging.info(f"   BAJA encontrado: [{elem.tag_name}] '{elem.text}' | Clickeable: {elem.is_enabled()}")
                        
                except Exception as debug_error:
                    logging.error(f"Error en debug: {debug_error}")
                
                return False
            
            # Esperar al minuto exacto
            logging.info("⏰ Esperando minuto exacto...")
            self.wait_for_exact_minute()
            
            # EJECUTAR OPERACIÓN
            execute_time = datetime.now()
            button.click()
            
            logging.info(f"🎯 *** OPERACIÓN EJECUTADA *** a las {execute_time.strftime('%H:%M:%S.%f')[:-3]}")
            logging.info(f"✅ Operación {direction.upper()} completada")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando operación: {e}")
            return False
    
    def close(self):
        """Cerrar navegador"""
        if self.driver:
            self.driver.quit()

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Uso: python script.py [call|put]"}))
        return
    
    direction = sys.argv[1]
    bot = IQOptionSingleAuto()
    
    try:
        if not bot.setup_chrome():
            print(json.dumps({"success": False, "message": "Error configurando Chrome"}))
            return
        
        if not bot.open_iqoption():
            print(json.dumps({"success": False, "message": "Error abriendo IQ Option"}))
            return
        
        success = bot.execute_single_trade(direction)
        
        if success:
            print(json.dumps({"success": True, "message": f"Operación {direction.upper()} ejecutada exitosamente"}))
            logging.info("🎉 ¡OPERACIÓN EJECUTADA! Revisa tu cuenta IQ Option")
        else:
            print(json.dumps({"success": False, "message": "Error ejecutando operación"}))
        
        # MANTENER EL BOT ABIERTO PARA MÁS OPERACIONES
        logging.info("🤖 Bot listo para más operaciones...")
        logging.info("💡 Comandos disponibles:")
        logging.info("   - 'call' o 'c' = Operación SUBE")
        logging.info("   - 'put' o 'p' = Operación BAJA") 
        logging.info("   - 'exit' o 'q' = Salir")
        
        while True:
            try:
                command = input("\n🎯 Comando: ").strip().lower()
                
                if command in ['exit', 'q', 'quit', 'salir']:
                    logging.info("👋 Cerrando bot...")
                    break
                elif command in ['call', 'c', 'sube']:
                    logging.info("🟢 Ejecutando CALL...")
                    bot.execute_single_trade("call")
                elif command in ['put', 'p', 'baja']:
                    logging.info("🔴 Ejecutando PUT...")
                    bot.execute_single_trade("put")
                else:
                    logging.info("❓ Comando no reconocido. Usa: call, put, exit")
                    
            except KeyboardInterrupt:
                logging.info("\n👋 Bot cerrado por usuario")
                break
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))
    finally:
        bot.close()

if __name__ == "__main__":
    main()
