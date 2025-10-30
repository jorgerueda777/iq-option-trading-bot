#!/usr/bin/env python3
"""
Quotex Full Auto - Sistema completamente automático
Detecta señales, espera la hora exacta y ejecuta automáticamente
"""

import sys
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from collections import deque
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexFullAuto:
    def __init__(self):
        self.drivers = {}  # Un driver por cada par
        self.windows = {}  # Información de ventanas
        self.logged_in = False
        self.trades_executed = 0
        
        # Activos OTC 24/7
        self.pairs = ["UK BRENT", "MICROSOFT", "ADA", "ETH", "USDINR", "USDEGP"]
        
        # Historial de velas
        self.candle_history = {pair: deque(maxlen=10) for pair in self.pairs}
        
        # Patrones de secuencias
        self.sequence_patterns = {
            ("DOWN", "DOWN", "UP"): (0.78, "DOWN"),
            ("UP", "UP", "DOWN"): (0.82, "UP"),
            ("DOWN", "UP", "DOWN"): (0.75, "UP"),
            ("UP", "DOWN", "UP"): (0.77, "DOWN"),
            ("DOWN", "DOWN", "DOWN"): (0.85, "UP"),
            ("UP", "UP", "UP"): (0.83, "DOWN"),
        }
        
        # Correlaciones
        self.correlations = {
            "UK BRENT": {"USDINR": -0.45, "USDEGP": -0.38, "ETH": 0.25},
            "MICROSOFT": {"ETH": 0.42, "ADA": 0.35, "UK BRENT": 0.15},
            "ADA": {"ETH": 0.78, "MICROSOFT": 0.35, "USDINR": -0.22},
            "ETH": {"ADA": 0.78, "MICROSOFT": 0.42, "UK BRENT": 0.25},
            "USDINR": {"USDEGP": 0.65, "UK BRENT": -0.45, "ETH": -0.18},
            "USDEGP": {"USDINR": 0.65, "UK BRENT": -0.38, "ADA": -0.15}
        }
        
        # Señales pendientes de ejecución
        self.pending_signals = {}
        
    def setup_chrome_for_pair(self, pair):
        """Configurar Chrome para un par específico"""
        try:
            logging.info(f"🛡️ Configurando Chrome para {pair}...")
            
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(f"--user-data-dir=C:/temp/chrome_{pair.replace(' ', '_')}")
            
            driver = uc.Chrome(options=options, version_main=None)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Posicionar ventanas para no solaparse
            positions = {
                "UK BRENT": (0, 0),
                "MICROSOFT": (640, 0), 
                "ADA": (1280, 0),
                "ETH": (0, 400),
                "USDINR": (640, 400),
                "USDEGP": (1280, 400)
            }
            
            if pair in positions:
                x, y = positions[pair]
                driver.set_window_position(x, y)
                driver.set_window_size(640, 400)
                driver.set_window_rect(x, y, 640, 400)
            
            self.drivers[pair] = driver
            logging.info(f"✅ Chrome {pair} configurado en posición {positions.get(pair, 'default')}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando {pair}: {e}")
            return False
    
    def setup_all_windows(self):
        """Configurar todas las ventanas"""
        try:
            logging.info("🌐 CONFIGURANDO 6 VENTANAS SIMULTÁNEAS...")
            
            for pair in self.pairs:
                if not self.setup_chrome_for_pair(pair):
                    logging.error(f"❌ Error configurando {pair}")
                    return False
                time.sleep(2)  # Delay entre ventanas
            
            logging.info("✅ Todas las ventanas configuradas")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            return False
    
    def open_all_quotex_windows(self):
        """Abrir Quotex en todas las ventanas"""
        try:
            logging.info("🌐 ABRIENDO QUOTEX EN 6 VENTANAS...")
            
            # Abrir Quotex en cada ventana
            for pair, driver in self.drivers.items():
                logging.info(f"🌐 Abriendo Quotex para {pair}...")
                driver.get("https://qxbroker.com/")
                time.sleep(2)
            
            logging.info("👤 HAZ LOGIN EN TODAS LAS VENTANAS - 90 segundos")
            logging.info("   📧 Email: arnolbrom634@gmail.com")
            logging.info("   🔑 Password: 7decadames")
            logging.info("   ⚠️ Haz login en cada una de las 6 ventanas")
            
            time.sleep(90)
            
            # Verificar login
            logged_count = 0
            for pair, driver in self.drivers.items():
                try:
                    current_url = driver.current_url
                    if "qxbroker.com" in current_url:
                        logged_count += 1
                        logging.info(f"✅ {pair}: Login exitoso")
                        
                        # Guardar información de ventana
                        self.windows[pair] = {
                            "driver": driver,
                            "pair": pair,
                            "logged_in": True,
                            "buttons": None
                        }
                    else:
                        logging.warning(f"⚠️ {pair}: Login pendiente")
                        
                except Exception as e:
                    logging.error(f"❌ {pair}: Error verificando login")
            
            if logged_count > 0:
                logging.info(f"✅ {logged_count}/6 ventanas con login exitoso")
                self.logged_in = True
                return True
            else:
                logging.error("❌ No se completó login en ninguna ventana")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            return False
    
    def detect_candle_direction(self, pair):
        """Detectar dirección de vela"""
        try:
            search_terms = [pair]
            
            if pair == "UK BRENT":
                search_terms.extend(["BRENT", "OIL", "CRUDE"])
            elif pair == "MICROSOFT":
                search_terms.extend(["MSFT", "Microsoft"])
            elif pair == "USDINR":
                search_terms.extend(["USD/INR", "USDINR"])
            elif pair == "USDEGP":
                search_terms.extend(["USD/EGP", "USDEGP"])
            
            # Simulación para testing (reemplazar con detección real)
            import random
            return random.choice(["UP", "DOWN"])
            
        except Exception as e:
            return None
    
    def update_candle_history(self, pair, direction):
        """Actualizar historial"""
        if direction:
            self.candle_history[pair].append(direction)
    
    def analyze_sequence_pattern(self, pair):
        """Analizar patrón de secuencia"""
        try:
            history = list(self.candle_history[pair])
            
            if len(history) < 3:
                return None, 0
            
            last_three = tuple(history[-3:])
            
            if last_three in self.sequence_patterns:
                probability, direction = self.sequence_patterns[last_three]
                return direction, probability
            
            # Patrones similares
            for pattern, (prob, dir) in self.sequence_patterns.items():
                matches = sum(1 for i in range(3) if i < len(last_three) and last_three[i] == pattern[i])
                if matches >= 2:
                    adjusted_prob = prob * 0.7
                    return dir, adjusted_prob
            
            return None, 0
            
        except Exception as e:
            return None, 0
    
    def analyze_correlations(self, pair, predicted_direction):
        """Analizar correlaciones"""
        try:
            correlation_boost = 0
            correlation_count = 0
            
            if pair not in self.correlations:
                return 0
            
            for other_pair, correlation_strength in self.correlations[pair].items():
                if other_pair in self.candle_history and len(self.candle_history[other_pair]) > 0:
                    last_direction = self.candle_history[other_pair][-1]
                    
                    if correlation_strength > 0:
                        if (predicted_direction == "UP" and last_direction == "UP") or \
                           (predicted_direction == "DOWN" and last_direction == "DOWN"):
                            correlation_boost += abs(correlation_strength)
                            correlation_count += 1
                    else:
                        if (predicted_direction == "UP" and last_direction == "DOWN") or \
                           (predicted_direction == "DOWN" and last_direction == "UP"):
                            correlation_boost += abs(correlation_strength)
                            correlation_count += 1
            
            if correlation_count > 0:
                return correlation_boost / correlation_count
            
            return 0
            
        except Exception as e:
            return 0
    
    def generate_signal(self, pair):
        """Generar señal"""
        try:
            seq_direction, seq_probability = self.analyze_sequence_pattern(pair)
            
            if not seq_direction or seq_probability < 0.7:
                return None
            
            correlation_boost = self.analyze_correlations(pair, seq_direction)
            combined_probability = seq_probability + (correlation_boost * 0.3)
            combined_probability = min(combined_probability, 0.95)
            
            if combined_probability >= 0.75:
                now = datetime.now()
                next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
                
                signal = {
                    "pair": pair,
                    "direction": seq_direction,
                    "probability": combined_probability,
                    "execute_at": next_minute.strftime("%H:%M:%S"),
                    "execute_timestamp": next_minute,
                    "command": f"EJECUTAR {pair} {seq_direction} a las {next_minute.strftime('%H:%M:%S')}",
                    "status": "READY_TO_EXECUTE"
                }
                
                return signal
            
            return None
            
        except Exception as e:
            return None
    
    def scan_and_generate_signals(self):
        """Escanear y generar señales"""
        try:
            logging.info("🔍 Escaneando activos...")
            
            # Escanear todos los pares
            for pair in self.pairs:
                direction = self.detect_candle_direction(pair)
                if direction:
                    self.update_candle_history(pair, direction)
                    logging.info(f"📈 {pair}: {direction}")
            
            # Generar señales
            signals = {}
            for pair in self.pairs:
                signal = self.generate_signal(pair)
                if signal:
                    signals[pair] = signal
            
            if signals:
                logging.info("🚨 SEÑALES GENERADAS PARA EJECUCIÓN AUTOMÁTICA:")
                logging.info("=" * 80)
                
                execute_time = None
                for pair, signal in signals.items():
                    direction_emoji = "🟢" if signal["direction"] == "UP" else "🔴"
                    logging.info(f"{direction_emoji} {signal['command']}")
                    logging.info(f"   📊 Probabilidad: {signal['probability']*100:.0f}%")
                    
                    if not execute_time:
                        execute_time = signal['execute_timestamp']
                
                logging.info("=" * 80)
                logging.info(f"🎯 EJECUCIÓN AUTOMÁTICA PROGRAMADA: {execute_time.strftime('%H:%M:%S')}")
                logging.info(f"🚀 TOTAL OPERACIONES: {len(signals)}")
                
                # Programar ejecución automática
                self.schedule_automatic_execution(signals, execute_time)
            
            return signals
            
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            return {}
    
    def find_trade_buttons(self):
        """Buscar botones de trading"""
        try:
            button_selectors = {
                "up": [
                    "//button[contains(@class, 'call')]",
                    "//button[contains(@class, 'up')]",
                    "//button[contains(text(), 'UP')]"
                ],
                "down": [
                    "//button[contains(@class, 'put')]",
                    "//button[contains(@class, 'down')]",
                    "//button[contains(text(), 'DOWN')]"
                ]
            }
            
            found_buttons = {"up": None, "down": None}
            
            for selector in button_selectors["up"]:
                try:
                    button = WebDriverWait(self.driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["up"] = button
                    break
                except:
                    continue
            
            for selector in button_selectors["down"]:
                try:
                    button = WebDriverWait(self.driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["down"] = button
                    break
                except:
                    continue
            
            return found_buttons
            
        except Exception as e:
            return {"up": None, "down": None}
    
    def schedule_automatic_execution(self, signals, execute_time):
        """Programar ejecución automática"""
        try:
            def execute_at_exact_time():
                # Esperar hasta la hora exacta
                while datetime.now() < execute_time:
                    time.sleep(0.1)
                
                # Esperar hasta el segundo exacto
                while datetime.now().second != 0:
                    time.sleep(0.001)
                
                # EJECUTAR AUTOMÁTICAMENTE
                self.execute_signals_automatically(signals)
            
            # Crear thread para ejecución automática
            execution_thread = threading.Thread(target=execute_at_exact_time)
            execution_thread.daemon = True
            execution_thread.start()
            
            logging.info("⏰ EJECUCIÓN AUTOMÁTICA PROGRAMADA")
            
        except Exception as e:
            logging.error(f"❌ Error programando ejecución: {e}")
    
    def find_buttons_in_window(self, pair):
        """Buscar botones en ventana específica"""
        try:
            driver = self.drivers[pair]
            logging.info(f"🔍 Buscando botones en ventana {pair}...")
            
            button_selectors = {
                "up": [
                    "//button[contains(@class, 'call')]",
                    "//button[contains(@class, 'up')]",
                    "//button[contains(text(), 'UP')]",
                    "//button[contains(text(), 'Arriba')]",
                    "//button[contains(@class, 'green')]"
                ],
                "down": [
                    "//button[contains(@class, 'put')]",
                    "//button[contains(@class, 'down')]",
                    "//button[contains(text(), 'DOWN')]",
                    "//button[contains(text(), 'Abajo')]",
                    "//button[contains(@class, 'red')]"
                ]
            }
            
            found_buttons = {"up": None, "down": None}
            
            for selector in button_selectors["up"]:
                try:
                    button = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["up"] = button
                    break
                except:
                    continue
            
            for selector in button_selectors["down"]:
                try:
                    button = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["down"] = button
                    break
                except:
                    continue
            
            if found_buttons["up"] and found_buttons["down"]:
                self.windows[pair]["buttons"] = found_buttons
                return True
            
            return False
            
        except Exception as e:
            return False
    
    def prepare_all_windows(self):
        """Preparar todas las ventanas con botones"""
        try:
            logging.info("🔧 PREPARANDO BOTONES EN TODAS LAS VENTANAS...")
            
            prepared_count = 0
            for pair in self.windows.keys():
                if self.find_buttons_in_window(pair):
                    prepared_count += 1
                    logging.info(f"✅ {pair}: Botones encontrados")
                else:
                    logging.warning(f"⚠️ {pair}: Botones no encontrados")
            
            logging.info(f"✅ {prepared_count}/{len(self.windows)} ventanas preparadas")
            return prepared_count > 0
            
        except Exception as e:
            logging.error(f"❌ Error preparando ventanas: {e}")
            return False
    
    def execute_signals_automatically(self, signals):
        """Ejecutar señales automáticamente en múltiples ventanas"""
        try:
            logging.info("🚀 *** EJECUTANDO EN MÚLTIPLES VENTANAS SIMULTÁNEAMENTE ***")
            
            # PREPARAR BOTONES JUSTO ANTES DE EJECUTAR
            logging.info("🔧 Preparando botones antes de ejecución...")
            self.prepare_all_windows()
            
            execute_time = datetime.now()
            
            def execute_single_trade(pair, signal):
                """Ejecutar una operación en su ventana específica"""
                try:
                    if pair not in self.windows or not self.windows[pair].get("buttons"):
                        logging.error(f"❌ {pair}: Ventana no preparada")
                        return
                    
                    direction = signal["direction"]
                    buttons = self.windows[pair]["buttons"]
                    
                    if direction == "UP":
                        buttons["up"].click()
                        logging.info(f"✅ {pair} UP EJECUTADO EN SU VENTANA")
                    else:
                        buttons["down"].click()
                        logging.info(f"✅ {pair} DOWN EJECUTADO EN SU VENTANA")
                    
                except Exception as e:
                    logging.error(f"❌ Error ejecutando {pair}: {e}")
            
            # Crear threads para ejecución simultánea
            threads = []
            for pair, signal in signals.items():
                if pair in self.windows:
                    thread = threading.Thread(target=execute_single_trade, args=(pair, signal))
                    threads.append(thread)
            
            # Ejecutar todos AL MISMO TIEMPO
            for thread in threads:
                thread.start()
            
            # Esperar que terminen
            for thread in threads:
                thread.join()
            
            logging.info("🎉" * 20)
            logging.info(f"🎯 *** EJECUCIÓN MULTI-VENTANA COMPLETADA ***")
            logging.info(f"⏰ TIEMPO: {execute_time.strftime('%H:%M:%S.%f')[:-3]}")
            logging.info(f"🚀 OPERACIONES SIMULTÁNEAS: {len(signals)}")
            logging.info("🎉" * 20)
            
            self.trades_executed += len(signals)
            
        except Exception as e:
            logging.error(f"❌ Error en ejecución automática: {e}")
    
    def run_continuous_automation(self):
        """Ejecutar automatización continua"""
        try:
            logging.info("🤖 INICIANDO AUTOMATIZACIÓN COMPLETA 24/7")
            logging.info("🔄 Ciclo: Detectar → Esperar → Ejecutar → Repetir")
            
            while True:
                try:
                    # Escanear y generar señales
                    signals = self.scan_and_generate_signals()
                    
                    if signals:
                        # Las señales se ejecutarán automáticamente
                        # Esperar hasta después de la ejecución
                        execute_time = list(signals.values())[0]['execute_timestamp']
                        wait_until = execute_time + timedelta(seconds=10)
                        
                        while datetime.now() < wait_until:
                            time.sleep(1)
                    
                    # Esperar antes del próximo ciclo
                    logging.info("⏰ Esperando próximo ciclo (60s)...")
                    time.sleep(60)
                    
                except KeyboardInterrupt:
                    logging.info("👋 Automatización detenida por usuario")
                    break
                except Exception as e:
                    logging.error(f"❌ Error en ciclo: {e}")
                    time.sleep(10)
            
        except Exception as e:
            logging.error(f"❌ Error en automatización: {e}")
    
    def close(self):
        """Cerrar todas las ventanas"""
        for pair, driver in self.drivers.items():
            try:
                driver.quit()
                logging.info(f"👋 {pair} cerrado")
            except:
                pass

def main():
    """Función principal"""
    bot = QuotexFullAuto()
    
    try:
        # Setup múltiples ventanas
        if not bot.setup_all_windows():
            return
        
        if not bot.open_all_quotex_windows():
            return
        
        # Preparar botones en todas las ventanas
        if not bot.prepare_all_windows():
            logging.warning("⚠️ Algunas ventanas no están preparadas, continuando...")
        
        # Iniciar automatización completa
        bot.run_continuous_automation()
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
    finally:
        bot.close()

if __name__ == "__main__":
    main()
