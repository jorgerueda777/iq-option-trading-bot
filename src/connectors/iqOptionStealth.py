#!/usr/bin/env python3
"""
IQ Option Stealth Bot - Bot avanzado no detectable
Usa técnicas stealth para evitar detección y ejecutar múltiples operaciones
"""

import sys
import json
import time
import logging
import random
import threading
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class IQOptionStealthBot:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.trades_executed = 0
        
    def setup_stealth_chrome(self):
        """Configurar Chrome con técnicas stealth avanzadas"""
        try:
            logging.info("🛡️ Configurando Chrome Stealth...")
            
            # Opciones stealth avanzadas
            options = uc.ChromeOptions()
            
            # Anti-detección
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins-discovery")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            
            # Simular usuario real
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--accept-lang=es-ES,es;q=0.9,en;q=0.8")
            
            # Crear driver stealth
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Scripts anti-detección adicionales
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']})")
            
            # Configurar ventana
            self.driver.set_window_size(1920, 1080)
            self.driver.maximize_window()
            
            logging.info("✅ Chrome Stealth configurado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome Stealth: {e}")
            return False
    
    def human_like_delay(self, min_seconds=0.5, max_seconds=2.0):
        """Delay aleatorio para simular comportamiento humano"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def human_like_typing(self, element, text):
        """Escribir texto de forma humana"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def open_iqoption(self):
        """Abrir IQ Option con comportamiento humano"""
        try:
            logging.info("🌐 Abriendo IQ Option...")
            
            # Navegar a IQ Option
            self.driver.get("https://iqoption.com/")
            self.human_like_delay(2, 4)
            
            logging.info("👤 HAZ LOGIN MANUALMENTE - Tienes 45 segundos")
            logging.info("   1. Ingresa tu email y contraseña")
            logging.info("   2. Haz clic en 'Iniciar sesión'")
            logging.info("   3. Espera a que cargue la plataforma")
            
            # Esperar login manual
            time.sleep(45)
            
            # Verificar si estamos logueados
            current_url = self.driver.current_url
            if "traderoom" in current_url:
                logging.info("✅ Login exitoso - En sala de trading")
                self.logged_in = True
                return True
            else:
                logging.warning("⚠️ Puede que no hayas completado el login")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error abriendo IQ Option: {e}")
            return False
    
    def navigate_to_binaries(self):
        """Navegar a opciones binarias automáticamente"""
        try:
            logging.info("📊 Navegando a opciones binarias...")
            
            # Buscar elementos de navegación
            nav_selectors = [
                "//span[contains(text(), 'Binarias')]",
                "//div[contains(text(), 'Binary')]",
                "//a[contains(@href, 'binary')]",
                "//button[contains(text(), 'Opciones')]"
            ]
            
            for selector in nav_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.human_like_delay(0.5, 1.0)
                    element.click()
                    logging.info(f"✅ Navegación exitosa: {selector}")
                    self.human_like_delay(2, 3)
                    return True
                except:
                    continue
            
            logging.warning("⚠️ No se pudo navegar automáticamente")
            logging.info("💡 Navega manualmente a opciones binarias - 30 segundos")
            time.sleep(30)
            return True
            
        except Exception as e:
            logging.error(f"❌ Error navegando: {e}")
            return False
    
    def find_trade_buttons(self):
        """Buscar botones de trading con múltiples estrategias"""
        try:
            logging.info("🔍 Buscando botones de trading...")
            
            # Esperar a que carguen los elementos
            self.human_like_delay(3, 5)
            
            # Múltiples selectores para botones
            button_selectors = {
                "higher": [
                    "//button[contains(text(), 'SUBE')]",
                    "//button[contains(text(), 'Sube')]", 
                    "//span[contains(text(), 'SUBE')]//parent::button",
                    "//div[contains(text(), 'SUBE')]//parent::button",
                    "//button[contains(text(), 'Higher')]",
                    "//button[contains(text(), 'Call')]",
                    "//button[contains(@class, 'call')]",
                    "//div[contains(@class, 'higher')]//button"
                ],
                "lower": [
                    "//button[contains(text(), 'BAJA')]",
                    "//button[contains(text(), 'Baja')]",
                    "//span[contains(text(), 'BAJA')]//parent::button", 
                    "//div[contains(text(), 'BAJA')]//parent::button",
                    "//button[contains(text(), 'Lower')]",
                    "//button[contains(text(), 'Put')]",
                    "//button[contains(@class, 'put')]",
                    "//div[contains(@class, 'lower')]//button"
                ]
            }
            
            found_buttons = {"higher": None, "lower": None}
            
            # Buscar botones Higher
            for selector in button_selectors["higher"]:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["higher"] = button
                    logging.info(f"✅ Botón HIGHER encontrado: {selector}")
                    break
                except:
                    continue
            
            # Buscar botones Lower
            for selector in button_selectors["lower"]:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["lower"] = button
                    logging.info(f"✅ Botón LOWER encontrado: {selector}")
                    break
                except:
                    continue
            
            return found_buttons
            
        except Exception as e:
            logging.error(f"❌ Error buscando botones: {e}")
            return {"higher": None, "lower": None}
    
    def wait_for_exact_second(self, target_second=0):
        """Esperar hasta el segundo exacto"""
        try:
            while True:
                now = datetime.now()
                if now.second == target_second:
                    return True
                time.sleep(0.001)  # Precisión de milisegundos
        except Exception as e:
            logging.error(f"❌ Error esperando segundo exacto: {e}")
            return False
    
    def execute_single_trade(self, direction):
        """Ejecutar una operación con timing perfecto"""
        try:
            logging.info(f"🎯 Preparando operación {direction.upper()}...")
            
            # Buscar botones
            buttons = self.find_trade_buttons()
            
            # Seleccionar botón
            if direction.lower() in ["call", "higher", "sube"]:
                target_button = buttons["higher"]
                action = "HIGHER"
            else:
                target_button = buttons["lower"]
                action = "LOWER"
            
            if not target_button:
                logging.error(f"❌ No se encontró botón para {action}")
                return False
            
            # Esperar al próximo minuto exacto
            now = datetime.now()
            next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
            wait_seconds = (next_minute - now).total_seconds()
            
            logging.info(f"⏰ Esperando {wait_seconds:.1f}s hasta {next_minute.strftime('%H:%M:%S')}")
            time.sleep(wait_seconds - 0.5)  # -500ms para preparar
            
            # Esperar segundo exacto
            self.wait_for_exact_second(0)
            
            # EJECUTAR OPERACIÓN
            execute_time = datetime.now()
            target_button.click()
            
            logging.info(f"🎯 *** OPERACIÓN {action} EJECUTADA *** a las {execute_time.strftime('%H:%M:%S.%f')[:-3]}")
            self.trades_executed += 1
            
            # Delay post-ejecución
            self.human_like_delay(1, 2)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando operación: {e}")
            return False
    
    def execute_multiple_trades(self, trades):
        """Ejecutar múltiples operaciones simultáneamente"""
        try:
            logging.info(f"🚀 Preparando {len(trades)} operaciones simultáneas...")
            
            # Buscar todos los botones una vez
            buttons = self.find_trade_buttons()
            
            if not buttons["higher"] or not buttons["lower"]:
                logging.error("❌ No se encontraron botones necesarios")
                return False
            
            # Preparar operaciones
            prepared_trades = []
            for trade in trades:
                direction = trade.get("direction", "call").lower()
                if direction in ["call", "higher", "sube"]:
                    button = buttons["higher"]
                    action = "HIGHER"
                else:
                    button = buttons["lower"] 
                    action = "LOWER"
                
                prepared_trades.append({
                    "button": button,
                    "action": action,
                    "asset": trade.get("asset", "UNKNOWN")
                })
            
            # Esperar al próximo minuto exacto
            now = datetime.now()
            next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
            wait_seconds = (next_minute - now).total_seconds()
            
            logging.info(f"⏰ Esperando {wait_seconds:.1f}s hasta {next_minute.strftime('%H:%M:%S')}")
            time.sleep(wait_seconds - 0.5)  # -500ms para preparar
            
            # Esperar segundo exacto
            self.wait_for_exact_second(0)
            
            # EJECUTAR TODAS LAS OPERACIONES SIMULTÁNEAMENTE
            execute_time = datetime.now()
            
            def click_button(trade_data):
                trade_data["button"].click()
                logging.info(f"✅ {trade_data['action']} ejecutado para {trade_data['asset']}")
            
            # Crear threads para clics simultáneos
            threads = []
            for trade in prepared_trades:
                thread = threading.Thread(target=click_button, args=(trade,))
                threads.append(thread)
            
            # Ejecutar todos los clics AL MISMO TIEMPO
            for thread in threads:
                thread.start()
            
            # Esperar que terminen
            for thread in threads:
                thread.join()
            
            logging.info(f"🎉 *** {len(trades)} OPERACIONES EJECUTADAS SIMULTÁNEAMENTE *** a las {execute_time.strftime('%H:%M:%S.%f')[:-3]}")
            self.trades_executed += len(trades)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando múltiples operaciones: {e}")
            return False
    
    def close(self):
        """Cerrar navegador"""
        if self.driver:
            self.driver.quit()

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Uso: python script.py [single|multi] [call|put]"}))
        return
    
    command = sys.argv[1]
    bot = IQOptionStealthBot()
    
    try:
        # Configurar Chrome Stealth
        if not bot.setup_stealth_chrome():
            print(json.dumps({"success": False, "message": "Error configurando Chrome Stealth"}))
            return
        
        # Abrir IQ Option
        if not bot.open_iqoption():
            print(json.dumps({"success": False, "message": "Error abriendo IQ Option"}))
            return
        
        # Navegar a binarias
        if not bot.navigate_to_binaries():
            print(json.dumps({"success": False, "message": "Error navegando a binarias"}))
            return
        
        if command == "single":
            if len(sys.argv) < 3:
                direction = "call"
            else:
                direction = sys.argv[2]
            
            success = bot.execute_single_trade(direction)
            
            if success:
                print(json.dumps({"success": True, "message": f"Operación {direction.upper()} ejecutada"}))
            else:
                print(json.dumps({"success": False, "message": "Error ejecutando operación"}))
        
        elif command == "multi":
            # Ejemplo de múltiples operaciones
            trades = [
                {"asset": "EURUSD", "direction": "call"},
                {"asset": "GBPUSD", "direction": "put"},
                {"asset": "USDJPY", "direction": "call"},
                {"asset": "AUDUSD", "direction": "put"}
            ]
            
            success = bot.execute_multiple_trades(trades)
            
            if success:
                print(json.dumps({"success": True, "message": f"{len(trades)} operaciones ejecutadas"}))
            else:
                print(json.dumps({"success": False, "message": "Error ejecutando operaciones múltiples"}))
        
        # Mantener bot abierto para más operaciones
        logging.info("🤖 Bot Stealth listo para más operaciones...")
        logging.info("💡 Comandos disponibles:")
        logging.info("   - 'c' = Operación CALL")
        logging.info("   - 'p' = Operación PUT")
        logging.info("   - 'm' = Múltiples operaciones")
        logging.info("   - 'q' = Salir")
        
        while True:
            try:
                command = input("\n🎯 Comando: ").strip().lower()
                
                if command in ['q', 'quit', 'exit']:
                    logging.info("👋 Cerrando bot...")
                    break
                elif command == 'c':
                    bot.execute_single_trade("call")
                elif command == 'p':
                    bot.execute_single_trade("put")
                elif command == 'm':
                    trades = [
                        {"asset": "EURUSD", "direction": "call"},
                        {"asset": "GBPUSD", "direction": "put"}
                    ]
                    bot.execute_multiple_trades(trades)
                else:
                    logging.info("❓ Comando no reconocido")
                    
            except KeyboardInterrupt:
                logging.info("\n👋 Bot cerrado por usuario")
                break
        
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))
    finally:
        bot.close()

if __name__ == "__main__":
    main()
