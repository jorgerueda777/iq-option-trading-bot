#!/usr/bin/env python3
"""
Quotex Pure API - Sin Chrome
Login directo con credenciales como IQ Option main.js
"""

import sys
import json
import time
import logging
import requests
import websocket
import threading
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexPureAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.ws = None
        self.is_connected = False
        self.ssid = None
        self.prices = {}
        self.base_url = "https://qxbroker.com"
        
        # Headers realistas como IQ Option
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.125 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Content-Type': 'application/json'
        })
    
    def get_initial_cookies(self):
        """Obtener cookies iniciales como IQ Option"""
        try:
            logging.info("🍪 Obteniendo cookies iniciales...")
            
            response = self.session.get(self.base_url, timeout=15)
            
            if response.status_code == 200:
                logging.info("✅ Cookies iniciales obtenidas")
                return True
            else:
                logging.error(f"❌ Error obteniendo cookies: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error obteniendo cookies: {e}")
            return False
    
    def login(self):
        """Login directo con credenciales EXACTAMENTE como IQ Option"""
        try:
            logging.info("🔐 Iniciando sesión con credenciales reales...")
            
            # Datos de login EXACTOS como IQ Option
            login_data = {
                "email": self.email,
                "password": self.password,
                "platform": "web"
            }
            
            # Headers EXACTOS como IQ Option
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/es/sign-in/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Obtener cookies existentes
            cookies = '; '.join([f'{c.name}={c.value}' for c in self.session.cookies])
            if cookies:
                headers['Cookie'] = cookies
            
            try:
                logging.info("🔍 Probando login en /api/login")
                
                response = self.session.post(
                    f"{self.base_url}/api/login",
                    json=login_data,
                    headers=headers,
                    timeout=15,
                    allow_redirects=True
                )
                
                logging.info(f"📡 Respuesta login - Status: {response.status_code}")
                
                # Procesar respuesta EXACTAMENTE como IQ Option
                if response.status_code == 200 and response.text:
                    try:
                        data = response.json()
                        logging.info(f"📄 Datos recibidos: {str(data)[:200]}...")
                        
                        # Verificar diferentes formatos como IQ Option
                        if data.get('isSuccessful') == True:
                            self.ssid = data.get('ssid')
                            logging.info('✅ Login exitoso - SSID obtenido')
                            return True
                        elif data.get('result') == True:
                            self.ssid = data.get('ssid') or data.get('session_id')
                            logging.info('✅ Login exitoso - Sesión iniciada')
                            return True
                        elif data.get('success') == True:
                            self.ssid = data.get('token') or data.get('session_token')
                            logging.info('✅ Login exitoso - Token obtenido')
                            return True
                        else:
                            # Intentar extraer cualquier token/ssid como IQ Option
                            response_str = json.dumps(data)
                            import re
                            ssid_match = re.search(r'"(?:ssid|session_id|token|session_token)":"([^"]+)"', response_str)
                            
                            if ssid_match:
                                self.ssid = ssid_match.group(1)
                                logging.info('✅ Login exitoso - ID de sesión extraído')
                                return True
                            else:
                                logging.info(f"❌ Respuesta de login: {data}")
                                
                                # Si hay datos pero no tokens, puede ser exitoso
                                if 'user' in data or 'profile' in data or 'account' in data:
                                    logging.info('✅ Login exitoso - Datos de usuario detectados')
                                    return True
                                    
                    except json.JSONDecodeError:
                        # Respuesta no JSON
                        if "dashboard" in response.text or "trading" in response.text or "trade" in response.text:
                            logging.info("✅ Login exitoso (HTML response)")
                            return True
                        else:
                            logging.info(f"❌ Respuesta no JSON: {response.text[:200]}...")
                
                elif response.status_code == 302:
                    # Redirección
                    location = response.headers.get('Location', '')
                    if "dashboard" in location or "trade" in location:
                        logging.info("✅ Login exitoso (redirect)")
                        return True
                        
                elif response.status_code == 403:
                    logging.info("🛡️ Cloudflare detectado - esto es normal")
                    # Intentar con diferentes endpoints
                    
                else:
                    logging.info(f"❌ Login falló - HTTP {response.status_code}")
                    
            except Exception as e:
                logging.info(f"❌ Error en login: {str(e)[:100]}")
            
            # Intentar endpoints alternativos
            alt_endpoints = ["/login", "/auth/login", "/api/v1/login", "/api/auth/login"]
            
            for endpoint in alt_endpoints:
                try:
                    logging.info(f"🔍 Probando endpoint alternativo: {endpoint}")
                    
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=login_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        logging.info(f"✅ Respuesta exitosa en {endpoint}")
                        return True
                        
                except:
                    continue
            
            logging.error("❌ Login falló en todos los endpoints")
            return False
            
        except Exception as e:
            logging.error(f"❌ Error en login: {e}")
            return False
    
    def connect_websocket(self):
        """Conectar WebSocket para precios reales"""
        try:
            logging.info("🌐 Conectando WebSocket...")
            
            # URLs de WebSocket posibles
            ws_urls = [
                "wss://qxbroker.com/websocket",
                "wss://qxbroker.com/ws",
                "wss://api.qxbroker.com/websocket",
                "wss://ws.qxbroker.com/",
                "wss://socket.qxbroker.com/"
            ]
            
            for ws_url in ws_urls:
                try:
                    logging.info(f"🔌 Probando WebSocket: {ws_url}")
                    
                    # Headers para WebSocket
                    headers = {
                        'User-Agent': self.session.headers['User-Agent'],
                        'Origin': self.base_url
                    }
                    
                    if self.ssid:
                        headers['Authorization'] = f'Bearer {self.ssid}'
                    
                    def on_message(ws, message):
                        try:
                            data = json.loads(message)
                            self.process_websocket_data(data)
                        except:
                            logging.info(f"📄 WS mensaje: {message[:100]}...")
                    
                    def on_error(ws, error):
                        logging.info(f"❌ WS error: {error}")
                    
                    def on_close(ws, close_status_code, close_msg):
                        logging.info(f"🔌 WebSocket cerrado")
                        self.is_connected = False
                    
                    def on_open(ws):
                        logging.info(f"✅ WebSocket conectado: {ws_url}")
                        self.is_connected = True
                        
                        # Suscribirse a precios
                        subscribe_messages = [
                            '{"action":"subscribe","data":{"asset":"BRENT_otc"}}',
                            '{"type":"subscribe","asset":"BRENT_otc"}',
                            '{"cmd":"subscribe","symbol":"BRENT_otc"}',
                            '{"subscribe":"prices"}',
                            '{"action":"get_prices"}'
                        ]
                        
                        for msg in subscribe_messages:
                            try:
                                ws.send(msg)
                                time.sleep(0.5)
                            except:
                                pass
                    
                    self.ws = websocket.WebSocketApp(
                        ws_url,
                        header=headers,
                        on_open=on_open,
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close
                    )
                    
                    # Ejecutar en thread separado
                    ws_thread = threading.Thread(target=self.ws.run_forever)
                    ws_thread.daemon = True
                    ws_thread.start()
                    
                    # Esperar conexión
                    time.sleep(3)
                    
                    if self.is_connected:
                        logging.info("✅ WebSocket conectado exitosamente")
                        return True
                    
                except Exception as e:
                    logging.info(f"❌ Error WebSocket: {str(e)[:50]}")
                    continue
            
            logging.warning("⚠️ No se pudo conectar WebSocket")
            return False
            
        except Exception as e:
            logging.error(f"❌ Error conectando WebSocket: {e}")
            return False
    
    def process_websocket_data(self, data):
        """Procesar datos del WebSocket"""
        try:
            # Buscar precios en los datos
            if isinstance(data, dict):
                # Buscar diferentes formatos de precios
                price_keys = ['price', 'rate', 'quote', 'value', 'last', 'bid', 'ask']
                
                for key in price_keys:
                    if key in data:
                        price = data[key]
                        if isinstance(price, (int, float)) and 0.01 < price < 100000:
                            asset = data.get('asset', data.get('symbol', 'UNKNOWN'))
                            self.prices[asset] = {
                                'price': price,
                                'timestamp': time.time(),
                                'source': 'websocket'
                            }
                            logging.info(f"💰 Precio WebSocket: {asset} = {price}")
                            
        except Exception as e:
            logging.error(f"❌ Error procesando WebSocket: {e}")
    
    def get_prices_api(self):
        """Obtener precios via API REST"""
        try:
            logging.info("📊 Obteniendo precios via API...")
            
            # Endpoints de precios posibles
            price_endpoints = [
                "/api/prices",
                "/api/v1/prices",
                "/api/quotes",
                "/api/v1/quotes",
                "/api/market/data",
                "/api/v1/market/data",
                "/api/assets/prices"
            ]
            
            for endpoint in price_endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            # Procesar precios
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    if isinstance(value, (int, float)) and 0.01 < value < 100000:
                                        self.prices[key] = {
                                            'price': value,
                                            'timestamp': time.time(),
                                            'source': 'api'
                                        }
                                        logging.info(f"💰 Precio API: {key} = {value}")
                            
                            elif isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict):
                                        asset = item.get('asset', item.get('symbol', 'UNKNOWN'))
                                        price = item.get('price', item.get('rate', item.get('value')))
                                        
                                        if price and isinstance(price, (int, float)) and 0.01 < price < 100000:
                                            self.prices[asset] = {
                                                'price': price,
                                                'timestamp': time.time(),
                                                'source': 'api'
                                            }
                                            logging.info(f"💰 Precio API: {asset} = {price}")
                            
                            if self.prices:
                                return True
                                
                        except:
                            continue
                            
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo precios API: {e}")
            return False
    
    def execute_trade_api(self, asset, amount, direction):
        """Ejecutar operación via API"""
        try:
            logging.info(f"🎯 Ejecutando operación API: {asset} {direction} ${amount}")
            
            # Endpoints de trading posibles
            trade_endpoints = [
                "/api/trade",
                "/api/v1/trade",
                "/api/buy",
                "/api/v1/buy",
                "/api/options/buy"
            ]
            
            # Datos de operación
            trade_data = {
                "asset": asset,
                "amount": amount,
                "direction": direction.upper(),
                "duration": 60,
                "type": "binary"
            }
            
            for endpoint in trade_endpoints:
                try:
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=trade_data,
                        timeout=10
                    )
                    
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
        """Conectar API completa como IQ Option"""
        try:
            logging.info("🚀 Conectando a Quotex API PURA...")
            
            # Paso 1: Obtener cookies iniciales
            if not self.get_initial_cookies():
                return False
            
            # Paso 2: Login con credenciales
            if not self.login():
                return False
            
            # Paso 3: Conectar WebSocket (opcional)
            self.connect_websocket()
            
            # Paso 4: Obtener precios iniciales
            self.get_prices_api()
            
            logging.info("✅ Conectado exitosamente a Quotex API PURA")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error conectando: {e}")
            return False
    
    def get_current_prices(self):
        """Obtener precios actuales"""
        # Actualizar precios
        self.get_prices_api()
        return self.prices
    
    def close(self):
        """Cerrar conexiones"""
        if self.ws:
            self.ws.close()
        self.is_connected = False

def main():
    """Función principal como IQ Option"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Comando requerido"}))
        return
    
    command = sys.argv[1]
    
    # Credenciales
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    api = QuotexPureAPI(email, password)
    
    try:
        if command == "connect":
            success = api.connect()
            
            if success:
                result = {"success": True, "message": "Conectado a Quotex API"}
                print(json.dumps(result))
                
                logging.info("🎉 ¡API conectada exitosamente!")
                logging.info("💰 Obteniendo precios...")
                
                # Mostrar precios por 30 segundos
                for i in range(30):
                    prices = api.get_current_prices()
                    if prices:
                        for asset, data in prices.items():
                            logging.info(f"💵 {asset}: {data['price']} ({data['source']})")
                    time.sleep(1)
                    
            else:
                result = {"success": False, "message": "Error conectando API"}
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
    finally:
        api.close()

if __name__ == "__main__":
    main()
