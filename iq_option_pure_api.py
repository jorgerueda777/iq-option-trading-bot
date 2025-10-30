#!/usr/bin/env python3
"""
IQ Option Pure API - Sin Selenium
API directa usando requests y websocket como los bots reales
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

class IQOptionPureAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.ws = None
        self.is_connected = False
        self.ssid = None
        self.prices = {}
        self.base_url = "https://iqoption.com"
        self.auth_url = "https://auth.iqoption.com/api/v2/login"
        self.ws_url = "wss://ws.iqoption.com/echo/websocket"
        self.logged_in = False
        self.profile_received = False
        self.pending_trade = None
        
        # Headers realistas
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.125 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
    
    def get_initial_cookies(self):
        """Obtener cookies iniciales"""
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
        """Login EXACTAMENTE como el archivo main de IQ Option"""
        try:
            logging.info("🔐 Iniciando sesión con credenciales reales...")
            
            # Datos de login EXACTOS como main OTC
            login_data = {
                "identifier": self.email,
                "password": self.password,
                "remember": False,
                "affiliate_promocode": ""
            }
            
            # Obtener cookies como string (como main.js)
            cookies = '; '.join([f'{c.name}={c.value}' for c in self.session.cookies])
            
            # Headers EXACTOS como main OTC
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'https://iqoption.com',
                'Referer': 'https://iqoption.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Usar la URL de autenticación OFICIAL como el main
            logging.info(f"🔍 Usando URL oficial de auth: {self.auth_url}")
            response = self.session.post(
                self.auth_url,
                json=login_data,
                headers=headers,
                timeout=15,
                allow_redirects=True
            )
            
            logging.info(f"📡 Respuesta login - Status: {response.status_code}")
            
            # Procesar respuesta EXACTAMENTE como main.js
            if response.status_code == 200 and response.text:
                try:
                    data = response.json()
                    logging.info(f"📄 Datos recibidos: {str(data)[:200]}...")
                    
                    # Verificar diferentes formatos EXACTOS como main OTC
                    if data.get('isSuccessful') == True or data.get('code') == 'success':
                        logging.info('✅ Login exitoso - Obteniendo SSID')
                        
                        # Obtener SSID directamente de data (más confiable)
                        self.ssid = data.get('ssid') or data.get('session_id')
                        if self.ssid:
                            logging.info('✅ SSID obtenido de data')
                            self.logged_in = True
                            
                            if self.logged_in:
                                return True
                    else:
                        # Intentar extraer cualquier token/ssid EXACTO como main.js
                        response_str = json.dumps(data)
                        import re
                        ssid_match = re.search(r'"(?:ssid|session_id|token|session_token)":"([^"]+)"', response_str)
                        
                        if ssid_match:
                            self.ssid = ssid_match.group(1)
                            logging.info('✅ Login exitoso - ID de sesión extraído')
                            self.logged_in = True
                        else:
                            logging.error(f'❌ Respuesta de login: {data}')
                            raise Exception('Login falló: No se pudo obtener ID de sesión')
                    
                    # Actualizar cookies con la respuesta (como main.js)
                    if 'set-cookie' in response.headers:
                        for cookie in response.headers.get_list('set-cookie'):
                            # Parsear y agregar cookies
                            pass
                    
                    if self.logged_in:
                        return True
                        
                except json.JSONDecodeError as e:
                    logging.error(f"❌ Error parseando JSON: {e}")
                    raise Exception(f'Login falló: Error parseando respuesta')
                    
            else:
                raise Exception(f'Login falló - HTTP {response.status_code}: {response.reason}')
                
        except Exception as e:
            logging.error(f'❌ Error en login: {e}')
            
            # Mostrar datos de respuesta si están disponibles (como main.js)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    logging.error(f'📄 Datos de respuesta: {error_data}')
                except:
                    pass
            
            raise Exception(f'Login falló: {e}')
            
        return False
    
    def connect_websocket(self):
        """Conectar WebSocket para precios reales"""
        try:
            logging.info("🌐 Conectando WebSocket...")
            
            ws_url = self.ws_url  # Usar la URL oficial del main
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    
                    # Buscar respuestas importantes
                    if isinstance(data, dict):
                        # CAPTURAR CUALQUIER respuesta de operación
                        if ('binary' in str(data).lower() or 
                            'option' in str(data).lower() or 
                            'trade' in str(data).lower() or
                            'open' in str(data).lower()):
                            logging.info(f"🎯 POSIBLE RESPUESTA OPERACIÓN: {data}")
                        # Respuestas de perfil
                        elif 'name' in data and data.get('name') == 'profile':
                            logging.info(f"👤 PERFIL RECIBIDO: {data}")
                            self.profile_received = True
                            
                            # EJECUTAR OPERACIÓN AUTOMÁTICAMENTE después del perfil
                            if self.pending_trade and not hasattr(self, 'trade_executed'):
                                self.trade_executed = True
                                logging.info("🎯 EJECUTANDO OPERACIÓN AUTOMÁTICA DESPUÉS DEL PERFIL...")
                                time.sleep(1)
                                
                                # Ejecutar la operación pendiente
                                asset, amount, direction = self.pending_trade
                                self._execute_trade_now(ws, asset, amount, direction)
                        # Mensajes con contenido
                        elif 'msg' in data and isinstance(data['msg'], dict):
                            msg = data['msg']
                            if 'name' in msg:
                                msg_name = msg.get('name', '')
                                if 'binary-options' in str(msg_name):
                                    logging.info(f"🎯 CONFIRMACIÓN OPERACIÓN: {msg}")
                                elif 'profile' in str(msg_name):
                                    logging.info(f"👤 DATOS PERFIL: {msg}")
                                elif msg_name in ['balance', 'user', 'account']:
                                    logging.info(f"💰 INFO CUENTA: {msg}")
                                elif 'change' in str(msg_name):
                                    logging.info(f"🔄 CAMBIO REALIZADO: {msg}")
                                elif 'demo' in str(msg_name):
                                    logging.info(f"🎮 RESPUESTA DEMO: {msg}")
                    
                    self.process_websocket_data(data)
                except:
                    logging.info(f"📄 WS mensaje: {message[:100]}...")
            
            def on_error(ws, error):
                logging.info(f"❌ WS error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                logging.info(f"🔌 WebSocket cerrado")
                self.is_connected = False
            
            def on_open(ws):
                logging.info(f"✅ WebSocket conectado")
                self.is_connected = True
                
                # AUTENTICAR con SSID como el main
                if self.ssid:
                    auth_message = {
                        "name": "ssid",
                        "msg": self.ssid
                    }
                    try:
                        ws.send(json.dumps(auth_message))
                        logging.info("🔑 Autenticación WebSocket enviada")
                        time.sleep(1)
                        
                        # Solicitar perfil como el main
                        profile_message = {
                            "name": "sendMessage",
                            "msg": {
                                "name": "get-profile",
                                "version": "1.0",
                                "body": {}
                            },
                            "request_id": int(time.time())
                        }
                        ws.send(json.dumps(profile_message))
                        logging.info("👤 Solicitando perfil...")
                        time.sleep(2)
                        
                        # Cambiar a cuenta DEMO explícitamente
                        demo_account_message = {
                            "name": "sendMessage",
                            "msg": {
                                "name": "change-account-type",
                                "version": "1.0",
                                "body": {
                                    "demo": 1  # Cambiar a DEMO
                                }
                            },
                            "request_id": int(time.time())
                        }
                        ws.send(json.dumps(demo_account_message))
                        logging.info("🎮 Cambiando a cuenta DEMO...")
                        time.sleep(2)
                        
                        # Cambiar a balance USD DEMO
                        demo_balance_message = {
                            "name": "sendMessage",
                            "msg": {
                                "name": "change-balance",
                                "version": "1.0",
                                "body": {
                                    "balance_id": 1227944349  # Balance USD DEMO
                                }
                            },
                            "request_id": int(time.time())
                        }
                        ws.send(json.dumps(demo_balance_message))
                        logging.info("💰 Cambiando a balance USD DEMO...")
                        time.sleep(2)
                        
                    except Exception as e:
                        logging.error(f"❌ Error enviando auth: {e}")
                
                # Suscribirse a precios después de autenticar
                subscribe_messages = [
                    '{"name":"subscribe","msg":{"name":"candle-generated","params":{"routingFilters":{"active_id":76,"size":60}}}}',
                    '{"name":"subscribe","msg":{"name":"quotes","params":{"routingFilters":{"active_id":76}}}}',
                ]
                
                for msg in subscribe_messages:
                    try:
                        ws.send(msg)
                        time.sleep(0.5)
                    except:
                        pass
            
            # Headers para WebSocket
            headers = {
                'User-Agent': self.session.headers['User-Agent'],
                'Origin': self.base_url
            }
            
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
            else:
                logging.warning("⚠️ WebSocket no conectado")
                return False
            
        except Exception as e:
            logging.error(f"❌ Error conectando WebSocket: {e}")
            return False
    
    def process_websocket_data(self, data):
        """Procesar datos del WebSocket"""
        try:
            if isinstance(data, dict):
                # Buscar precios en diferentes formatos
                if 'msg' in data and isinstance(data['msg'], dict):
                    msg = data['msg']
                    
                    # Precios de velas
                    if 'price' in msg:
                        price = msg['price']
                        if isinstance(price, (int, float)) and 0.01 < price < 100000:
                            asset = msg.get('active_id', 'UNKNOWN')
                            self.prices[f'ASSET_{asset}'] = {
                                'price': price,
                                'timestamp': time.time(),
                                'source': 'websocket'
                            }
                            logging.info(f"💰 Precio WebSocket: ASSET_{asset} = {price}")
                    
                    # Cotizaciones
                    if 'ask' in msg and 'bid' in msg:
                        ask = msg['ask']
                        bid = msg['bid']
                        asset = msg.get('active_id', 'UNKNOWN')
                        
                        if isinstance(ask, (int, float)) and 0.01 < ask < 100000:
                            self.prices[f'ASSET_{asset}_ASK'] = {
                                'price': ask,
                                'timestamp': time.time(),
                                'source': 'websocket_ask'
                            }
                            
                        if isinstance(bid, (int, float)) and 0.01 < bid < 100000:
                            self.prices[f'ASSET_{asset}_BID'] = {
                                'price': bid,
                                'timestamp': time.time(),
                                'source': 'websocket_bid'
                            }
                            
                        logging.info(f"💰 Cotización WebSocket: ASSET_{asset} ASK={ask} BID={bid}")
                            
        except Exception as e:
            logging.error(f"❌ Error procesando WebSocket: {e}")
    
    def _execute_trade_now(self, ws, asset, amount, direction, duration=60):
        """Ejecutar operación INMEDIATAMENTE por WebSocket"""
        try:
            logging.info(f"🎯 EJECUTANDO AHORA: {asset} {direction} ${amount}")
            
            # Mapear activos a IDs como el main
            otc_assets = {
                'EURUSD-OTC': 76,
                'GBPUSD-OTC': 77,
                'USDJPY-OTC': 78,
                'AUDUSD-OTC': 79
            }
            
            asset_id = otc_assets.get(asset, 76)  # Default EURUSD-OTC
            option_type = 'call' if direction.upper() == 'CALL' else 'put'
            
            # Mensaje EXACTO como el main
            message = {
                "name": "sendMessage",
                "msg": {
                    "name": "binary-options.open-option",
                    "version": "1.0",
                    "body": {
                        "user_balance_id": 1227944349,  # Balance USD REAL que tienes
                        "active_id": asset_id,
                        "option_type_id": 3,  # Turbo options (1 minuto como manual)
                        "direction": option_type,
                        "expired": ((int(time.time()) // 60) + 1) * 60,  # Próximo minuto exacto
                        "price": amount,
                        "value": amount,
                        "profit_income": 0.85,  # 85% payout
                        "time_rate": duration
                    }
                },
                "request_id": int(time.time())
            }
            
            # Enviar mensaje por WebSocket
            ws.send(json.dumps(message))
            logging.info("✅ OPERACIÓN EJECUTADA INMEDIATAMENTE")
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando inmediatamente: {e}")
    
    def execute_trade_websocket(self, asset, amount, direction, duration=60):
        """Ejecutar operación via WebSocket como el main"""
        try:
            logging.info(f"🎯 Programando operación: {asset} {direction} ${amount}")
            
            # Programar la operación para después del perfil
            self.pending_trade = (asset, amount, direction)
            logging.info("⏳ Operación programada para ejecutar después del perfil...")
            
            if not self.is_connected:
                logging.error("❌ WebSocket no conectado")
                return {"success": False, "message": "WebSocket no conectado"}
            
            # Mapear activos a IDs como el main
            otc_assets = {
                'EURUSD-OTC': 76,
                'GBPUSD-OTC': 77,
                'USDJPY-OTC': 78,
                'AUDUSD-OTC': 79,
                'USDCAD-OTC': 80,
                'EURJPY-OTC': 81,
                'GBPJPY-OTC': 82,
                'EURGBP-OTC': 83,
                'AUDJPY-OTC': 84,
                'NZDUSD-OTC': 85
            }
            
            asset_id = otc_assets.get(asset)
            if not asset_id:
                logging.error(f"❌ Asset {asset} no encontrado")
                return {"success": False, "message": f"Asset {asset} no encontrado"}
            
            # Convertir dirección como el main
            option_type = 'call' if direction.upper() == 'CALL' else 'put'
            
            # Mensaje EXACTO como el main
            message = {
                "name": "sendMessage",
                "msg": {
                    "name": "binary-options.open-option",
                    "version": "1.0",
                    "body": {
                        "user_balance_id": 1227944349,  # Balance USD REAL que tienes
                        "active_id": asset_id,
                        "option_type_id": 3,  # Turbo options (1 minuto como manual)
                        "direction": option_type,
                        "expired": ((int(time.time()) // 60) + 1) * 60,  # Próximo minuto exacto
                        "price": amount,
                        "value": amount,
                        "profit_income": 0.85,  # 85% payout
                        "time_rate": duration
                    }
                },
                "request_id": int(time.time())
            }
            
            # Enviar mensaje por WebSocket
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(json.dumps(message))
                logging.info("✅ Operación enviada por WebSocket")
                logging.info("⏳ Esperando confirmación del servidor...")
                
                # Esperar respuesta del servidor
                logging.info("⏳ Esperando respuesta de IQ Option...")
                time.sleep(15)  # Esperar MÁS tiempo para ver respuesta
                
                return {"success": True, "message": "Operación programada exitosamente"}
            else:
                logging.error("❌ WebSocket no disponible para envío")
                return {"success": False, "message": "WebSocket no disponible"}
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando operación: {e}")
            return {"success": False, "message": str(e)}
    
    def connect(self):
        """Conectar API completa"""
        try:
            logging.info("🚀 Conectando a IQ Option API PURA...")
            
            # Paso 1: Obtener cookies iniciales
            if not self.get_initial_cookies():
                return False
            
            # Paso 2: Login con credenciales
            if not self.login():
                return False
            
            # Paso 3: Conectar WebSocket
            self.connect_websocket()
            
            logging.info("✅ Conectado exitosamente a IQ Option API PURA")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error conectando: {e}")
            return False
    
    def close(self):
        """Cerrar conexiones"""
        if self.ws:
            self.ws.close()
        self.is_connected = False

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Comando requerido"}))
        return
    
    command = sys.argv[1]
    
    # Credenciales
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    api = IQOptionPureAPI(email, password)
    
    try:
        if command == "connect":
            success = api.connect()
            
            if success:
                result = {"success": True, "message": "Conectado a IQ Option API"}
                print(json.dumps(result))
                
                logging.info("🎉 ¡API conectada exitosamente!")
                logging.info("💰 Mostrando precios por 30 segundos...")
                
                # Mostrar precios por 30 segundos
                for i in range(30):
                    if api.prices:
                        for asset, data in list(api.prices.items())[:5]:
                            logging.info(f"💵 {asset}: {data['price']} ({data['source']})")
                    time.sleep(1)
                    
            else:
                result = {"success": False, "message": "Error conectando API"}
                print(json.dumps(result))
                
        elif command == "buy":
            if len(sys.argv) < 5:
                print(json.dumps({"success": False, "message": "Parámetros insuficientes: asset amount direction"}))
                return
            
            asset = sys.argv[2]
            amount = float(sys.argv[3])
            direction = sys.argv[4]
            
            if api.connect():
                result = api.execute_trade_websocket(asset, amount, direction)
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
