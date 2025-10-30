#!/usr/bin/env python3
"""
Quotex Internal API Client
Cliente para conectar directamente con la API interna de Quotex
Sin necesidad de navegador - Conexión directa
"""

import requests
import json
import time
import logging
import websocket
import threading
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexInternalAPI:
    def __init__(self):
        self.session = requests.Session()
        self.ws = None
        self.is_connected = False
        self.auth_token = None
        self.user_id = None
        self.balance = 0
        
        # Endpoints conocidos de Quotex
        self.base_url = "https://qxbroker.com"
        self.api_url = "https://api.qxbroker.com"
        self.ws_url = "wss://ws.qxbroker.com"
        
        # Credenciales
        self.email = "arnolbrom634@gmail.com"
        self.password = "7decadames"
        
        # Headers comunes
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://qxbroker.com',
            'Referer': 'https://qxbroker.com/'
        }
        
        # Datos en tiempo real
        self.live_prices = {}
        self.price_history = {}
        
    def authenticate(self):
        """Autenticar con la API de Quotex"""
        try:
            logging.info("🔐 Autenticando con API de Quotex...")
            
            # Endpoint de login
            login_url = f"{self.base_url}/api/v1/auth/login"
            
            login_data = {
                "email": self.email,
                "password": self.password,
                "remember": True
            }
            
            response = self.session.post(
                login_url, 
                json=login_data, 
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    self.auth_token = data.get("token")
                    self.user_id = data.get("user_id")
                    self.balance = data.get("balance", 0)
                    
                    # Actualizar headers con token
                    self.headers['Authorization'] = f'Bearer {self.auth_token}'
                    
                    logging.info(f"✅ Autenticación exitosa")
                    logging.info(f"   👤 User ID: {self.user_id}")
                    logging.info(f"   💰 Balance: ${self.balance}")
                    
                    return True
                else:
                    logging.error(f"❌ Error de autenticación: {data.get('message', 'Unknown error')}")
            else:
                logging.error(f"❌ Error HTTP {response.status_code}: {response.text}")
            
            return False
            
        except Exception as e:
            logging.error(f"❌ Error en autenticación: {e}")
            return False
    
    def get_assets_list(self):
        """Obtener lista de activos disponibles"""
        try:
            logging.info("📊 Obteniendo lista de activos...")
            
            assets_url = f"{self.api_url}/v1/assets"
            
            response = self.session.get(
                assets_url,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    assets = data.get("assets", [])
                    
                    # Filtrar activos OTC
                    otc_assets = [asset for asset in assets if asset.get("type") == "otc"]
                    
                    logging.info(f"✅ {len(otc_assets)} activos OTC encontrados:")
                    for asset in otc_assets[:10]:  # Mostrar primeros 10
                        logging.info(f"   📈 {asset.get('name', 'N/A')} - ID: {asset.get('id', 'N/A')}")
                    
                    return otc_assets
                else:
                    logging.error(f"❌ Error obteniendo activos: {data.get('message')}")
            else:
                logging.error(f"❌ Error HTTP {response.status_code}")
            
            return []
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo activos: {e}")
            return []
    
    def get_asset_price(self, asset_id):
        """Obtener precio actual de un activo"""
        try:
            price_url = f"{self.api_url}/v1/price/{asset_id}"
            
            response = self.session.get(
                price_url,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    price_data = data.get("price", {})
                    
                    current_price = price_data.get("current")
                    previous_price = price_data.get("previous")
                    timestamp = price_data.get("timestamp")
                    
                    if current_price and previous_price:
                        direction = "UP" if current_price > previous_price else "DOWN"
                        change_percent = ((current_price - previous_price) / previous_price) * 100
                        
                        return {
                            "asset_id": asset_id,
                            "current_price": current_price,
                            "previous_price": previous_price,
                            "direction": direction,
                            "change_percent": change_percent,
                            "timestamp": timestamp
                        }
            
            return None
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo precio {asset_id}: {e}")
            return None
    
    def get_historical_data(self, asset_id, timeframe="1m", count=100):
        """Obtener datos históricos"""
        try:
            history_url = f"{self.api_url}/v1/history/{asset_id}"
            
            params = {
                "timeframe": timeframe,
                "count": count
            }
            
            response = self.session.get(
                history_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    candles = data.get("candles", [])
                    
                    # Procesar velas
                    processed_candles = []
                    for candle in candles:
                        processed_candles.append({
                            "timestamp": candle.get("timestamp"),
                            "open": candle.get("open"),
                            "high": candle.get("high"),
                            "low": candle.get("low"),
                            "close": candle.get("close"),
                            "direction": "UP" if candle.get("close") > candle.get("open") else "DOWN"
                        })
                    
                    logging.info(f"📊 {len(processed_candles)} velas históricas obtenidas para {asset_id}")
                    return processed_candles
            
            return []
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo historial {asset_id}: {e}")
            return []
    
    def connect_websocket(self):
        """Conectar WebSocket para datos en tiempo real"""
        try:
            logging.info("🌐 Conectando WebSocket...")
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    
                    if data.get("type") == "price_update":
                        asset_id = data.get("asset_id")
                        price = data.get("price")
                        
                        if asset_id and price:
                            self.live_prices[asset_id] = price
                            
                            # Mantener historial
                            if asset_id not in self.price_history:
                                self.price_history[asset_id] = []
                            
                            self.price_history[asset_id].append({
                                "price": price,
                                "timestamp": datetime.now()
                            })
                            
                            # Mantener solo últimos 100 precios
                            if len(self.price_history[asset_id]) > 100:
                                self.price_history[asset_id] = self.price_history[asset_id][-100:]
                            
                            logging.info(f"💰 {asset_id}: ${price}")
                
                except Exception as e:
                    logging.error(f"❌ Error procesando mensaje WS: {e}")
            
            def on_error(ws, error):
                logging.error(f"❌ Error WebSocket: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                logging.info("🔌 WebSocket cerrado")
                self.is_connected = False
            
            def on_open(ws):
                logging.info("✅ WebSocket conectado")
                self.is_connected = True
                
                # Suscribirse a precios
                subscribe_msg = {
                    "type": "subscribe",
                    "channel": "prices",
                    "assets": ["UK_BRENT", "MICROSOFT", "ADA", "ETH"]
                }
                
                ws.send(json.dumps(subscribe_msg))
            
            # Crear WebSocket con token de autenticación
            ws_url_with_auth = f"{self.ws_url}?token={self.auth_token}"
            
            self.ws = websocket.WebSocketApp(
                ws_url_with_auth,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Ejecutar en thread separado
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error conectando WebSocket: {e}")
            return False
    
    def place_trade(self, asset_id, direction, amount, duration=60):
        """Colocar una operación"""
        try:
            logging.info(f"🚀 Colocando operación: {asset_id} {direction} ${amount}")
            
            trade_url = f"{self.api_url}/v1/trade"
            
            trade_data = {
                "asset_id": asset_id,
                "direction": direction.lower(),  # "up" o "down"
                "amount": amount,
                "duration": duration,
                "timestamp": int(time.time())
            }
            
            response = self.session.post(
                trade_url,
                json=trade_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    trade_id = data.get("trade_id")
                    logging.info(f"✅ Operación colocada - ID: {trade_id}")
                    return trade_id
                else:
                    logging.error(f"❌ Error en operación: {data.get('message')}")
            else:
                logging.error(f"❌ Error HTTP {response.status_code}")
            
            return None
            
        except Exception as e:
            logging.error(f"❌ Error colocando operación: {e}")
            return None
    
    def get_live_price(self, asset_id):
        """Obtener precio en vivo desde WebSocket"""
        return self.live_prices.get(asset_id)
    
    def get_price_direction(self, asset_id):
        """Determinar dirección del precio basado en historial"""
        try:
            if asset_id in self.price_history and len(self.price_history[asset_id]) >= 2:
                recent_prices = self.price_history[asset_id][-2:]
                
                current_price = recent_prices[-1]["price"]
                previous_price = recent_prices[-2]["price"]
                
                direction = "UP" if current_price > previous_price else "DOWN"
                change_percent = ((current_price - previous_price) / previous_price) * 100
                
                return {
                    "direction": direction,
                    "current_price": current_price,
                    "previous_price": previous_price,
                    "change_percent": change_percent
                }
            
            return None
            
        except Exception as e:
            logging.error(f"❌ Error calculando dirección {asset_id}: {e}")
            return None
    
    def test_connection(self):
        """Probar conexión completa"""
        try:
            logging.info("🧪 PROBANDO CONEXIÓN API INTERNA DE QUOTEX")
            logging.info("=" * 60)
            
            # 1. Autenticar
            if not self.authenticate():
                return False
            
            # 2. Obtener activos
            assets = self.get_assets_list()
            if not assets:
                return False
            
            # 3. Obtener precios
            for asset in assets[:3]:  # Probar primeros 3
                asset_id = asset.get("id")
                price_data = self.get_asset_price(asset_id)
                
                if price_data:
                    logging.info(f"💰 {asset.get('name')}: ${price_data['current_price']:.4f} ({price_data['direction']})")
            
            # 4. Conectar WebSocket
            if self.connect_websocket():
                logging.info("⏰ Esperando datos en tiempo real (10s)...")
                time.sleep(10)
                
                logging.info(f"📊 Precios en vivo recibidos: {len(self.live_prices)}")
                for asset_id, price in self.live_prices.items():
                    logging.info(f"   💵 {asset_id}: ${price}")
            
            logging.info("✅ PRUEBA COMPLETADA")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error en prueba: {e}")
            return False

def main():
    """Función principal de prueba"""
    api = QuotexInternalAPI()
    api.test_connection()

if __name__ == "__main__":
    main()
