#!/usr/bin/env python3
"""
Test de API de Quotex SIN Chrome - Estilo main.py
Prueba conexiones directas a APIs y WebSockets de Quotex
"""

import requests
import json
import time
import logging
import websocket
import threading
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexAPIPureTester:
    def __init__(self):
        self.session = requests.Session()
        self.ws = None
        self.prices_found = []
        self.running = True
        
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
    
    def test_quotex_endpoints(self):
        """Probar endpoints conocidos de Quotex"""
        try:
            logging.info("🌐 PROBANDO ENDPOINTS DE QUOTEX...")
            
            endpoints = [
                "https://qxbroker.com/api/v1/prices",
                "https://qxbroker.com/api/v1/assets",
                "https://qxbroker.com/api/v1/quotes",
                "https://qxbroker.com/api/v1/market/data",
                "https://qxbroker.com/api/v1/trading/assets",
                "https://qxbroker.com/api/prices",
                "https://qxbroker.com/api/assets",
                "https://qxbroker.com/api/quotes",
                "https://qxbroker.com/api/market",
                "https://qxbroker.com/prices",
                "https://qxbroker.com/quotes",
                "https://qxbroker.com/market",
                "https://api.qxbroker.com/v1/prices",
                "https://api.qxbroker.com/v1/assets",
                "https://api.qxbroker.com/prices",
                "https://websocket.qxbroker.com/prices",
                "https://ws.qxbroker.com/prices"
            ]
            
            successful_endpoints = []
            
            for endpoint in endpoints:
                try:
                    logging.info(f"🔍 Probando: {endpoint}")
                    
                    response = self.session.get(endpoint, timeout=10)
                    
                    logging.info(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logging.info(f"   ✅ JSON válido: {len(str(data))} chars")
                            
                            # Buscar precios en la respuesta
                            prices = self.extract_prices_from_data(data)
                            if prices:
                                logging.info(f"   💰 Precios encontrados: {prices}")
                                successful_endpoints.append({
                                    'endpoint': endpoint,
                                    'data': data,
                                    'prices': prices
                                })
                            
                        except:
                            logging.info(f"   📄 Respuesta texto: {response.text[:100]}...")
                            
                    elif response.status_code == 401:
                        logging.info(f"   🔐 Requiere autenticación")
                    elif response.status_code == 403:
                        logging.info(f"   🚫 Acceso denegado")
                    else:
                        logging.info(f"   ❌ Error: {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    logging.info(f"   ⏰ Timeout")
                except requests.exceptions.ConnectionError:
                    logging.info(f"   🔌 Error de conexión")
                except Exception as e:
                    logging.info(f"   ❌ Error: {str(e)[:50]}")
                
                time.sleep(0.5)  # No saturar
            
            logging.info(f"📊 ENDPOINTS EXITOSOS: {len(successful_endpoints)}")
            return successful_endpoints
            
        except Exception as e:
            logging.error(f"❌ Error probando endpoints: {e}")
            return []
    
    def extract_prices_from_data(self, data):
        """Extraer precios de datos JSON"""
        try:
            prices = []
            
            def search_recursive(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        new_path = f"{path}.{key}" if path else key
                        
                        # Buscar claves relacionadas con precios
                        if any(keyword in key.lower() for keyword in ['price', 'rate', 'quote', 'value', 'amount']):
                            if isinstance(value, (int, float)) and 0.01 < value < 100000:
                                prices.append({
                                    'path': new_path,
                                    'key': key,
                                    'value': value
                                })
                        
                        search_recursive(value, new_path)
                        
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        search_recursive(item, f"{path}[{i}]")
                        
                elif isinstance(obj, (int, float)):
                    if 0.01 < obj < 100000:
                        # Verificar si parece un precio
                        str_val = str(obj)
                        if '.' in str_val and len(str_val) < 10:
                            prices.append({
                                'path': path,
                                'key': 'numeric_value',
                                'value': obj
                            })
            
            search_recursive(data)
            return prices[:10]  # Top 10
            
        except Exception as e:
            logging.error(f"❌ Error extrayendo precios: {e}")
            return []
    
    def test_websocket_connections(self):
        """Probar conexiones WebSocket"""
        try:
            logging.info("🌐 PROBANDO WEBSOCKETS DE QUOTEX...")
            
            ws_urls = [
                "wss://qxbroker.com/websocket",
                "wss://qxbroker.com/ws",
                "wss://qxbroker.com/socket",
                "wss://api.qxbroker.com/websocket",
                "wss://api.qxbroker.com/ws",
                "wss://ws.qxbroker.com/",
                "wss://websocket.qxbroker.com/",
                "wss://socket.qxbroker.com/",
                "wss://qxbroker.com/api/websocket",
                "wss://qxbroker.com/api/ws"
            ]
            
            successful_ws = []
            
            for ws_url in ws_urls:
                try:
                    logging.info(f"🔌 Probando WebSocket: {ws_url}")
                    
                    def on_message(ws, message):
                        try:
                            data = json.loads(message)
                            prices = self.extract_prices_from_data(data)
                            if prices:
                                logging.info(f"💰 WebSocket precio: {prices}")
                                self.prices_found.extend(prices)
                        except:
                            logging.info(f"📄 WebSocket mensaje: {message[:100]}...")
                    
                    def on_error(ws, error):
                        logging.info(f"❌ WebSocket error: {error}")
                    
                    def on_close(ws, close_status_code, close_msg):
                        logging.info(f"🔌 WebSocket cerrado: {close_status_code}")
                    
                    def on_open(ws):
                        logging.info(f"✅ WebSocket conectado: {ws_url}")
                        successful_ws.append(ws_url)
                        
                        # Enviar mensajes de prueba
                        test_messages = [
                            '{"action":"subscribe","data":{"asset":"BRENT_otc"}}',
                            '{"type":"subscribe","asset":"BRENT_otc"}',
                            '{"cmd":"subscribe","symbol":"BRENT_otc"}',
                            '{"subscribe":"prices"}',
                            '{"action":"get_prices"}',
                            'ping'
                        ]
                        
                        for msg in test_messages:
                            try:
                                ws.send(msg)
                                time.sleep(0.5)
                            except:
                                pass
                    
                    # Crear WebSocket con timeout corto
                    ws = websocket.WebSocketApp(
                        ws_url,
                        on_open=on_open,
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close
                    )
                    
                    # Ejecutar por 5 segundos
                    ws_thread = threading.Thread(target=ws.run_forever)
                    ws_thread.daemon = True
                    ws_thread.start()
                    
                    time.sleep(5)
                    ws.close()
                    
                except Exception as e:
                    logging.info(f"❌ Error WebSocket: {str(e)[:50]}")
                
                time.sleep(1)
            
            logging.info(f"📊 WEBSOCKETS EXITOSOS: {len(successful_ws)}")
            return successful_ws
            
        except Exception as e:
            logging.error(f"❌ Error probando WebSockets: {e}")
            return []
    
    def test_external_apis(self):
        """Probar APIs externas para precios de commodities"""
        try:
            logging.info("🌍 PROBANDO APIS EXTERNAS...")
            
            external_apis = [
                {
                    'name': 'Alpha Vantage',
                    'url': 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=BZ=F&apikey=demo',
                    'asset': 'BRENT'
                },
                {
                    'name': 'Yahoo Finance',
                    'url': 'https://query1.finance.yahoo.com/v8/finance/chart/BZ=F',
                    'asset': 'BRENT'
                },
                {
                    'name': 'Investing.com API',
                    'url': 'https://api.investing.com/api/financialdata/8833/historical/chart/?period=P1D&interval=PT1M&pointscount=60',
                    'asset': 'BRENT'
                },
                {
                    'name': 'MarketData API',
                    'url': 'https://api.marketdata.app/v1/stocks/quotes/BZ=F/',
                    'asset': 'BRENT'
                },
                {
                    'name': 'Finnhub',
                    'url': 'https://finnhub.io/api/v1/quote?symbol=BZ=F&token=demo',
                    'asset': 'BRENT'
                },
                {
                    'name': 'Quandl',
                    'url': 'https://www.quandl.com/api/v3/datasets/CHRIS/ICE_B1.json?limit=1',
                    'asset': 'BRENT'
                }
            ]
            
            successful_apis = []
            
            for api in external_apis:
                try:
                    logging.info(f"🔍 Probando {api['name']}...")
                    
                    response = self.session.get(api['url'], timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            prices = self.extract_prices_from_data(data)
                            
                            if prices:
                                logging.info(f"   ✅ {api['name']}: {len(prices)} precios")
                                for price in prices[:3]:
                                    logging.info(f"      💰 {price['value']} ({price['key']})")
                                
                                successful_apis.append({
                                    'name': api['name'],
                                    'url': api['url'],
                                    'prices': prices
                                })
                            else:
                                logging.info(f"   📄 {api['name']}: Sin precios")
                                
                        except:
                            logging.info(f"   📄 {api['name']}: Respuesta no JSON")
                    else:
                        logging.info(f"   ❌ {api['name']}: {response.status_code}")
                        
                except Exception as e:
                    logging.info(f"   ❌ {api['name']}: {str(e)[:50]}")
                
                time.sleep(0.5)
            
            logging.info(f"📊 APIS EXTERNAS EXITOSAS: {len(successful_apis)}")
            return successful_apis
            
        except Exception as e:
            logging.error(f"❌ Error probando APIs externas: {e}")
            return []
    
    def run_full_test(self):
        """Ejecutar prueba completa sin Chrome"""
        try:
            logging.info("🚀 INICIANDO PRUEBA COMPLETA DE API SIN CHROME")
            logging.info("=" * 60)
            
            # 1. Probar endpoints de Quotex
            quotex_results = self.test_quotex_endpoints()
            
            # 2. Probar WebSockets
            ws_results = self.test_websocket_connections()
            
            # 3. Probar APIs externas
            external_results = self.test_external_apis()
            
            # 4. Resumen final
            logging.info("🎯 RESUMEN FINAL:")
            logging.info("=" * 60)
            
            total_prices = 0
            
            if quotex_results:
                logging.info(f"✅ Quotex Endpoints: {len(quotex_results)} exitosos")
                for result in quotex_results:
                    total_prices += len(result.get('prices', []))
            else:
                logging.info("❌ Quotex Endpoints: Ninguno exitoso")
            
            if ws_results:
                logging.info(f"✅ WebSockets: {len(ws_results)} conectados")
            else:
                logging.info("❌ WebSockets: Ninguno conectado")
            
            if external_results:
                logging.info(f"✅ APIs Externas: {len(external_results)} exitosas")
                for result in external_results:
                    total_prices += len(result.get('prices', []))
            else:
                logging.info("❌ APIs Externas: Ninguna exitosa")
            
            logging.info(f"💰 TOTAL PRECIOS ENCONTRADOS: {total_prices}")
            
            # Mostrar mejores fuentes de precios
            if external_results:
                logging.info("🏆 MEJORES FUENTES DE PRECIOS:")
                for result in external_results:
                    if result.get('prices'):
                        logging.info(f"   🥇 {result['name']}: {result['prices'][0]['value']}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error en prueba completa: {e}")
            return False

def main():
    """Función principal"""
    tester = QuotexAPIPureTester()
    tester.run_full_test()

if __name__ == "__main__":
    main()
