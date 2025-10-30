#!/usr/bin/env python3
"""
Quotex Final API - Método Híbrido Optimizado
Chrome headless SOLO para obtener tokens, luego API pura para todo lo demás
"""

import sys
import json
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexFinalAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        self.session = requests.Session()
        self.tokens = {}
        self.cookies = {}
        self.prices = {}
        self.base_url = "https://qxbroker.com"
        self.logged_in = False
        
    def get_auth_tokens(self):
        """Usar Chrome headless SOLO para obtener tokens de autenticación"""
        try:
            logging.info("🔧 Obteniendo tokens de autenticación...")
            
            # Chrome mínimo y rápido
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--window-size=800,600")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Login rápido
            logging.info("🔐 Haciendo login para obtener tokens...")
            self.driver.get(f"{self.base_url}/es/sign-in/")
            time.sleep(2)
            
            # Llenar formulario
            try:
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
                )
                email_field.send_keys(self.email)
                
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.send_keys(self.password)
                
                # Submit
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                login_button.click()
                
                # Esperar login
                time.sleep(5)
                
                # Extraer cookies y tokens
                cookies = self.driver.get_cookies()
                for cookie in cookies:
                    self.cookies[cookie['name']] = cookie['value']
                
                # Extraer tokens del localStorage/sessionStorage
                tokens_script = """
                let tokens = {};
                try {
                    // localStorage
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        let value = localStorage.getItem(key);
                        if (key.includes('token') || key.includes('auth') || key.includes('session')) {
                            tokens[key] = value;
                        }
                    }
                    
                    // sessionStorage
                    for (let i = 0; i < sessionStorage.length; i++) {
                        let key = sessionStorage.key(i);
                        let value = sessionStorage.getItem(key);
                        if (key.includes('token') || key.includes('auth') || key.includes('session')) {
                            tokens[key] = value;
                        }
                    }
                    
                    return tokens;
                } catch (e) {
                    return {error: e.message};
                }
                """
                
                storage_tokens = self.driver.execute_script(tokens_script)
                if storage_tokens and not storage_tokens.get('error'):
                    self.tokens.update(storage_tokens)
                
                # Verificar si el login fue exitoso
                current_url = self.driver.current_url
                if "trade" in current_url or "dashboard" in current_url:
                    logging.info("✅ Tokens obtenidos exitosamente")
                    self.logged_in = True
                    
                    # Configurar session con cookies
                    for name, value in self.cookies.items():
                        self.session.cookies.set(name, value)
                    
                    # Configurar headers con tokens
                    if self.tokens:
                        for key, value in self.tokens.items():
                            if 'token' in key.lower():
                                self.session.headers.update({
                                    'Authorization': f'Bearer {value}',
                                    'X-Auth-Token': value
                                })
                                break
                    
                    return True
                else:
                    logging.error("❌ Login falló")
                    return False
                    
            except Exception as e:
                logging.error(f"❌ Error en login: {e}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error obteniendo tokens: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def get_prices_api(self):
        """Obtener precios usando API con tokens válidos"""
        try:
            logging.info("💰 Obteniendo precios via API autenticada...")
            
            # Headers con tokens
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/trade/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Endpoints de precios
            price_endpoints = [
                "/api/quotes",
                "/api/v1/quotes", 
                "/api/prices",
                "/api/v1/prices",
                "/api/market/data",
                "/api/assets/prices",
                "/trade/api/quotes"
            ]
            
            for endpoint in price_endpoints:
                try:
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                    
                    logging.info(f"📊 {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            # Procesar precios
                            prices_found = 0
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    if isinstance(value, (int, float)) and 0.01 < value < 100000:
                                        self.prices[key] = {
                                            'price': value,
                                            'timestamp': time.time(),
                                            'source': f'api_{endpoint}'
                                        }
                                        prices_found += 1
                                        
                            elif isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict):
                                        asset = item.get('asset', item.get('symbol', f'asset_{len(self.prices)}'))
                                        price = item.get('price', item.get('rate', item.get('value')))
                                        
                                        if price and isinstance(price, (int, float)) and 0.01 < price < 100000:
                                            self.prices[asset] = {
                                                'price': price,
                                                'timestamp': time.time(),
                                                'source': f'api_{endpoint}'
                                            }
                                            prices_found += 1
                            
                            if prices_found > 0:
                                logging.info(f"✅ {prices_found} precios encontrados en {endpoint}")
                                return True
                                
                        except json.JSONDecodeError:
                            continue
                            
                except Exception as e:
                    continue
            
            logging.warning("⚠️ No se encontraron precios en APIs")
            return False
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo precios: {e}")
            return False
    
    def execute_trade_api(self, asset, amount, direction):
        """Ejecutar operación usando API autenticada"""
        try:
            logging.info(f"🎯 Ejecutando operación: {asset} {direction} ${amount}")
            
            trade_data = {
                "asset": asset,
                "amount": amount,
                "direction": direction.upper(),
                "duration": 60,
                "type": "binary"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/trade/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            trade_endpoints = [
                "/api/trade",
                "/api/v1/trade",
                "/api/buy",
                "/trade/api/buy",
                "/api/options/buy"
            ]
            
            for endpoint in trade_endpoints:
                try:
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=trade_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    logging.info(f"🎯 {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if result.get('success') or result.get('status') == 'success':
                                logging.info("✅ Operación ejecutada exitosamente")
                                return {"success": True, "data": result}
                        except:
                            pass
                            
                except Exception as e:
                    continue
            
            logging.error("❌ No se pudo ejecutar operación")
            return {"success": False, "message": "No se pudo ejecutar operación"}
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando operación: {e}")
            return {"success": False, "message": str(e)}
    
    def connect(self):
        """Conectar usando método híbrido optimizado"""
        try:
            logging.info("🚀 Conectando con método híbrido optimizado...")
            
            # Paso 1: Obtener tokens con Chrome (rápido)
            if not self.get_auth_tokens():
                return False
            
            # Paso 2: Usar API pura con tokens válidos
            self.get_prices_api()
            
            logging.info("✅ Conectado exitosamente con método híbrido")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error conectando: {e}")
            return False
    
    def get_current_prices(self):
        """Obtener precios actuales"""
        self.get_prices_api()
        return self.prices

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Comando requerido"}))
        return
    
    command = sys.argv[1]
    
    # Credenciales
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    api = QuotexFinalAPI(email, password)
    
    try:
        if command == "connect":
            success = api.connect()
            
            if success:
                result = {"success": True, "message": "Conectado híbrido"}
                print(json.dumps(result))
                
                logging.info("🎉 ¡API híbrida conectada!")
                logging.info("💰 Mostrando precios por 30 segundos...")
                
                # Mostrar precios
                for i in range(30):
                    prices = api.get_current_prices()
                    if prices:
                        for asset, data in list(prices.items())[:5]:
                            logging.info(f"💵 {asset}: {data['price']} ({data['source']})")
                    time.sleep(1)
                    
            else:
                result = {"success": False, "message": "Error conectando híbrido"}
                print(json.dumps(result))
                
        elif command == "prices":
            if api.connect():
                prices = api.get_current_prices()
                result = {"success": True, "data": prices}
            else:
                result = {"success": False, "message": "Error conectando"}
            
            print(json.dumps(result))
            
        elif command == "buy":
            if len(sys.argv) < 5:
                print(json.dumps({"success": False, "message": "Parámetros insuficientes"}))
                return
            
            asset = sys.argv[2]
            amount = float(sys.argv[3])
            direction = sys.argv[4]
            
            if api.connect():
                result = api.execute_trade_api(asset, amount, direction)
            else:
                result = {"success": False, "message": "Error conectando"}
            
            print(json.dumps(result))
            
        else:
            print(json.dumps({"success": False, "message": "Comando no reconocido"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))

if __name__ == "__main__":
    main()
