#!/usr/bin/env python3
"""
IQ Option Python Bridge
Conecta con la API oficial de IQ Option para ejecutar operaciones reales
"""

import sys
import json
import time
import logging
import requests
from iqoptionapi.stable_api import IQ_Option

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class IQOptionBridge:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.api = None
        self.connected = False
        
    def connect(self):
        """Conectar a IQ Option"""
        try:
            # FORZAR SERVIDOR ESPECÍFICO PARA EVITAR RESTRICCIONES
            self.api = IQ_Option(self.email, self.password)
            self.api.API_URL = "https://iqoption.com/api"  # Servidor alternativo
            check, reason = self.api.connect()
            
            if check:
                self.connected = True
                # CUENTA DEMO para opciones binarias OTC
                self.api.change_balance("PRACTICE")  # PRACTICE = Demo, REAL = Real
                
                # ESPERAR UN POCO PARA ESTABILIZAR CONEXIÓN
                import time
                time.sleep(1)
                
                # VERIFICAR ASSETS DISPONIBLES
                logging.info("🔍 Verificando assets disponibles...")
                try:
                    assets = self.api.get_all_open_time()
                    for asset, status in assets.items():
                        if 'EUR' in asset or 'USD' in asset:
                            logging.info(f"📊 {asset}: {status}")
                except Exception as e:
                    logging.error(f"❌ Error verificando assets: {e}")
                balance = self.api.get_balance()
                
                return {
                    "success": True,
                    "message": "Conectado exitosamente",
                    "balance": balance
                }
            else:
                return {
                    "success": False,
                    "message": f"Error de conexión: {reason}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def buy_option(self, asset, amount, direction, duration):
        """Ejecutar operación binaria"""
        try:
            if not self.connected:
                return {"success": False, "message": "No conectado"}
            
            # CONVERTIR ASSETS OTC A FORMATO CORRECTO
            asset_mapping = {
                "EURUSD-OTC": "EURUSD",
                "GBPUSD-OTC": "GBPUSD", 
                "USDJPY-OTC": "USDJPY",
                "AUDUSD-OTC": "AUDUSD"
            }
            
            # Usar asset correcto
            correct_asset = asset_mapping.get(asset, asset)
            logging.info(f"🔄 Convirtiendo {asset} → {correct_asset}")
            
            # Convertir dirección
            action = "call" if direction.upper() == "CALL" else "put"
            logging.info(f"🎯 Ejecutando: {correct_asset} {action} ${amount} por {duration}s")
            
            # EJECUTAR OPERACIÓN DIRECTAMENTE (SIN COMPLICACIONES)
            try:
                logging.info(f"🎯 Ejecutando operación...")
                check, operation_id = self.api.buy(amount, correct_asset, action, duration)
                logging.info(f"📊 Resultado: check={check}, operation_id={operation_id}")
            except Exception as e:
                logging.error(f"❌ Error ejecutando: {e}")
                check = False
                operation_id = f"Error: {str(e)}"
            
            if check:
                return {
                    "success": True,
                    "operation_id": operation_id,
                    "message": f"Operación ejecutada: {asset} {action} ${amount}"
                }
            else:
                return {
                    "success": False,
                    "message": "Error ejecutando operación"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def check_result(self, operation_id):
        """Verificar resultado de operación"""
        try:
            result = self.api.check_win_v3(operation_id)
            return {
                "success": True,
                "result": result,
                "operation_id": operation_id
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

def main():
    """Función principal para comunicación con Node.js"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Comando requerido"}))
        return
    
    command = sys.argv[1]
    
    # Leer credenciales del archivo de configuración
    try:
        import os
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'iqoption_credentials.json')
        with open(config_path, 'r') as f:
            credentials = json.load(f)
        
        email = credentials['email']
        password = credentials['password']
        
        if password == "TU_PASSWORD_REAL_AQUI":
            print(json.dumps({"success": False, "message": "DEBES configurar tu contraseña real en config/iqoption_credentials.json"}))
            return
            
    except Exception as e:
        print(json.dumps({"success": False, "message": f"Error leyendo credenciales: {str(e)}"}))
        return
    
    bridge = IQOptionBridge(email, password)
    
    if command == "connect":
        result = bridge.connect()
        print(json.dumps(result))
        
    elif command == "buy":
        if len(sys.argv) < 6:
            print(json.dumps({"success": False, "message": "Parámetros insuficientes"}))
            return
            
        asset = sys.argv[2]
        amount = float(sys.argv[3])
        direction = sys.argv[4]
        duration = int(sys.argv[5])
        
        # Conectar primero
        connect_result = bridge.connect()
        if not connect_result["success"]:
            print(json.dumps(connect_result))
            return
        
        # Ejecutar operación
        result = bridge.buy_option(asset, amount, direction, duration)
        print(json.dumps(result))
        
    elif command == "check":
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "message": "Operation ID requerido"}))
            return
            
        operation_id = sys.argv[2]
        
        # Conectar primero
        connect_result = bridge.connect()
        if not connect_result["success"]:
            print(json.dumps(connect_result))
            return
        
        # Verificar resultado
        result = bridge.check_result(operation_id)
        print(json.dumps(result))
        
    else:
        print(json.dumps({"success": False, "message": f"Comando desconocido: {command}"}))

if __name__ == "__main__":
    main()
