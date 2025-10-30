#!/usr/bin/env python3
"""
Quotex Auto Trading Bot
API más confiable que IQ Option para operaciones automáticas
"""

import sys
import json
import time
import logging
import requests
import threading
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexBot:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.token = None
        self.balance = 0
        self.connected = False
        
        # Configuración de headers para evitar detección
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Content-Type': 'application/json'
        })
    
    def connect(self):
        """Conectar a Quotex"""
        try:
            logging.info("🔧 Conectando a Quotex...")
            
            # URL de login de Quotex (URL real)
            login_url = "https://qxbroker.com/en/sign-in"
            
            login_data = {
                "email": self.email,
                "password": self.password,
                "platform": "web"
            }
            
            response = self.session.post(login_url, json=login_data)
            
            # DEBUG: Ver qué respuesta recibimos
            logging.info(f"🔍 Status Code: {response.status_code}")
            logging.info(f"🔍 Response Text: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data.get('token')
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    self.connected = True
                    
                    # Obtener balance
                    self.get_balance()
                    
                    logging.info(f"✅ Conectado a Quotex - Balance: ${self.balance}")
                    return {"success": True, "message": "Conectado exitosamente", "balance": self.balance}
                else:
                    logging.error(f"❌ Error de login: {data.get('message')}")
                    return {"success": False, "message": data.get('message')}
            else:
                logging.error(f"❌ Error HTTP: {response.status_code}")
                return {"success": False, "message": f"Error HTTP: {response.status_code}"}
                
        except Exception as e:
            logging.error(f"❌ Error conectando: {e}")
            return {"success": False, "message": str(e)}
    
    def get_balance(self):
        """Obtener balance actual"""
        try:
            balance_url = "https://qxbroker.com/api/v1/user/balance"
            response = self.session.get(balance_url)
            
            if response.status_code == 200:
                data = response.json()
                self.balance = data.get('balance', 0)
                return self.balance
            else:
                logging.warning("⚠️ No se pudo obtener balance")
                return 0
                
        except Exception as e:
            logging.error(f"❌ Error obteniendo balance: {e}")
            return 0
    
    def get_available_assets(self):
        """Obtener activos disponibles"""
        try:
            assets_url = "https://qxbroker.com/api/v1/assets"
            response = self.session.get(assets_url)
            
            if response.status_code == 200:
                data = response.json()
                assets = data.get('assets', [])
                
                logging.info(f"📊 Activos disponibles: {len(assets)}")
                for asset in assets[:10]:  # Mostrar primeros 10
                    name = asset.get('name')
                    payout = asset.get('payout', 0)
                    logging.info(f"   - {name}: {payout}% payout")
                
                return assets
            else:
                logging.warning("⚠️ No se pudieron obtener activos")
                return []
                
        except Exception as e:
            logging.error(f"❌ Error obteniendo activos: {e}")
            return []
    
    def execute_trade(self, asset, amount, direction, duration=60):
        """Ejecutar operación en Quotex"""
        try:
            logging.info(f"🎯 Ejecutando: {asset} {direction.upper()} ${amount} por {duration}s")
            
            trade_url = "https://qxbroker.com/api/v1/trade/binary"
            
            trade_data = {
                "asset": asset,
                "amount": amount,
                "direction": direction.lower(),  # "call" o "put"
                "duration": duration,
                "timestamp": int(time.time())
            }
            
            response = self.session.post(trade_url, json=trade_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    trade_id = data.get('trade_id')
                    logging.info(f"✅ Operación ejecutada - ID: {trade_id}")
                    
                    return {
                        "success": True,
                        "trade_id": trade_id,
                        "message": f"Operación {direction.upper()} ejecutada",
                        "asset": asset,
                        "amount": amount,
                        "direction": direction
                    }
                else:
                    error_msg = data.get('message', 'Error desconocido')
                    logging.error(f"❌ Error ejecutando: {error_msg}")
                    return {"success": False, "message": error_msg}
            else:
                logging.error(f"❌ Error HTTP: {response.status_code}")
                return {"success": False, "message": f"Error HTTP: {response.status_code}"}
                
        except Exception as e:
            logging.error(f"❌ Error ejecutando operación: {e}")
            return {"success": False, "message": str(e)}
    
    def execute_multiple_trades(self, trades):
        """Ejecutar múltiples operaciones simultáneamente"""
        try:
            logging.info(f"🚀 Ejecutando {len(trades)} operaciones simultáneas...")
            
            results = []
            threads = []
            
            def execute_single(trade_data):
                result = self.execute_trade(
                    trade_data['asset'],
                    trade_data['amount'], 
                    trade_data['direction'],
                    trade_data.get('duration', 60)
                )
                results.append(result)
            
            # Crear threads para ejecución simultánea
            for trade in trades:
                thread = threading.Thread(target=execute_single, args=(trade,))
                threads.append(thread)
            
            # Ejecutar todas al mismo tiempo
            start_time = time.time()
            for thread in threads:
                thread.start()
            
            # Esperar que terminen todas
            for thread in threads:
                thread.join()
            
            execution_time = time.time() - start_time
            successful = sum(1 for r in results if r.get('success'))
            
            logging.info(f"🎉 {successful}/{len(trades)} operaciones exitosas en {execution_time:.2f}s")
            
            return {
                "success": True,
                "total_trades": len(trades),
                "successful_trades": successful,
                "execution_time": execution_time,
                "results": results
            }
            
        except Exception as e:
            logging.error(f"❌ Error ejecutando múltiples operaciones: {e}")
            return {"success": False, "message": str(e)}

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Uso: python script.py [connect|trade|multi]"}))
        return
    
    command = sys.argv[1]
    
    # Credenciales (temporales - luego las pondremos en config)
    email = "arnolbrom634@gmail.com"  # Cambiar por tu email de Quotex
    password = "7decadames"  # Cambiar por tu password de Quotex
    
    bot = QuotexBot(email, password)
    
    try:
        if command == "connect":
            result = bot.connect()
            if result["success"]:
                assets = bot.get_available_assets()
            print(json.dumps(result))
            
        elif command == "trade":
            if len(sys.argv) < 6:
                print(json.dumps({"success": False, "message": "Uso: trade <asset> <amount> <direction> <duration>"}))
                return
            
            asset = sys.argv[2]
            amount = float(sys.argv[3])
            direction = sys.argv[4]
            duration = int(sys.argv[5])
            
            # Conectar primero
            connect_result = bot.connect()
            if not connect_result["success"]:
                print(json.dumps(connect_result))
                return
            
            # Ejecutar operación
            result = bot.execute_trade(asset, amount, direction, duration)
            print(json.dumps(result))
            
        elif command == "multi":
            # Ejemplo de múltiples operaciones
            trades = [
                {"asset": "EURUSD", "amount": 1, "direction": "call", "duration": 60},
                {"asset": "GBPUSD", "amount": 1, "direction": "put", "duration": 60},
                {"asset": "USDJPY", "amount": 1, "direction": "call", "duration": 60}
            ]
            
            # Conectar primero
            connect_result = bot.connect()
            if not connect_result["success"]:
                print(json.dumps(connect_result))
                return
            
            # Ejecutar múltiples operaciones
            result = bot.execute_multiple_trades(trades)
            print(json.dumps(result))
            
        else:
            print(json.dumps({"success": False, "message": f"Comando desconocido: {command}"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))

if __name__ == "__main__":
    main()
