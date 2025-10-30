#!/usr/bin/env python3
"""
Quotex Multi-Window Bot - Múltiples ventanas para diferentes pares
Abre una pestaña por cada par de divisas para operaciones simultáneas
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

class QuotexMultiWindowBot:
    def __init__(self):
        self.driver = None
        self.windows = {}  # Diccionario para almacenar ventanas por par
        self.logged_in = False
        self.trades_executed = 0
        
    def setup_stealth_chrome(self):
        """Configurar Chrome con técnicas stealth"""
        try:
            logging.info("🛡️ Configurando Chrome Multi-Window...")
            
            options = uc.ChromeOptions()
            
            # Anti-detección
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins-discovery")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            
            # User agent realista
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Crear driver stealth
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Scripts anti-detección
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']})")
            
            # Configurar ventana
            self.driver.set_window_size(1920, 1080)
            self.driver.maximize_window()
            
            logging.info("✅ Chrome Multi-Window configurado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome: {e}")
            return False
    
    def human_like_delay(self, min_seconds=0.5, max_seconds=2.0):
        """Delay aleatorio para simular comportamiento humano"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def open_quotex_main(self):
        """Abrir ventana principal de Quotex"""
        try:
            logging.info("🌐 Abriendo Quotex principal...")
            
            # Navegar a Quotex
            self.driver.get("https://qxbroker.com/")
            self.human_like_delay(3, 5)
            
            logging.info("👤 HAZ LOGIN MANUALMENTE - Tienes 60 segundos")
            logging.info("   1. Haz clic en 'Sign In'")
            logging.info("   2. Email: arnolbrom634@gmail.com")
            logging.info("   3. Password: 7decadames")
            logging.info("   4. Haz clic en 'Sign In'")
            
            # Esperar login
            time.sleep(60)
            
            # Verificar login
            current_url = self.driver.current_url
            if "trade" in current_url or "platform" in current_url or "qxbroker.com" in current_url:
                logging.info("✅ Login exitoso en ventana principal")
                self.logged_in = True
                
                # Guardar ventana principal
                main_window = self.driver.current_window_handle
                self.windows["MAIN"] = {
                    "handle": main_window,
                    "pair": "EURUSD",
                    "buttons": None
                }
                
                return True
            else:
                logging.error("❌ Login fallido")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error abriendo Quotex: {e}")
            return False
    
    def open_additional_windows(self, pairs):
        """Abrir ventanas adicionales para cada par"""
        try:
            logging.info(f"🚀 Abriendo {len(pairs)} ventanas adicionales...")
            
            for i, pair in enumerate(pairs):
                if pair == "EURUSD":  # Ya tenemos la ventana principal
                    continue
                    
                logging.info(f"🌐 Abriendo ventana para {pair}...")
                
                # Abrir nueva pestaña
                self.driver.execute_script("window.open('https://qxbroker.com/', '_blank');")
                self.human_like_delay(2, 3)
                
                # Cambiar a la nueva pestaña
                new_window = self.driver.window_handles[-1]
                self.driver.switch_to.window(new_window)
                
                # Esperar a que cargue
                self.human_like_delay(5, 8)
                
                # Guardar información de la ventana
                self.windows[pair] = {
                    "handle": new_window,
                    "pair": pair,
                    "buttons": None
                }
                
                logging.info(f"✅ Ventana {pair} abierta")
            
            logging.info(f"🎉 {len(self.windows)} ventanas abiertas total")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error abriendo ventanas adicionales: {e}")
            return False
    
    def find_buttons_in_window(self, window_handle):
        """Buscar botones en una ventana específica"""
        try:
            # Cambiar a la ventana
            self.driver.switch_to.window(window_handle)
            self.human_like_delay(1, 2)
            
            # Buscar botones UP/DOWN
            button_selectors = {
                "up": [
                    "//button[contains(text(), 'UP')]",
                    "//button[contains(text(), 'Up')]",
                    "//div[contains(text(), 'UP')]//parent::button",
                    "//span[contains(text(), 'UP')]//parent::button",
                    "//button[contains(@class, 'up')]",
                    "//button[contains(@class, 'call')]",
                    "//button[contains(@class, 'green')]"
                ],
                "down": [
                    "//button[contains(text(), 'DOWN')]",
                    "//button[contains(text(), 'Down')]",
                    "//div[contains(text(), 'DOWN')]//parent::button",
                    "//span[contains(text(), 'DOWN')]//parent::button",
                    "//button[contains(@class, 'down')]",
                    "//button[contains(@class, 'put')]",
                    "//button[contains(@class, 'red')]"
                ]
            }
            
            found_buttons = {"up": None, "down": None}
            
            # Buscar botones UP
            for selector in button_selectors["up"]:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["up"] = button
                    break
                except:
                    continue
            
            # Buscar botones DOWN
            for selector in button_selectors["down"]:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["down"] = button
                    break
                except:
                    continue
            
            return found_buttons
            
        except Exception as e:
            logging.error(f"❌ Error buscando botones en ventana: {e}")
            return {"up": None, "down": None}
    
    def prepare_all_windows(self):
        """Preparar todas las ventanas con sus botones"""
        try:
            logging.info("🔧 Preparando todas las ventanas...")
            
            for pair, window_info in self.windows.items():
                logging.info(f"🔍 Preparando ventana {pair}...")
                
                buttons = self.find_buttons_in_window(window_info["handle"])
                
                if buttons["up"] and buttons["down"]:
                    window_info["buttons"] = buttons
                    logging.info(f"✅ Ventana {pair} preparada")
                else:
                    logging.warning(f"⚠️ Ventana {pair} sin botones")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error preparando ventanas: {e}")
            return False
    
    def wait_for_exact_second(self, target_second=0):
        """Esperar hasta el segundo exacto"""
        try:
            while True:
                now = datetime.now()
                if now.second == target_second:
                    return True
                time.sleep(0.001)
        except Exception as e:
            logging.error(f"❌ Error esperando segundo exacto: {e}")
            return False
    
    def execute_simultaneous_trades(self, trades):
        """Ejecutar operaciones simultáneas en múltiples ventanas"""
        try:
            logging.info(f"🚀 Ejecutando {len(trades)} operaciones simultáneas...")
            
            # Preparar operaciones
            prepared_trades = []
            
            for trade in trades:
                pair = trade.get("asset", "EURUSD")
                direction = trade.get("direction", "call").lower()
                
                if pair in self.windows:
                    window_info = self.windows[pair]
                    
                    if window_info["buttons"]:
                        if direction in ["call", "up", "higher"]:
                            button = window_info["buttons"]["up"]
                            action = "UP"
                        else:
                            button = window_info["buttons"]["down"]
                            action = "DOWN"
                        
                        prepared_trades.append({
                            "window_handle": window_info["handle"],
                            "button": button,
                            "action": action,
                            "pair": pair
                        })
                        
                        logging.info(f"✅ {pair} {action} preparado")
                    else:
                        logging.warning(f"⚠️ {pair} sin botones")
                else:
                    logging.warning(f"⚠️ Ventana para {pair} no encontrada")
            
            if not prepared_trades:
                logging.error("❌ No hay operaciones preparadas")
                return False
            
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
            
            def execute_trade(trade_data):
                try:
                    # Cambiar a la ventana
                    self.driver.switch_to.window(trade_data["window_handle"])
                    # Hacer clic
                    trade_data["button"].click()
                    logging.info(f"✅ {trade_data['pair']} {trade_data['action']} EJECUTADO")
                except Exception as e:
                    logging.error(f"❌ Error en {trade_data['pair']}: {e}")
            
            # Crear threads para ejecución simultánea
            threads = []
            for trade in prepared_trades:
                thread = threading.Thread(target=execute_trade, args=(trade,))
                threads.append(thread)
            
            # Ejecutar todos AL MISMO TIEMPO
            for thread in threads:
                thread.start()
            
            # Esperar que terminen
            for thread in threads:
                thread.join()
            
            logging.info(f"🎉 *** {len(prepared_trades)} OPERACIONES EJECUTADAS SIMULTÁNEAMENTE *** a las {execute_time.strftime('%H:%M:%S.%f')[:-3]}")
            self.trades_executed += len(prepared_trades)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando operaciones simultáneas: {e}")
            return False
    
    def close(self):
        """Cerrar navegador"""
        if self.driver:
            self.driver.quit()

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Uso: python script.py [multi]"}))
        return
    
    command = sys.argv[1]
    bot = QuotexMultiWindowBot()
    
    try:
        # Configurar Chrome
        if not bot.setup_stealth_chrome():
            print(json.dumps({"success": False, "message": "Error configurando Chrome"}))
            return
        
        # Abrir ventana principal
        if not bot.open_quotex_main():
            print(json.dumps({"success": False, "message": "Error abriendo Quotex"}))
            return
        
        # Definir pares para múltiples ventanas
        pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
        
        # Abrir ventanas adicionales
        if not bot.open_additional_windows(pairs):
            print(json.dumps({"success": False, "message": "Error abriendo ventanas adicionales"}))
            return
        
        # Preparar todas las ventanas
        if not bot.prepare_all_windows():
            print(json.dumps({"success": False, "message": "Error preparando ventanas"}))
            return
        
        if command == "multi":
            # Operaciones simultáneas en diferentes pares
            trades = [
                {"asset": "EURUSD", "direction": "call"},
                {"asset": "GBPUSD", "direction": "put"},
                {"asset": "USDJPY", "direction": "call"},
                {"asset": "AUDUSD", "direction": "put"},
                {"asset": "USDCAD", "direction": "call"}
            ]
            
            success = bot.execute_simultaneous_trades(trades)
            
            if success:
                print(json.dumps({"success": True, "message": f"{len(trades)} operaciones en diferentes pares"}))
            else:
                print(json.dumps({"success": False, "message": "Error ejecutando operaciones"}))
        
        # Mantener bot abierto
        logging.info("🤖 Bot Multi-Window listo...")
        logging.info("💡 Comandos disponibles:")
        logging.info("   - 'm' = Ejecutar operaciones en todos los pares")
        logging.info("   - 'q' = Salir")
        
        while True:
            try:
                command = input("\n🎯 Comando: ").strip().lower()
                
                if command in ['q', 'quit', 'exit']:
                    logging.info("👋 Cerrando bot...")
                    break
                elif command == 'm':
                    trades = [
                        {"asset": "EURUSD", "direction": "call"},
                        {"asset": "GBPUSD", "direction": "put"},
                        {"asset": "USDJPY", "direction": "call"},
                        {"asset": "AUDUSD", "direction": "put"},
                        {"asset": "USDCAD", "direction": "call"}
                    ]
                    bot.execute_simultaneous_trades(trades)
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
