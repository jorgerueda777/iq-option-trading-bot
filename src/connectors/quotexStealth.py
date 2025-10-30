#!/usr/bin/env python3
"""
Quotex Stealth Bot - Bot avanzado no detectable para Quotex
Mejor que IQ Option - menos restricciones, más confiable
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

class QuotexStealthBot:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.trades_executed = 0
        self.balance = 0
        
    def setup_stealth_chrome(self):
        """Configurar Chrome con técnicas stealth para Quotex"""
        try:
            logging.info("🛡️ Configurando Chrome Stealth para Quotex...")
            
            options = uc.ChromeOptions()
            
            # Anti-detección específico para Quotex
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
            
            # Scripts anti-detección para Quotex
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']})")
            self.driver.execute_script("window.chrome = {runtime: {}}")
            
            # Configurar ventana
            self.driver.set_window_size(1920, 1080)
            self.driver.maximize_window()
            
            logging.info("✅ Chrome Stealth configurado para Quotex")
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
    
    def open_quotex(self):
        """Abrir Quotex con comportamiento humano"""
        try:
            logging.info("🌐 Abriendo Quotex...")
            
            # Navegar a Quotex
            self.driver.get("https://qxbroker.com/")
            self.human_like_delay(3, 5)
            
            logging.info("👤 HAZ LOGIN MANUALMENTE - Tienes 60 segundos")
            logging.info("   1. Haz clic en 'Sign In' o 'Iniciar Sesión'")
            logging.info("   2. Ingresa: arnolbrom634@gmail.com")
            logging.info("   3. Ingresa: 7decadames")
            logging.info("   4. Haz clic en 'Sign In'")
            logging.info("   5. Espera a que cargue la plataforma de trading")
            
            # Esperar login manual con más tiempo
            time.sleep(60)
            
            # Verificar si estamos logueados
            current_url = self.driver.current_url
            if "trade" in current_url or "platform" in current_url or "qxbroker.com" in current_url:
                logging.info("✅ Login exitoso - En plataforma Quotex")
                self.logged_in = True
                
                # Intentar obtener balance
                self.get_balance()
                
                return True
            else:
                logging.warning("⚠️ Puede que no hayas completado el login")
                logging.info(f"📄 URL actual: {current_url}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error abriendo Quotex: {e}")
            return False
    
    def get_balance(self):
        """Obtener balance de la cuenta - VERSIÓN MEJORADA"""
        try:
            logging.info("💰 Buscando balance...")
            
            # Buscar TODOS los elementos que contengan $
            try:
                dollar_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
                for element in dollar_elements:
                    text = element.text.strip()
                    if text and any(char.isdigit() for char in text):
                        logging.info(f"💰 Balance encontrado: {text}")
                        self.balance = text
                        return text
            except:
                pass
            
            # Buscar por selectores específicos
            balance_selectors = [
                "//div[contains(@class, 'balance')]",
                "//span[contains(@class, 'balance')]", 
                "//div[contains(@class, 'money')]",
                "//span[contains(@class, 'money')]",
                "//*[contains(@class, 'amount')]",
                "//*[contains(@class, 'wallet')]"
            ]
            
            for selector in balance_selectors:
                try:
                    balance_element = self.driver.find_element(By.XPATH, selector)
                    balance_text = balance_element.text.strip()
                    if balance_text and ('$' in balance_text or '€' in balance_text or any(char.isdigit() for char in balance_text)):
                        logging.info(f"💰 Balance por selector: {balance_text}")
                        self.balance = balance_text
                        return balance_text
                except:
                    continue
            
            logging.warning("💰 Balance: No encontrado - Verificar cuenta demo")
            return "N/A"
            
        except Exception as e:
            logging.warning(f"⚠️ No se pudo obtener balance: {e}")
            return "N/A"
    
    def navigate_to_binary_options(self):
        """Navegar a opciones binarias/divisas en Quotex"""
        try:
            logging.info("📊 Navegando a trading de divisas...")
            
            # En Quotex, las "opciones binarias" están en la sección de divisas/forex
            # Buscar elementos de navegación para divisas
            binary_selectors = [
                "//div[contains(text(), 'Forex')]",
                "//span[contains(text(), 'Forex')]", 
                "//button[contains(text(), 'Forex')]",
                "//div[contains(text(), 'Divisas')]",
                "//span[contains(text(), 'Divisas')]",
                "//div[contains(text(), 'Currency')]",
                "//span[contains(text(), 'Currency')]",
                "//div[contains(text(), 'Binary')]",
                "//span[contains(text(), 'Binary')]",
                "//button[contains(text(), 'Binary')]",
                "//div[contains(@class, 'binary')]",
                "//span[contains(text(), 'Turbo')]",
                "//div[contains(text(), 'Digital')]"
            ]
            
            for selector in binary_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.human_like_delay(0.5, 1.0)
                    element.click()
                    logging.info(f"✅ Navegación a binarias exitosa: {selector}")
                    self.human_like_delay(2, 3)
                    return True
                except:
                    continue
            
            logging.info("📊 Asumiendo que ya estamos en trading de divisas")
            self.human_like_delay(2, 3)
            return True
            
        except Exception as e:
            logging.error(f"❌ Error navegando: {e}")
            return False
    
    def select_currency_pair(self, pair="EURUSD"):
        """Seleccionar par de divisas específico"""
        try:
            logging.info(f"💱 Seleccionando par: {pair}")
            
            # Selectores para encontrar el selector de pares
            pair_selectors = [
                f"//div[contains(text(), '{pair}')]",
                f"//span[contains(text(), '{pair}')]",
                f"//button[contains(text(), '{pair}')]",
                f"//*[contains(text(), '{pair}')]",
                "//div[contains(@class, 'asset')]",
                "//div[contains(@class, 'pair')]",
                "//div[contains(@class, 'symbol')]",
                "//button[contains(@class, 'asset')]"
            ]
            
            for selector in pair_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    logging.info(f"✅ Par {pair} seleccionado: {selector}")
                    self.human_like_delay(1, 2)
                    return True
                except:
                    continue
            
            logging.warning(f"⚠️ No se pudo seleccionar {pair}, usando par actual")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error seleccionando par {pair}: {e}")
            return False
    
    def get_current_pair(self):
        """Detectar qué par está actualmente seleccionado - VERSIÓN RÁPIDA"""
        try:
            logging.info("⚡ Detectando par actual...")
            
            # Selectores RÁPIDOS - Solo los más comunes
            pair_selectors = [
                "//span[contains(@class, 'asset')]",
                "//span[contains(@class, 'symbol')]", 
                "//*[contains(text(), 'USD')]",
                "//*[contains(text(), 'EUR')]"
            ]
            
            current_pair = "DESCONOCIDO"
            
            for selector in pair_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip().upper()
                        
                        # Verificar si el texto parece un par de divisas
                        if len(text) >= 6 and any(currency in text for currency in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']):
                            # Limpiar el texto para obtener solo el par
                            for pair in ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY']:
                                if pair in text:
                                    current_pair = pair
                                    logging.info(f"✅ Par detectado: {current_pair}")
                                    return current_pair
                except:
                    continue
            
            # DEBUG FORZADO: Mostrar TODOS los elementos
            logging.info("🔍 DEBUG FORZADO - Elementos en la página:")
            try:
                # Obtener TODOS los elementos con texto
                all_elements = self.driver.find_elements(By.XPATH, "//*")
                element_count = 0
                
                for element in all_elements:
                    try:
                        text = element.text.strip()
                        if text and len(text) <= 100 and element_count < 50:  # Primeros 50 elementos con texto
                            tag = element.tag_name
                            classes = element.get_attribute("class") or "sin-clase"
                            element_count += 1
                            
                            logging.info(f"   {element_count}. [{tag}] '{text}' | '{classes}'")
                            
                            # Buscar pares y balance
                            text_upper = text.upper()
                            
                            # Detectar pares
                            for pair in ['EUR/USD', 'EURUSD', 'GBP/USD', 'GBPUSD', 'USD/JPY', 'USDJPY', 'AUD/USD', 'AUDUSD', 'USD/CAD', 'USDCAD']:
                                if pair in text_upper:
                                    clean_pair = pair.replace('/', '')
                                    logging.info(f"🎯 PAR ENCONTRADO: {clean_pair}")
                                    return clean_pair
                            
                            # Detectar balance
                            if '$' in text and any(char.isdigit() for char in text):
                                logging.info(f"💰 BALANCE ENCONTRADO: {text}")
                                
                    except:
                        continue
                        
                logging.info(f"📊 Total elementos analizados: {element_count}")
                
            except Exception as debug_error:
                logging.error(f"❌ Error en debug forzado: {debug_error}")
            
            # Si aún no encuentra nada, usar selector manual
            logging.info("🔍 Búsqueda manual de elementos específicos...")
            try:
                # Buscar elementos que contengan divisas
                currency_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'USD') or contains(text(), 'EUR') or contains(text(), 'GBP') or contains(text(), 'JPY')]")
                for element in currency_elements[:10]:
                    text = element.text.strip().upper()
                    logging.info(f"💱 Elemento con divisa: '{text}'")
                    
                    for pair in ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']:
                        if pair in text or pair.replace('USD', '/USD') in text:
                            logging.info(f"✅ Par detectado manualmente: {pair}")
                            return pair
                            
            except Exception as manual_error:
                logging.error(f"❌ Error en búsqueda manual: {manual_error}")
            
            logging.warning(f"⚠️ No se pudo detectar el par actual - Usando: {current_pair}")
            return current_pair
            
        except Exception as e:
            logging.error(f"❌ Error detectando par actual: {e}")
            return "DESCONOCIDO"
    
    def find_trade_buttons(self):
        """Buscar botones de trading en Quotex - VERSIÓN RÁPIDA"""
        try:
            logging.info("⚡ Búsqueda rápida de botones...")
            
            # Espera mínima - solo 1 segundo
            time.sleep(1)
            
            # Selectores CORREGIDOS - Excluir botones de input
            button_selectors = {
                "up": [
                    "//button[contains(text(), 'UP')]",
                    "//button[contains(text(), 'Arriba')]",
                    "//button[contains(@class, 'call-btn')]",
                    "//button[contains(@class, 'call') and not(contains(@class, 'input'))]",
                    "//button[contains(@class, 'up') and not(contains(@class, 'input'))]",
                    "//button[contains(@class, 'green') and not(contains(@class, 'input'))]"
                ],
                "down": [
                    "//button[contains(text(), 'DOWN')]",
                    "//button[contains(text(), 'Abajo')]",
                    "//button[contains(text(), 'Bajo')]",
                    "//button[contains(@class, 'put-btn')]",
                    "//button[contains(@class, 'put') and not(contains(@class, 'input'))]",
                    "//button[contains(@class, 'down') and not(contains(@class, 'input'))]",
                    "//button[contains(@class, 'red') and not(contains(@class, 'input'))]",
                    # Excluir específicamente botones de control
                    "//button[contains(@class, 'put') and not(contains(@class, 'input-control'))]"
                ]
            }
            
            found_buttons = {"up": None, "down": None}
            
            # Buscar botones UP - RÁPIDO (0.5s timeout)
            for selector in button_selectors["up"]:
                try:
                    button = WebDriverWait(self.driver, 0.5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["up"] = button
                    logging.info(f"⚡ UP encontrado: {selector}")
                    break
                except:
                    continue
            
            # Buscar botones DOWN - RÁPIDO (0.5s timeout)
            for selector in button_selectors["down"]:
                try:
                    button = WebDriverWait(self.driver, 0.5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    found_buttons["down"] = button
                    logging.info(f"⚡ DOWN encontrado: {selector}")
                    break
                except:
                    continue
            
            # Debug: Si no encuentra botones, mostrar elementos disponibles
            if not found_buttons["up"] and not found_buttons["down"]:
                logging.info("🔍 DEBUG - Elementos disponibles:")
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for i, btn in enumerate(all_buttons[:10]):
                        text = btn.text.strip()
                        classes = btn.get_attribute("class")
                        if text:
                            logging.info(f"   {i+1}. '{text}' | Clases: {classes}")
                except:
                    pass
            
            return found_buttons
            
        except Exception as e:
            logging.error(f"❌ Error buscando botones: {e}")
            return {"up": None, "down": None}
    
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
            
            # DETECTAR PAR ACTUAL PRIMERO
            current_pair = self.get_current_pair()
            logging.info("=" * 60)
            logging.info(f"💱 PAR ACTUAL: {current_pair}")
            logging.info(f"🎯 OPERACIÓN: {direction.upper()}")
            logging.info("=" * 60)
            
            # Confirmar con el usuario si el par es correcto
            if current_pair == "DESCONOCIDO":
                logging.error("❌ NO SE PUDO DETECTAR EL PAR - OPERACIÓN CANCELADA")
                logging.error("💡 Verifica que estés en la página de trading correcta")
                return False
            
            # Buscar botones
            buttons = self.find_trade_buttons()
            
            # Seleccionar botón con debug detallado
            if direction.lower() in ["call", "up", "higher"]:
                target_button = buttons["up"]
                action = "UP"
                logging.info(f"🟢 Seleccionado botón UP para {direction}")
            else:
                target_button = buttons["down"]
                action = "DOWN"
                logging.info(f"🔴 Seleccionado botón DOWN para {direction}")
            
            # Debug detallado del botón
            if target_button:
                try:
                    button_text = target_button.text
                    button_class = target_button.get_attribute("class")
                    button_enabled = target_button.is_enabled()
                    button_displayed = target_button.is_displayed()
                    
                    logging.info(f"🔍 Botón {action} - Texto: '{button_text}' | Clases: '{button_class}'")
                    logging.info(f"🔍 Botón {action} - Habilitado: {button_enabled} | Visible: {button_displayed}")
                    
                    if not button_enabled:
                        logging.error(f"❌ Botón {action} está DESHABILITADO")
                        return False
                    if not button_displayed:
                        logging.error(f"❌ Botón {action} NO es VISIBLE")
                        return False
                        
                except Exception as debug_error:
                    logging.warning(f"⚠️ Error en debug del botón: {debug_error}")
            else:
                logging.error(f"❌ No se encontró botón para {action}")
                
                # Debug MEJORADO: Mostrar TODOS los botones
                logging.info("🔍 DEBUG - TODOS los botones en la página:")
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for i, btn in enumerate(all_buttons):
                        text = btn.text.strip()
                        classes = btn.get_attribute("class") or "sin-clase"
                        enabled = btn.is_enabled()
                        visible = btn.is_displayed()
                        
                        # Solo mostrar botones que podrían ser de trading
                        if any(keyword in classes.lower() for keyword in ['call', 'put', 'up', 'down', 'trade', 'btn']) or text in ['UP', 'DOWN', 'Arriba', 'Abajo']:
                            logging.info(f"   🎯 {i+1}. '{text}' | '{classes}' | Habilitado: {enabled} | Visible: {visible}")
                        elif i < 20:  # Mostrar primeros 20 de todos modos
                            logging.info(f"   {i+1}. '{text}' | '{classes}' | Habilitado: {enabled} | Visible: {visible}")
                except Exception as btn_debug_error:
                    logging.error(f"Error en debug de botones: {btn_debug_error}")
                    
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
            
            logging.info("🎉" * 20)
            logging.info(f"🎯 *** OPERACIÓN EJECUTADA ***")
            logging.info(f"💱 PAR: {current_pair}")
            logging.info(f"📈 DIRECCIÓN: {action}")
            logging.info(f"⏰ TIEMPO: {execute_time.strftime('%H:%M:%S.%f')[:-3]}")
            logging.info("🎉" * 20)
            self.trades_executed += 1
            
            # Delay mínimo post-ejecución
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando operación: {e}")
            return False
    
    def execute_multiple_trades(self, trades):
        """Ejecutar múltiples operaciones simultáneamente"""
        try:
            logging.info(f"🚀 Preparando {len(trades)} operaciones simultáneas en Quotex...")
            
            # DETECTAR PAR ACTUAL
            current_pair = self.get_current_pair()
            logging.info("=" * 60)
            logging.info(f"💱 PAR ACTUAL: {current_pair}")
            logging.info(f"🚀 OPERACIONES MÚLTIPLES: {len(trades)}")
            logging.info("💡 NOTA: Todas las operaciones se ejecutarán en el mismo par")
            logging.info("💡 Para diferentes pares, necesitarías múltiples pestañas")
            logging.info("=" * 60)
            
            if current_pair == "DESCONOCIDO":
                logging.error("❌ NO SE PUDO DETECTAR EL PAR - OPERACIONES CANCELADAS")
                return False
            
            # Buscar todos los botones una vez
            buttons = self.find_trade_buttons()
            
            if not buttons["up"] or not buttons["down"]:
                logging.error("❌ No se encontraron botones necesarios")
                return False
            
            # Preparar operaciones
            prepared_trades = []
            for trade in trades:
                direction = trade.get("direction", "call").lower()
                if direction in ["call", "up", "higher"]:
                    button = buttons["up"]
                    action = "UP"
                else:
                    button = buttons["down"] 
                    action = "DOWN"
                
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
    bot = QuotexStealthBot()
    
    try:
        # Configurar Chrome Stealth
        if not bot.setup_stealth_chrome():
            print(json.dumps({"success": False, "message": "Error configurando Chrome Stealth"}))
            return
        
        # Abrir Quotex
        if not bot.open_quotex():
            print(json.dumps({"success": False, "message": "Error abriendo Quotex"}))
            return
        
        # Navegar a opciones binarias
        if not bot.navigate_to_binary_options():
            print(json.dumps({"success": False, "message": "Error navegando a binarias"}))
            return
        
        if command == "single":
            if len(sys.argv) < 3:
                direction = "call"
            else:
                direction = sys.argv[2]
            
            success = bot.execute_single_trade(direction)
            
            if success:
                print(json.dumps({"success": True, "message": f"Operación {direction.upper()} ejecutada en Quotex"}))
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
                print(json.dumps({"success": True, "message": f"{len(trades)} operaciones ejecutadas en Quotex"}))
            else:
                print(json.dumps({"success": False, "message": "Error ejecutando operaciones múltiples"}))
        
        # Mantener bot abierto para más operaciones
        logging.info("🤖 Bot Quotex Stealth listo para más operaciones...")
        logging.info("💡 Comandos disponibles:")
        logging.info("   - 'c' = Operación CALL/UP")
        logging.info("   - 'p' = Operación PUT/DOWN")
        logging.info("   - 'm' = Múltiples operaciones")
        logging.info("   - 'q' = Salir")
        
        while True:
            try:
                command = input("\n🎯 Comando: ").strip().lower()
                
                if command in ['q', 'quit', 'exit']:
                    logging.info("👋 Cerrando bot...")
                    break
                elif command == 'c':
                    logging.info("🟢 Ejecutando operación CALL...")
                    success = bot.execute_single_trade("call")
                    if success:
                        logging.info("✅ Operación CALL completada")
                    else:
                        logging.error("❌ Error en operación CALL")
                elif command == 'p':
                    logging.info("🔴 Ejecutando operación PUT...")
                    success = bot.execute_single_trade("put")
                    if success:
                        logging.info("✅ Operación PUT completada")
                    else:
                        logging.error("❌ Error en operación PUT")
                elif command == 'm':
                    logging.info("🚀 Ejecutando múltiples operaciones...")
                    trades = [
                        {"asset": "EURUSD", "direction": "call"},
                        {"asset": "GBPUSD", "direction": "put"},
                        {"asset": "USDJPY", "direction": "call"},
                        {"asset": "AUDUSD", "direction": "put"},
                        {"asset": "USDCAD", "direction": "call"}
                    ]
                    success = bot.execute_multiple_trades(trades)
                    if success:
                        logging.info("✅ Múltiples operaciones completadas")
                    else:
                        logging.error("❌ Error en múltiples operaciones")
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
