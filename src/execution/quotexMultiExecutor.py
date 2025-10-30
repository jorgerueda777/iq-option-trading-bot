#!/usr/bin/env python3
"""
Quotex Multi Executor - Ejecuta múltiples operaciones simultáneas
Lee señales del analizador y ejecuta en ventanas separadas
"""

import sys
import json
import time
import logging
import threading
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexMultiExecutor:
    def __init__(self):
        self.drivers = {}  # Un driver por activo
        self.windows = {}  # Información de ventanas
        self.logged_in = False
        self.trades_executed = 0
        
        # Activos OTC 24/7
        self.assets = ["MICROSOFT", "ADA", "USDINR", "USDEGP", "UK BRENT", "ETH"]
        
    def setup_chrome_instance(self, asset_name):
        """Configurar una instancia de Chrome para un activo"""
        try:
            logging.info(f"🛡️ Configurando Chrome para {asset_name}...")
            
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(f"--user-data-dir=C:/temp/chrome_{asset_name}")
            
            driver = uc.Chrome(options=options, version_main=None)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Posicionar ventanas para no solaparse
            positions = {
                "MICROSOFT": (0, 0),
                "ADA": (640, 0), 
                "USDINR": (1280, 0),
                "USDEGP": (0, 400),
                "UK BRENT": (640, 400),
                "ETH": (1280, 400)
            }
            
            if asset_name in positions:
                x, y = positions[asset_name]
                driver.set_window_position(x, y)
                driver.set_window_size(640, 400)
            
            self.drivers[asset_name] = driver
            logging.info(f"✅ Chrome {asset_name} configurado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando {asset_name}: {e}")
            return False
    
    def open_quotex_window(self, asset_name):
        """Abrir Quotex en una ventana específica"""
        try:
            driver = self.drivers[asset_name]
            logging.info(f"🌐 Abriendo Quotex para {asset_name}...")
            
            driver.get("https://qxbroker.com/")
            time.sleep(3)
            
            # Guardar información de la ventana
            self.windows[asset_name] = {
                "driver": driver,
                "asset": asset_name,
                "logged_in": False,
                "buttons": None
            }
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error abriendo {asset_name}: {e}")
            return False
    
    def setup_all_windows(self):
        """Configurar todas las ventanas necesarias"""
        try:
            logging.info("🚀 CONFIGURANDO MÚLTIPLES VENTANAS...")
            
            # Solo configurar ventanas para activos con señales
            signals = self.load_current_signals()
            
            if not signals:
                logging.warning("⚠️ No hay señales disponibles")
                return False
            
            assets_needed = list(signals.keys())
            logging.info(f"📊 Configurando ventanas para: {assets_needed}")
            
            # Configurar Chrome para cada activo
            for asset in assets_needed:
                if not self.setup_chrome_instance(asset):
                    return False
                if not self.open_quotex_window(asset):
                    return False
                time.sleep(2)  # Delay entre ventanas
            
            logging.info(f"✅ {len(assets_needed)} ventanas configuradas")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando ventanas: {e}")
            return False
    
    def login_all_windows(self):
        """Login manual en todas las ventanas"""
        try:
            logging.info("👤 HACER LOGIN EN TODAS LAS VENTANAS - 90 segundos")
            logging.info("   📧 Email: arnolbrom634@gmail.com")
            logging.info("   🔑 Password: 7decadames")
            logging.info("   ⚠️ Haz login en cada ventana que se abrió")
            
            # Esperar login manual
            time.sleep(90)
            
            # Verificar login en cada ventana
            logged_count = 0
            for asset, window_info in self.windows.items():
                try:
                    driver = window_info["driver"]
                    current_url = driver.current_url
                    
                    if "qxbroker.com" in current_url:
                        window_info["logged_in"] = True
                        logged_count += 1
                        logging.info(f"✅ {asset}: Login exitoso")
                    else:
                        logging.warning(f"⚠️ {asset}: Login pendiente")
                        
                except Exception as e:
                    logging.error(f"❌ {asset}: Error verificando login")
            
            if logged_count > 0:
                logging.info(f"✅ {logged_count}/{len(self.windows)} ventanas con login exitoso")
                self.logged_in = True
                return True
            else:
                logging.error("❌ No se completó login en ninguna ventana")
                return False
            
        except Exception as e:
            logging.error(f"❌ Error en login: {e}")
            return False
    
    def find_buttons_in_window(self, asset):
        """Buscar botones UP/DOWN en una ventana específica"""
        try:
            driver = self.drivers[asset]
            logging.info(f"🔍 Buscando botones en {asset}...")
            
            # Selectores optimizados
            button_selectors = {
                "up": [
                    "//button[contains(@class, 'call')]",
                    "//button[contains(@class, 'up')]",
                    "//button[contains(text(), 'UP')]",
                    "//button[contains(text(), 'Arriba')]"
                ],
                "down": [
                    "//button[contains(@class, 'put')]",
                    "//button[contains(@class, 'down')]", 
                    "//button[contains(text(), 'DOWN')]",
                    "//button[contains(text(), 'Abajo')]"
                ]
            }
            
            found_buttons = {"up": None, "down": None}
            
            # Buscar UP
            for selector in button_selectors["up"]:
                try:
                    button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["up"] = button
                    break
                except:
                    continue
            
            # Buscar DOWN
            for selector in button_selectors["down"]:
                try:
                    button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["down"] = button
                    break
                except:
                    continue
            
            if found_buttons["up"] and found_buttons["down"]:
                self.windows[asset]["buttons"] = found_buttons
                logging.info(f"✅ {asset}: Botones encontrados")
                return True
            else:
                logging.warning(f"⚠️ {asset}: Botones no encontrados")
                return False
            
        except Exception as e:
            logging.error(f"❌ Error buscando botones {asset}: {e}")
            return False
    
    def prepare_all_windows(self):
        """Preparar todas las ventanas con botones"""
        try:
            logging.info("🔧 PREPARANDO TODAS LAS VENTANAS...")
            
            prepared_count = 0
            for asset in self.windows.keys():
                if self.find_buttons_in_window(asset):
                    prepared_count += 1
            
            logging.info(f"✅ {prepared_count}/{len(self.windows)} ventanas preparadas")
            return prepared_count > 0
            
        except Exception as e:
            logging.error(f"❌ Error preparando ventanas: {e}")
            return False
    
    def load_current_signals(self):
        """Cargar señales actuales del archivo"""
        try:
            with open("D:/iq_quot/signals/current_signals.json", "r") as f:
                signals = json.load(f)
            
            logging.info(f"📊 Señales cargadas: {len(signals)}")
            for asset, signal in signals.items():
                direction = signal["direction"]
                probability = signal["probability"]
                execute_at = signal.get("execute_at", "INMEDIATO")
                command = signal.get("command", f"{asset} {direction}")
                emoji = "🟢" if direction == "UP" else "🔴"
                logging.info(f"   {emoji} {command}")
                logging.info(f"      📊 Probabilidad: {probability*100:.0f}%")
                logging.info(f"      ⏰ Ejecutar a las: {execute_at}")
            
            return signals
            
        except FileNotFoundError:
            logging.error("❌ No se encontró archivo de señales")
            return {}
        except Exception as e:
            logging.error(f"❌ Error cargando señales: {e}")
            return {}
    
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
    
    def execute_simultaneous_trades(self):
        """Ejecutar todas las operaciones simultáneamente"""
        try:
            # Cargar señales actuales
            signals = self.load_current_signals()
            
            if not signals:
                logging.error("❌ No hay señales para ejecutar")
                return False
            
            logging.info("🚀 PREPARANDO EJECUCIÓN SIMULTÁNEA...")
            logging.info("=" * 60)
            
            # Preparar operaciones
            prepared_trades = []
            
            for asset, signal in signals.items():
                if asset in self.windows and self.windows[asset].get("buttons"):
                    direction = signal["direction"]
                    probability = signal["probability"]
                    
                    if direction == "UP":
                        button = self.windows[asset]["buttons"]["up"]
                        action = "UP"
                    else:
                        button = self.windows[asset]["buttons"]["down"]
                        action = "DOWN"
                    
                    prepared_trades.append({
                        "asset": asset,
                        "button": button,
                        "action": action,
                        "probability": probability,
                        "driver": self.drivers[asset]
                    })
                    
                    emoji = "🟢" if action == "UP" else "🔴"
                    logging.info(f"   {emoji} {asset}: {action} ({probability*100:.0f}%)")
            
            if not prepared_trades:
                logging.error("❌ No hay operaciones preparadas")
                return False
            
            logging.info("=" * 60)
            
            # Esperar al próximo minuto exacto
            now = datetime.now()
            next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
            wait_seconds = (next_minute - now).total_seconds()
            
            logging.info(f"⏰ EJECUTANDO EN {wait_seconds:.1f}s - {next_minute.strftime('%H:%M:%S')}")
            time.sleep(wait_seconds - 0.5)  # -500ms para preparar
            
            # Esperar segundo exacto
            self.wait_for_exact_second(0)
            
            # EJECUTAR TODAS LAS OPERACIONES AL MISMO TIEMPO
            execute_time = datetime.now()
            
            def execute_trade(trade_data):
                try:
                    trade_data["button"].click()
                    logging.info(f"✅ {trade_data['asset']} {trade_data['action']} EJECUTADO")
                except Exception as e:
                    logging.error(f"❌ Error {trade_data['asset']}: {e}")
            
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
            
            logging.info("🎉" * 20)
            logging.info(f"🎯 *** {len(prepared_trades)} OPERACIONES EJECUTADAS SIMULTÁNEAMENTE ***")
            logging.info(f"⏰ TIEMPO: {execute_time.strftime('%H:%M:%S.%f')[:-3]}")
            logging.info("🎉" * 20)
            
            self.trades_executed += len(prepared_trades)
            return True
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando operaciones: {e}")
            return False
    
    def close_all(self):
        """Cerrar todas las ventanas"""
        for asset, driver in self.drivers.items():
            try:
                driver.quit()
                logging.info(f"👋 {asset} cerrado")
            except:
                pass

def main():
    """Función principal"""
    executor = QuotexMultiExecutor()
    
    try:
        # Configurar todas las ventanas
        if not executor.setup_all_windows():
            return
        
        # Login en todas las ventanas
        if not executor.login_all_windows():
            return
        
        # Preparar ventanas con botones
        if not executor.prepare_all_windows():
            return
        
        # Ejecutar operaciones simultáneas
        success = executor.execute_simultaneous_trades()
        
        if success:
            logging.info("🎉 ¡EJECUCIÓN SIMULTÁNEA COMPLETADA!")
        else:
            logging.error("❌ Error en ejecución simultánea")
        
        # Mantener abierto para más operaciones
        logging.info("🤖 Executor listo para más operaciones...")
        logging.info("💡 Comandos disponibles:")
        logging.info("   - 'execute' = Ejecutar señales actuales")
        logging.info("   - 'reload' = Recargar señales")
        logging.info("   - 'q' = Salir")
        
        while True:
            try:
                command = input("\n🎯 Comando: ").strip().lower()
                
                if command in ['q', 'quit', 'exit']:
                    logging.info("👋 Cerrando executor...")
                    break
                elif command == 'execute':
                    executor.execute_simultaneous_trades()
                elif command == 'reload':
                    signals = executor.load_current_signals()
                    logging.info(f"🔄 {len(signals)} señales recargadas")
                else:
                    logging.info("❓ Comando no reconocido")
                    
            except KeyboardInterrupt:
                logging.info("\n👋 Executor cerrado por usuario")
                break
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
    finally:
        executor.close_all()

if __name__ == "__main__":
    main()
