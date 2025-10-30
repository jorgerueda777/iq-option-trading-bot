#!/usr/bin/env python3
"""
IQ Option Bot HÍBRIDO - Combina lo mejor de ambos métodos
- Login con iqoptionapi (funciona)
- Ejecución con WebSocket puro (funciona con TODOS los assets)
"""

import sys
import json
import time
import websocket
import threading
from iqoptionapi.stable_api import IQ_Option

class IQOptionHybrid:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.api = None
        self.ws = None
        self.ssid = None
        self.connected = False
        
    def connect(self):
        """Conectar usando iqoptionapi para obtener SSID"""
        try:
            print("🚀 Conectando con método híbrido...")
            
            # Usar iqoptionapi solo para login y obtener SSID
            self.api = IQ_Option(self.email, self.password)
            check, reason = self.api.connect()
            
            if not check:
                return False, reason
            
            # Cambiar a DEMO
            self.api.change_balance("PRACTICE")
            
            # Obtener SSID del objeto api
            self.ssid = self.api.ssid
            print(f"✅ SSID obtenido: {self.ssid[:20]}...")
            
            # Conectar WebSocket con el SSID
            self.connect_websocket()
            
            return True, "Conectado exitosamente"
            
        except Exception as e:
            return False, str(e)
    
    def connect_websocket(self):
        """Conectar WebSocket usando el SSID obtenido"""
        try:
            ws_url = "wss://ws.iqoption.com/echo/websocket"
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # Ejecutar WebSocket en hilo separado
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Esperar conexión
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Error WebSocket: {e}")
    
    def on_open(self, ws):
        """Cuando se abre la conexión WebSocket"""
        print("🌐 WebSocket conectado")
        
        # Autenticar con SSID
        auth_message = {
            "name": "ssid",
            "msg": self.ssid
        }
        
        ws.send(json.dumps(auth_message))
        print("🔑 Autenticación enviada")
        self.connected = True
    
    def on_message(self, ws, message):
        """Procesar mensajes del WebSocket"""
        try:
            data = json.loads(message)
            
            # Capturar respuestas de operaciones
            if isinstance(data, dict) and 'name' in data:
                if 'option' in data['name']:
                    print(f"🎯 RESPUESTA OPERACIÓN: {data}")
                    
        except Exception as e:
            pass
    
    def on_error(self, ws, error):
        """Manejar errores del WebSocket"""
        print(f"❌ Error WebSocket: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Cuando se cierra la conexión"""
        print("🔌 WebSocket cerrado")
        self.connected = False
    
    def buy(self, amount, asset, direction, duration=1):
        """Ejecutar operación usando WebSocket puro"""
        if not self.connected:
            return False, "No conectado"
        
        try:
            # Obtener asset_id del mapeo interno de iqoptionapi
            asset_id = self.get_asset_id(asset)
            
            if not asset_id:
                # Si no encuentra el asset, usar WebSocket puro con nombre
                asset_id = asset
            
            # Mensaje de operación usando WebSocket puro
            message = {
                "name": "sendMessage",
                "msg": {
                    "name": "binary-options.open-option",
                    "version": "1.0",
                    "body": {
                        "user_balance_id": 1227944349,  # Tu balance USD DEMO
                        "active_id": asset_id,
                        "option_type_id": 3,  # Turbo 1 minuto
                        "direction": direction,
                        "expired": ((int(time.time()) // 60) + 1) * 60,
                        "price": amount,
                        "value": amount,
                        "profit_income": 0.85,
                        "time_rate": duration
                    }
                },
                "request_id": int(time.time())
            }
            
            # Enviar por WebSocket
            self.ws.send(json.dumps(message))
            print(f"✅ Operación enviada: {asset} {direction} ${amount}")
            
            return True, int(time.time())
            
        except Exception as e:
            print(f"❌ Error ejecutando operación: {e}")
            return False, str(e)
    
    def get_asset_id(self, asset_name):
        """Intentar obtener ID del asset"""
        try:
            # Mapeo de assets conocidos
            asset_map = {
                "EURUSD-OTC": 76,
                "GBPUSD-OTC": 77,
                "AUDUSD-OTC": 79,
                "USDJPY-OTC": 78,
                "GBPJPY-OTC": 80,
                # Agregar más según se descubran
            }
            
            return asset_map.get(asset_name, asset_name)
            
        except:
            return asset_name
    
    def get_balance(self):
        """Obtener balance usando iqoptionapi"""
        if self.api:
            return self.api.get_balance()
        return 0

def execute_hybrid_trade(asset, amount, direction):
    """Ejecutar operación con método híbrido"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    try:
        # Crear instancia híbrida
        hybrid = IQOptionHybrid(email, password)
        
        # Conectar
        success, reason = hybrid.connect()
        if not success:
            return {"success": False, "message": reason}
        
        # Obtener balance
        balance = hybrid.get_balance()
        print(f"💰 Balance: ${balance}")
        
        # Ejecutar operación
        success, trade_id = hybrid.buy(amount, asset, direction)
        
        if success:
            return {"success": True, "trade_id": trade_id, "method": "hybrid"}
        else:
            return {"success": False, "message": trade_id}
            
    except Exception as e:
        return {"success": False, "message": str(e)}

def main():
    """Función principal"""
    if len(sys.argv) < 5:
        print("Uso: python iq_option_hybrid.py buy ASSET AMOUNT DIRECTION")
        return
    
    command = sys.argv[1]
    asset = sys.argv[2]
    amount = float(sys.argv[3])
    direction = sys.argv[4].lower()
    
    if command == "buy":
        result = execute_hybrid_trade(asset, amount, direction)
        print(json.dumps(result))

if __name__ == "__main__":
    main()
