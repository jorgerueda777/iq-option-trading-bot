#!/usr/bin/env python3
"""
Probar TODOS los assets con el método HÍBRIDO
Esto debería funcionar con TODOS los assets sin limitaciones
"""

import sys
import json
import time
import websocket
import threading
from iqoptionapi.stable_api import IQ_Option

class IQOptionHybridTester:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.api = None
        self.ws = None
        self.ssid = None
        self.connected = False
        self.trade_responses = []
        
    def connect(self):
        """Conectar usando método híbrido"""
        try:
            print("🚀 Conectando con método híbrido...")
            
            # Login con iqoptionapi
            self.api = IQ_Option(self.email, self.password)
            check, reason = self.api.connect()
            
            if not check:
                return False, reason
            
            self.api.change_balance("PRACTICE")
            
            # Obtener SSID del objeto interno
            try:
                self.ssid = self.api.api.ssid
            except:
                try:
                    self.ssid = self.api.ssid
                except:
                    # Método alternativo - obtener de cookies/session
                    self.ssid = self.api.api.session.cookies.get('ssid')
            
            if not self.ssid:
                return False, "No se pudo obtener SSID"
                
            print(f"✅ SSID obtenido: {str(self.ssid)[:20]}...")
            
            # Conectar WebSocket
            self.connect_websocket()
            time.sleep(3)  # Esperar conexión
            
            return True, "Conectado exitosamente"
            
        except Exception as e:
            return False, str(e)
    
    def connect_websocket(self):
        """Conectar WebSocket"""
        try:
            ws_url = "wss://ws.iqoption.com/echo/websocket"
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
        except Exception as e:
            print(f"❌ Error WebSocket: {e}")
    
    def on_open(self, ws):
        """Cuando se abre WebSocket"""
        print("🌐 WebSocket conectado")
        
        auth_message = {
            "name": "ssid",
            "msg": self.ssid
        }
        
        ws.send(json.dumps(auth_message))
        print("🔑 Autenticación enviada")
        self.connected = True
    
    def on_message(self, ws, message):
        """Procesar mensajes"""
        try:
            data = json.loads(message)
            
            if isinstance(data, dict) and 'name' in data:
                if any(keyword in data['name'] for keyword in ['option', 'binary']):
                    self.trade_responses.append(data)
                    if 'option-changed' in data['name']:
                        print(f"✅ OPERACIÓN CONFIRMADA: {data}")
                    elif 'option' in data['name'] and 'message' in str(data):
                        print(f"❌ RESPUESTA: {data}")
                        
        except Exception as e:
            pass
    
    def on_error(self, ws, error):
        """Error WebSocket"""
        print(f"❌ Error WebSocket: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket cerrado"""
        print("🔌 WebSocket cerrado")
        self.connected = False
    
    def test_asset(self, asset, amount=1, direction="call"):
        """Probar un asset específico"""
        if not self.connected:
            return False, "No conectado"
        
        try:
            # Mapeo de IDs conocidos
            asset_ids = {
                "EURUSD": 1, "EURUSD-OTC": 76, "GBPUSD": 2, "GBPUSD-OTC": 77,
                "USDJPY": 3, "USDJPY-OTC": 78, "AUDUSD": 4, "AUDUSD-OTC": 79,
                "USDCAD": 5, "USDCAD-OTC": 81, "GBPJPY": 6, "GBPJPY-OTC": 80,
                "EURGBP": 7, "EURGBP-OTC": 82, "EURJPY": 8, "EURJPY-OTC": 83,
                "USDCHF": 9, "USDCHF-OTC": 84, "NZDUSD": 10, "NZDUSD-OTC": 85
            }
            
            # Usar ID si está disponible, sino usar el nombre
            asset_id = asset_ids.get(asset, asset)
            
            message = {
                "name": "sendMessage",
                "msg": {
                    "name": "binary-options.open-option",
                    "version": "1.0",
                    "body": {
                        "user_balance_id": 1227944349,
                        "active_id": asset_id,
                        "option_type_id": 3,  # Turbo 1 minuto
                        "direction": direction,
                        "expired": ((int(time.time()) // 60) + 1) * 60,
                        "price": amount,
                        "value": amount,
                        "profit_income": 0.85,
                        "time_rate": 1
                    }
                },
                "request_id": int(time.time())
            }
            
            # Limpiar respuestas anteriores
            self.trade_responses = []
            
            # Enviar operación
            self.ws.send(json.dumps(message))
            
            # Esperar respuesta
            time.sleep(3)
            
            # Verificar si hubo respuesta exitosa
            for response in self.trade_responses:
                if 'option-changed' in response.get('name', ''):
                    return True, response.get('msg', {}).get('option_id', 'success')
                elif 'option' in response.get('name', '') and 'message' in str(response):
                    return False, response.get('msg', {}).get('message', 'failed')
            
            return False, "No response"
            
        except Exception as e:
            return False, str(e)

def test_all_assets_hybrid():
    """Probar todos los assets con método híbrido"""
    
    email = "arnolbrom634@gmail.com"
    password = "7decadames"
    
    try:
        print("🔍 PROBANDO TODOS LOS ASSETS CON MÉTODO HÍBRIDO...")
        print("=" * 70)
        
        # Crear tester híbrido
        tester = IQOptionHybridTester(email, password)
        
        # Conectar
        success, reason = tester.connect()
        if not success:
            print(f"❌ No se pudo conectar: {reason}")
            return
        
        # Balance inicial
        initial_balance = tester.api.get_balance()
        print(f"💰 Balance inicial: ${initial_balance}")
        print()
        
        # Lista completa de assets para probar
        test_assets = [
            # Forex principales
            "EURUSD", "EURUSD-OTC", "GBPUSD", "GBPUSD-OTC",
            "USDJPY", "USDJPY-OTC", "AUDUSD", "AUDUSD-OTC",
            "USDCAD", "USDCAD-OTC", "GBPJPY", "GBPJPY-OTC",
            "EURGBP", "EURGBP-OTC", "EURJPY", "EURJPY-OTC",
            "USDCHF", "USDCHF-OTC", "NZDUSD", "NZDUSD-OTC",
            
            # Forex secundarios
            "AUDCAD", "AUDCAD-OTC", "AUDCHF", "AUDCHF-OTC",
            "AUDJPY", "AUDJPY-OTC", "AUDNZD", "AUDNZD-OTC",
            "CADCHF", "CADCHF-OTC", "CADJPY", "CADJPY-OTC",
            "CHFJPY", "CHFJPY-OTC", "EURAUD", "EURAUD-OTC",
            "EURCAD", "EURCAD-OTC", "EURCHF", "EURCHF-OTC",
            "EURNZD", "EURNZD-OTC", "GBPAUD", "GBPAUD-OTC",
            "GBPCAD", "GBPCAD-OTC", "GBPCHF", "GBPCHF-OTC",
            "GBPNZD", "GBPNZD-OTC", "NZDCAD", "NZDCAD-OTC",
            "NZDCHF", "NZDCHF-OTC", "NZDJPY", "NZDJPY-OTC"
        ]
        
        working_assets = []
        failed_assets = []
        
        # Probar cada asset
        for i, asset in enumerate(test_assets[:20], 1):  # Limitar a 20 para no gastar mucho
            print(f"🧪 PROBANDO {i}/20: {asset}")
            
            success, result = tester.test_asset(asset)
            
            if success:
                print(f"✅ FUNCIONA - ID: {result}")
                working_assets.append(asset)
            else:
                print(f"❌ NO FUNCIONA - {result}")
                failed_assets.append(asset)
            
            time.sleep(1)  # Pausa entre pruebas
        
        print()
        print("📊 RESULTADOS FINALES CON MÉTODO HÍBRIDO:")
        print("=" * 70)
        
        print(f"✅ ASSETS QUE FUNCIONAN ({len(working_assets)}):")
        for asset in working_assets:
            print(f"   ✅ {asset}")
        
        print()
        print(f"❌ ASSETS QUE NO FUNCIONAN ({len(failed_assets)}):")
        for asset in failed_assets:
            print(f"   ❌ {asset}")
        
        # Balance final
        final_balance = tester.api.get_balance()
        print()
        print(f"💰 Balance final: ${final_balance}")
        print(f"💸 Gastado en pruebas: ${initial_balance - final_balance}")
        
        if working_assets:
            print()
            print("🎯 LISTA COMPLETA DE ASSETS HÍBRIDOS:")
            print("=" * 70)
            print("hybrid_working_assets = [")
            for asset in working_assets:
                print(f'    "{asset}",')
            print("]")
        
        return working_assets
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return []

if __name__ == "__main__":
    test_all_assets_hybrid()
