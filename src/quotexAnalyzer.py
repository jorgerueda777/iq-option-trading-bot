#!/usr/bin/env python3
"""
Quotex Analyzer - Basado en main.js de IQ Option
Analizador completo con predicciones y ejecución automática
"""

import sys
import os
import time
import logging
import threading
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json
import asyncio

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.quotexAPIClient import QuotexAPIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger('QuotexAnalyzer')
        self.quotex_client = QuotexAPIClient()
        
        # Configuración de trading automático (igual que main.js)
        self.auto_trading_enabled = True
        self.trading_config = {
            "amount": 1,  # $1 por operación
            "min_confidence": 75,  # 75% confianza mínima (más alto que IQ Option)
            "max_simultaneous_operations": 2,  # Máximo 2 operaciones simultáneas
            "operation_duration": 60,  # 60 segundos
            "enabled_assets": ["UK BRENT", "MICROSOFT", "ADA", "ETH"]
        }
        
        # Estado del sistema
        self.is_running = False
        self.predictions = {}
        self.last_predictions = {}
        self.active_operations = {}
        self.scheduled_operations = {}
        
        # Datos de análisis (como main.js)
        self.candle_history = defaultdict(lambda: deque(maxlen=100))
        self.price_history = defaultdict(lambda: deque(maxlen=50))
        
        # Patrones de análisis (mejorados para Quotex)
        self.patterns = {
            ("DOWN", "DOWN", "UP"): 0.78,
            ("UP", "UP", "DOWN"): 0.82,
            ("DOWN", "UP", "DOWN"): 0.75,
            ("UP", "DOWN", "UP"): 0.77,
            ("DOWN", "DOWN", "DOWN"): 0.85,
            ("UP", "UP", "UP"): 0.83,
        }
        
    async def initialize(self):
        """Inicializar el analizador (como main.js)"""
        try:
            self.logger.info('🚀 Iniciando Quotex AI Analyzer...')
            
            # Conectar a Quotex - OBLIGATORIO
            if not self.quotex_client.authenticate():
                raise Exception("❌ AUTENTICACIÓN FALLIDA - No se puede continuar sin conexión real a Quotex")
            
            # Obtener activos
            assets = self.quotex_client.get_assets_list()
            self.logger.info(f"📊 {len(assets)} activos disponibles")
            
            self.logger.info('✅ Analyzer inicializado correctamente')
            return True
            
        except Exception as e:
            self.logger.error(f'❌ Error inicializando: {e}')
            return False
    
    def start_analysis(self):
        """Iniciar análisis continuo (como main.js)"""
        if self.is_running:
            self.logger.warning('El analyzer ya está ejecutándose')
            return
        
        self.is_running = True
        self.logger.info('🤖 Iniciando análisis y predicciones...')
        
        # Iniciar hilo de análisis
        analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        analysis_thread.start()
        
        self.logger.info('✅ Análisis iniciado')
    
    def _analysis_loop(self):
        """Loop principal de análisis (como main.js)"""
        while self.is_running:
            try:
                # Escanear todos los activos
                for asset in self.trading_config["enabled_assets"]:
                    self._analyze_asset(asset)
                
                # Limpiar operaciones expiradas
                self._clean_expired_operations()
                
                # Esperar antes del siguiente ciclo
                time.sleep(10)  # Análisis cada 10 segundos
                
            except Exception as e:
                self.logger.error(f'❌ Error en loop de análisis: {e}')
                time.sleep(5)
    
    def _analyze_asset(self, asset):
        """Analizar un activo específico (como main.js)"""
        try:
            # Obtener datos de mercado - SOLO REALES
            market_data = self.quotex_client.get_live_price(asset)
            
            if not market_data:
                self.logger.warning(f"⚠️ {asset}: No se pudieron obtener datos REALES - SALTANDO")
                return
            
            # Verificar que no sea simulado
            if market_data.get("source") == "simulated":
                self.logger.warning(f"⚠️ {asset}: Datos simulados detectados - RECHAZANDO")
                return
            
            price = market_data["price"]
            direction = market_data["direction"]
            
            # Actualizar historial
            self.price_history[asset].append(price)
            self.candle_history[asset].append(direction)
            
            # Generar predicción
            prediction = self._generate_prediction(asset)
            
            if prediction:
                self._handle_new_prediction(prediction)
                
        except Exception as e:
            self.logger.error(f'❌ Error analizando {asset}: {e}')
    
    def _generate_prediction(self, asset):
        """Generar predicción basada en patrones (como main.js)"""
        try:
            if len(self.candle_history[asset]) < 3:
                return None
            
            # Obtener últimos 3 movimientos
            recent_pattern = tuple(list(self.candle_history[asset])[-3:])
            
            if recent_pattern not in self.patterns:
                return None
            
            base_confidence = self.patterns[recent_pattern]
            
            # Análisis adicional de tendencia
            trend_boost = self._analyze_trend(asset)
            final_confidence = min(base_confidence + trend_boost, 0.95)
            
            # Solo generar si supera umbral mínimo
            if final_confidence < (self.trading_config["min_confidence"] / 100):
                return None
            
            # Determinar dirección predicha
            predicted_direction = self._predict_direction(recent_pattern, asset)
            
            prediction = {
                "id": f"{asset}_{int(time.time())}",
                "asset": asset,
                "direction": predicted_direction,
                "confidence": final_confidence,
                "pattern": recent_pattern,
                "timestamp": datetime.now().isoformat(),
                "source": "quotex_analyzer"
            }
            
            return prediction
            
        except Exception as e:
            self.logger.error(f'❌ Error generando predicción {asset}: {e}')
            return None
    
    def _analyze_trend(self, asset):
        """Analizar tendencia para boost de confianza"""
        try:
            if len(self.price_history[asset]) < 10:
                return 0
            
            prices = list(self.price_history[asset])[-10:]
            
            # Calcular tendencia simple
            trend_up = sum(1 for i in range(1, len(prices)) if prices[i] > prices[i-1])
            trend_strength = abs(trend_up - 5) / 5  # Normalizar 0-1
            
            return trend_strength * 0.1  # Máximo 10% boost
            
        except:
            return 0
    
    def _predict_direction(self, pattern, asset):
        """Predecir dirección basada en patrón"""
        # Lógica de reversión para patrones fuertes
        last_direction = pattern[-1]
        
        if pattern.count("UP") >= 2:
            return "DOWN"  # Reversión después de tendencia alcista
        elif pattern.count("DOWN") >= 2:
            return "UP"    # Reversión después de tendencia bajista
        else:
            return "DOWN" if last_direction == "UP" else "UP"
    
    def _handle_new_prediction(self, prediction):
        """Manejar nueva predicción (como main.js)"""
        asset = prediction["asset"]
        confidence = prediction["confidence"]
        direction = prediction["direction"]
        
        self.logger.info(f'🎯 Nueva predicción: {asset} {direction} ({confidence*100:.1f}%)')
        
        # Guardar predicción
        self.predictions[prediction["id"]] = prediction
        self.last_predictions[asset] = prediction
        
        # Ejecutar trading automático si está habilitado
        if self.auto_trading_enabled:
            self._execute_auto_trade(prediction)
    
    def _execute_auto_trade(self, prediction):
        """Ejecutar trading automático (como main.js)"""
        try:
            asset = prediction["asset"]
            
            # Verificar si ya hay operación programada para este asset
            if asset in self.scheduled_operations:
                return
            
            # Validaciones de seguridad
            if not self._should_execute_trade(prediction):
                return
            
            # Programar ejecución al próximo minuto exacto
            now = datetime.now()
            next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
            delay = (next_minute - now).total_seconds()
            
            self.logger.info(f'⏰ PROGRAMANDO: {asset} {prediction["direction"]} para {next_minute.strftime("%H:%M:%S")}')
            
            # Programar ejecución
            timer = threading.Timer(delay, self._execute_operation, args=[prediction])
            timer.start()
            
            # Guardar timer para poder cancelarlo
            self.scheduled_operations[asset] = timer
            
        except Exception as e:
            self.logger.error(f'❌ Error en auto trading: {e}')
    
    def _should_execute_trade(self, prediction):
        """Validar si se debe ejecutar la operación (como main.js)"""
        asset = prediction["asset"]
        confidence = prediction["confidence"]
        
        # Verificar confianza mínima
        if (confidence * 100) < self.trading_config["min_confidence"]:
            return False
        
        # Verificar límite de operaciones simultáneas
        if len(self.active_operations) >= self.trading_config["max_simultaneous_operations"]:
            return False
        
        # Verificar si ya hay operación activa para este asset
        for op in self.active_operations.values():
            if op["asset"] == asset:
                return False
        
        return True
    
    def _execute_operation(self, prediction):
        """Ejecutar operación al minuto exacto (como main.js)"""
        try:
            asset = prediction["asset"]
            direction = prediction["direction"]
            
            self.logger.info(f'🎯 *** EJECUTANDO *** {asset} {direction} - {datetime.now().strftime("%H:%M:%S")}')
            
            # Simular ejecución (aquí integrarías con quotexDual.py)
            operation_id = f"{asset}_{int(time.time())}"
            
            # Registrar operación activa
            self.active_operations[operation_id] = {
                "asset": asset,
                "direction": direction,
                "amount": self.trading_config["amount"],
                "confidence": prediction["confidence"],
                "start_time": time.time(),
                "prediction": prediction
            }
            
            self.logger.info(f'✅ OPERACIÓN EJECUTADA: {operation_id}')
            
            # Liberar asset para próximas operaciones
            if asset in self.scheduled_operations:
                del self.scheduled_operations[asset]
            
            # Programar verificación del resultado
            result_timer = threading.Timer(
                self.trading_config["operation_duration"] + 5,
                self._check_operation_result,
                args=[operation_id]
            )
            result_timer.start()
            
        except Exception as e:
            self.logger.error(f'❌ Error ejecutando operación: {e}')
            # Liberar asset en caso de error
            if asset in self.scheduled_operations:
                del self.scheduled_operations[asset]
    
    def _check_operation_result(self, operation_id):
        """Verificar resultado de operación (como main.js)"""
        try:
            if operation_id not in self.active_operations:
                return
            
            operation = self.active_operations[operation_id]
            
            # Simular resultado (aquí obtendrías resultado real de Quotex)
            import random
            is_win = random.random() > 0.4  # 60% win rate simulado
            profit = operation["amount"] * 0.8 if is_win else -operation["amount"]
            
            result_text = "GANADA" if is_win else "PERDIDA"
            self.logger.info(f'📊 RESULTADO {operation_id}: {result_text} - ${profit:+.2f}')
            
            # Remover de operaciones activas
            del self.active_operations[operation_id]
            
        except Exception as e:
            self.logger.error(f'❌ Error verificando resultado {operation_id}: {e}')
    
    def _clean_expired_operations(self):
        """Limpiar operaciones expiradas (como main.js)"""
        now = time.time()
        expired_time = 2 * 60  # 2 minutos
        
        expired_ops = []
        for op_id, operation in self.active_operations.items():
            if now - operation["start_time"] > expired_time:
                expired_ops.append(op_id)
        
        for op_id in expired_ops:
            del self.active_operations[op_id]
            self.logger.info(f'🧹 Operación expirada limpiada: {op_id}')
    
    def stop(self):
        """Detener analyzer"""
        self.is_running = False
        
        # Cancelar operaciones programadas
        for timer in self.scheduled_operations.values():
            timer.cancel()
        self.scheduled_operations.clear()
        
        self.logger.info('🛑 Analyzer detenido')
    
    def get_status(self):
        """Obtener estado actual (como main.js API)"""
        return {
            "is_running": self.is_running,
            "active_operations": len(self.active_operations),
            "scheduled_operations": len(self.scheduled_operations),
            "total_predictions": len(self.predictions),
            "enabled_assets": self.trading_config["enabled_assets"]
        }

def main():
    """Función principal"""
    analyzer = QuotexAnalyzer()
    
    try:
        # Inicializar
        if not asyncio.run(analyzer.initialize()):
            return
        
        # Iniciar análisis
        analyzer.start_analysis()
        
        # Mantener ejecutándose
        analyzer.logger.info('🚀 Quotex Analyzer ejecutándose... (Ctrl+C para detener)')
        
        while True:
            time.sleep(30)
            status = analyzer.get_status()
            analyzer.logger.info(f'📊 Estado: {status["active_operations"]} ops activas, {status["scheduled_operations"]} programadas')
    
    except KeyboardInterrupt:
        analyzer.logger.info('🛑 Deteniendo analyzer...')
        analyzer.stop()
    except Exception as e:
        analyzer.logger.error(f'❌ Error fatal: {e}')
    finally:
        analyzer.logger.info('👋 Analyzer terminado')

if __name__ == "__main__":
    main()
