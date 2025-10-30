#!/usr/bin/env python3
"""
Test Trading Operations - Prueba de Operaciones Automáticas
Ejecuta operaciones de compra/venta para probar si el sistema funciona
"""

import sys
import json
import time
import logging
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class TradingTester:
    def __init__(self):
        self.logger = logging
        self.operations_executed = 0
        self.operations_successful = 0
        self.operations_failed = 0
        
    def test_blitz_operation(self, asset, amount, direction):
        """Probar operación usando IQ Option Blitz"""
        try:
            self.logger.info(f"🎯 PROBANDO OPERACIÓN: {asset} {direction} ${amount}")
            
            # Ejecutar operación usando la API pura (SIN SELENIUM)
            cmd = [
                "python", 
                "iq_option_pure_api.py", 
                "buy", 
                asset, 
                str(amount), 
                direction
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # 2 minutos
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout.strip())
                    if response.get('success'):
                        self.logger.info(f"✅ OPERACIÓN EXITOSA: {asset} {direction}")
                        self.operations_successful += 1
                        return True
                    else:
                        self.logger.error(f"❌ OPERACIÓN FALLÓ: {response.get('message', 'Unknown error')}")
                        self.operations_failed += 1
                        return False
                except json.JSONDecodeError:
                    self.logger.info(f"📄 Respuesta: {result.stdout}")
                    if "ejecutada" in result.stdout.lower() or "exitosa" in result.stdout.lower():
                        self.operations_successful += 1
                        return True
                    else:
                        self.operations_failed += 1
                        return False
            else:
                self.logger.error(f"❌ Error ejecutando comando: {result.stderr}")
                self.operations_failed += 1
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en operación: {e}")
            self.operations_failed += 1
            return False
        finally:
            self.operations_executed += 1
    
    def test_multiple_operations(self):
        """Probar múltiples operaciones en diferentes activos"""
        test_operations = [
            {"asset": "EURUSD-OTC", "amount": 1, "direction": "CALL"},
            {"asset": "EURUSD-OTC", "amount": 1, "direction": "PUT"},
            {"asset": "GBPUSD-OTC", "amount": 1, "direction": "CALL"},
            {"asset": "GBPUSD-OTC", "amount": 1, "direction": "PUT"},
            {"asset": "USDJPY-OTC", "amount": 1, "direction": "CALL"},
            {"asset": "AUDUSD-OTC", "amount": 1, "direction": "PUT"}
        ]
        
        self.logger.info("🚀 INICIANDO PRUEBAS DE OPERACIONES MÚLTIPLES")
        self.logger.info(f"📊 Total de operaciones a probar: {len(test_operations)}")
        
        for i, op in enumerate(test_operations, 1):
            self.logger.info(f"\n--- OPERACIÓN {i}/{len(test_operations)} ---")
            
            success = self.test_blitz_operation(
                op["asset"], 
                op["amount"], 
                op["direction"]
            )
            
            if success:
                self.logger.info(f"✅ Operación {i} EXITOSA")
            else:
                self.logger.info(f"❌ Operación {i} FALLÓ")
            
            # Esperar entre operaciones
            if i < len(test_operations):
                self.logger.info("⏳ Esperando 3 segundos...")
                time.sleep(3)
        
        # Mostrar resumen
        self.show_summary()
    
    def test_rapid_fire(self, count=10):
        """Prueba rápida de múltiples operaciones"""
        assets = ["EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC"]
        directions = ["CALL", "PUT"]
        
        self.logger.info(f"🔥 PRUEBA RÁPIDA: {count} operaciones")
        
        for i in range(count):
            asset = assets[i % len(assets)]
            direction = directions[i % len(directions)]
            
            self.logger.info(f"\n🎯 OPERACIÓN RÁPIDA {i+1}/{count}")
            self.test_blitz_operation(asset, 1, direction)
            
            time.sleep(1)  # 1 segundo entre operaciones
        
        self.show_summary()
    
    def test_single_operation(self, asset="EURUSD-OTC", direction="CALL"):
        """Probar una sola operación"""
        self.logger.info("🎯 PRUEBA DE OPERACIÓN ÚNICA")
        success = self.test_blitz_operation(asset, 1, direction)
        
        if success:
            self.logger.info("✅ PRUEBA EXITOSA - El sistema puede ejecutar operaciones")
        else:
            self.logger.info("❌ PRUEBA FALLÓ - Revisar configuración")
        
        self.show_summary()
    
    def show_summary(self):
        """Mostrar resumen de resultados"""
        self.logger.info("\n" + "="*50)
        self.logger.info("📊 RESUMEN DE PRUEBAS")
        self.logger.info("="*50)
        self.logger.info(f"🎯 Operaciones ejecutadas: {self.operations_executed}")
        self.logger.info(f"✅ Operaciones exitosas: {self.operations_successful}")
        self.logger.info(f"❌ Operaciones fallidas: {self.operations_failed}")
        
        if self.operations_executed > 0:
            success_rate = (self.operations_successful / self.operations_executed) * 100
            self.logger.info(f"📈 Tasa de éxito: {success_rate:.1f}%")
            
            if success_rate > 0:
                self.logger.info("🎉 ¡EL SISTEMA PUEDE EJECUTAR OPERACIONES!")
            else:
                self.logger.info("⚠️ EL SISTEMA NO PUEDE EJECUTAR OPERACIONES")
        
        self.logger.info("="*50)

def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python test_trading_operations.py single [ASSET] [DIRECTION]")
        print("  python test_trading_operations.py multiple")
        print("  python test_trading_operations.py rapid [COUNT]")
        print("")
        print("Ejemplos:")
        print("  python test_trading_operations.py single EURUSD-OTC CALL")
        print("  python test_trading_operations.py multiple")
        print("  python test_trading_operations.py rapid 5")
        return
    
    command = sys.argv[1].lower()
    tester = TradingTester()
    
    try:
        if command == "single":
            asset = sys.argv[2] if len(sys.argv) > 2 else "EURUSD-OTC"
            direction = sys.argv[3] if len(sys.argv) > 3 else "CALL"
            tester.test_single_operation(asset, direction)
            
        elif command == "multiple":
            tester.test_multiple_operations()
            
        elif command == "rapid":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            tester.test_rapid_fire(count)
            
        else:
            print(f"Comando no reconocido: {command}")
            
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
        tester.show_summary()
    except Exception as e:
        print(f"❌ Error: {e}")
        tester.show_summary()

if __name__ == "__main__":
    main()
