#!/usr/bin/env python3
"""
Quotex Real API Client - Usando PyQuotex Oficial
Cliente basado en la documentación oficial de PyQuotex
"""

import asyncio
import logging
import time
from datetime import datetime
from collections import deque

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexRealAPIClient:
    def __init__(self):
        self.logger = logging.getLogger('QuotexRealAPI')
        self.client = None
        self.is_connected = False
        self.is_authenticated = False
        
        # Credenciales
        self.email = "arnolbrom634@gmail.com"
        self.password = "7decadames"
        
        # Datos en tiempo real
        self.live_prices = {}
        self.candle_history = {}
        
        # Activos objetivo
        self.target_assets = {
            "UK BRENT": "BRENT_otc",
            "MICROSOFT": "MSFT_otc", 
            "ADA": "ADA_otc",
            "ETH": "ETH_otc"
        }
        
    async def initialize_client(self):
        """Inicializar cliente PyQuotex"""
        try:
            self.logger.info("🔧 Inicializando cliente PyQuotex...")
            
            # Intentar importar PyQuotex
            try:
                from pyquotex.stable_api import Quotex
                self.logger.info("✅ PyQuotex importado correctamente")
            except ImportError:
                self.logger.error("❌ PyQuotex no está instalado")
                self.logger.info("💡 Instala con: pip install pyquotex")
                return False
            
            # Inicializar cliente
            self.client = Quotex(
                email=self.email,
                password=self.password,
                lang="en"
            )
            
            # Habilitar debug
            self.client.debug_ws_enable = True
            
            self.logger.info("✅ Cliente PyQuotex inicializado")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando cliente: {e}")
            return False
    
    async def connect_with_retries(self, attempts=5):
        """Conectar con reintentos"""
        try:
            self.logger.info("🔐 Conectando a Quotex...")
            
            check_connect, message = await self.client.connect()
            
            if not check_connect:
                attempt = 0
                while attempt <= attempts:
                    if not await self.client.check_connect():
                        self.logger.info(f"🔄 Reintento {attempt+1}/{attempts}")
                        check_connect, message = await self.client.connect()
                        
                        if check_connect:
                            self.logger.info("✅ Reconexión exitosa")
                            break
                        else:
                            attempt += 1
                            await asyncio.sleep(5)
                    else:
                        break
            
            if check_connect:
                self.logger.info("✅ Conexión exitosa a Quotex")
                self.is_connected = True
                self.is_authenticated = True
                return True
            else:
                self.logger.error(f"❌ Error de conexión: {message}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando: {e}")
            return False
    
    async def get_assets_list(self):
        """Obtener lista de activos"""
        try:
            self.logger.info("📊 Obteniendo lista de activos...")
            
            # Usar método de PyQuotex para obtener activos
            assets = await self.client.get_all_asset_name()
            
            if assets:
                self.logger.info(f"✅ {len(assets)} activos obtenidos")
                
                # Mostrar algunos activos
                for i, asset in enumerate(list(assets.keys())[:10]):
                    self.logger.info(f"   📈 {i+1}. {asset}")
                
                return assets
            else:
                self.logger.warning("⚠️ No se obtuvieron activos")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo activos: {e}")
            return {}
    
    async def start_realtime_price(self, asset_name):
        """Iniciar stream de precios en tiempo real"""
        try:
            # Mapear nombre de activo
            quotex_asset = self.target_assets.get(asset_name, asset_name)
            
            self.logger.info(f"📡 Iniciando stream para {asset_name} ({quotex_asset})")
            
            # Iniciar stream de precios según documentación
            await self.client.start_realtime_price(quotex_asset, 60)
            
            self.logger.info(f"✅ Stream iniciado para {asset_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando stream {asset_name}: {e}")
            return False
    
    async def get_realtime_price(self, asset_name):
        """Obtener precio en tiempo real"""
        try:
            # Mapear nombre de activo
            quotex_asset = self.target_assets.get(asset_name, asset_name)
            
            # Obtener precio según documentación
            price_data = await self.client.get_realtime_price(quotex_asset)
            
            if price_data:
                current_price = price_data.get('price', 0)
                timestamp = price_data.get('timestamp', datetime.now())
                
                # Determinar dirección
                direction = self.calculate_direction(asset_name, current_price)
                
                # Actualizar cache
                self.live_prices[asset_name] = {
                    "price": current_price,
                    "direction": direction,
                    "timestamp": timestamp
                }
                
                self.logger.info(f"📊 {asset_name}: {current_price:.6f} ({direction}) REAL")
                
                return {
                    "asset": asset_name,
                    "price": current_price,
                    "direction": direction,
                    "timestamp": timestamp,
                    "source": "pyquotex_real"
                }
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo precio {asset_name}: {e}")
            return None
    
    def calculate_direction(self, asset_name, current_price):
        """Calcular dirección del precio"""
        try:
            if asset_name in self.live_prices:
                previous_price = self.live_prices[asset_name]["price"]
                return "UP" if current_price > previous_price else "DOWN"
            else:
                return "UP"  # Primera lectura
        except:
            return "UP"
    
    async def start_candles_stream(self, asset_name):
        """Iniciar stream de velas"""
        try:
            quotex_asset = self.target_assets.get(asset_name, asset_name)
            
            self.logger.info(f"🕯️ Iniciando stream de velas para {asset_name}")
            
            # Iniciar stream de velas según documentación
            self.client.start_candles_stream(quotex_asset, 0)  # 0 = 1 minuto
            self.client.follow_candle(quotex_asset)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando velas {asset_name}: {e}")
            return False
    
    async def get_candle_history(self, asset_name, count=10):
        """Obtener historial de velas"""
        try:
            quotex_asset = self.target_assets.get(asset_name, asset_name)
            
            # Obtener velas históricas
            candles = await self.client.get_candles(quotex_asset, 60, count)  # 60 segundos
            
            if candles:
                directions = []
                for candle in candles:
                    direction = "UP" if candle['close'] > candle['open'] else "DOWN"
                    directions.append(direction)
                
                # Actualizar cache
                if asset_name not in self.candle_history:
                    self.candle_history[asset_name] = deque(maxlen=100)
                
                self.candle_history[asset_name].extend(directions)
                
                self.logger.info(f"📈 {asset_name}: {len(directions)} velas históricas obtenidas")
                return directions
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo historial {asset_name}: {e}")
            return []
    
    async def test_connection(self):
        """Probar conexión completa"""
        try:
            self.logger.info("🧪 PROBANDO CONEXIÓN PYQUOTEX REAL")
            self.logger.info("=" * 60)
            
            # 1. Inicializar cliente
            if not await self.initialize_client():
                return False
            
            # 2. Conectar
            if not await self.connect_with_retries():
                return False
            
            # 3. Obtener activos
            assets = await self.get_assets_list()
            
            # 4. Probar precios en tiempo real
            self.logger.info("💰 PROBANDO PRECIOS EN TIEMPO REAL:")
            
            for asset_name in self.target_assets.keys():
                # Iniciar stream
                await self.start_realtime_price(asset_name)
                await asyncio.sleep(2)
                
                # Obtener precio
                price_data = await self.get_realtime_price(asset_name)
                
                if price_data:
                    self.logger.info(f"✅ {asset_name}: ${price_data['price']:.6f} ({price_data['direction']})")
                else:
                    self.logger.warning(f"⚠️ {asset_name}: No se obtuvo precio")
                
                await asyncio.sleep(1)
            
            # 5. Probar historial
            self.logger.info("📈 PROBANDO HISTORIAL DE VELAS:")
            
            for asset_name in list(self.target_assets.keys())[:2]:  # Solo 2 para no saturar
                history = await self.get_candle_history(asset_name, 5)
                if history:
                    self.logger.info(f"✅ {asset_name}: {history}")
                
                await asyncio.sleep(1)
            
            self.logger.info("✅ PRUEBA COMPLETADA - PYQUOTEX FUNCIONANDO")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en prueba: {e}")
            return False
        finally:
            if self.client:
                try:
                    await self.client.close()
                except:
                    pass
    
    async def close(self):
        """Cerrar conexión"""
        try:
            if self.client:
                await self.client.close()
                self.logger.info("👋 Conexión cerrada")
        except Exception as e:
            self.logger.error(f"❌ Error cerrando: {e}")

async def main():
    """Función principal"""
    client = QuotexRealAPIClient()
    
    try:
        success = await client.test_connection()
        
        if success:
            print("\n🎉 ¡PYQUOTEX FUNCIONANDO! Endpoints reales confirmados.")
        else:
            print("\n⚠️ PyQuotex necesita instalación o configuración.")
            
    except KeyboardInterrupt:
        print("\n🛑 Prueba interrumpida")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
