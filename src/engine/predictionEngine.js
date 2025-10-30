const EventEmitter = require('events');
const moment = require('moment');
const config = require('../../config/config');
const Logger = require('../utils/logger');
const HistoricalDownloader = require('../utils/historicalDownloader');

class PredictionEngine extends EventEmitter {
  constructor(iqConnector, aiPredictor, technicalAnalyzer, dataManager, historicalDataManager = null) {
    super();
    this.logger = new Logger('PredictionEngine');
    this.iqConnector = iqConnector;
    this.aiPredictor = aiPredictor;
    this.technicalAnalyzer = technicalAnalyzer;
    this.dataManager = dataManager;
    this.historicalDataManager = historicalDataManager; // NUEVO: Datos históricos
    this.historicalDownloader = null;
    
    this.isRunning = false;
    this.intervals = new Map();
    this.candleBuffers = new Map();
    this.lastPredictions = new Map();
    this.cooldowns = new Map();
    
    // Estadísticas
    this.stats = {
      predictionsToday: 0,
      correctPredictions: 0,
      totalPredictions: 0,
      startTime: Date.now()
    };
  }

  async initialize() {
    try {
      this.logger.info('Inicializando motor de predicción...');
      
      // Inicializar descargador histórico
      this.historicalDownloader = new HistoricalDownloader(this.iqConnector);
      await this.historicalDownloader.initialize();
      this.logger.info('✅ Sistema histórico híbrido inicializado');
      
      // Configurar eventos del conector
      this.setupConnectorEvents();
      
      // Inicializar buffers de velas para cada activo
      await this.initializeCandleBuffers();
      
      // Programar actualización diaria automática
      this.scheduleDailyUpdates();
      
      // Programar reentrenamiento de IA
      this.aiPredictor.scheduleRetraining();
      
      this.logger.info('Motor de predicción inicializado');
      
    } catch (error) {
      this.logger.error('Error inicializando motor de predicción:', error);
      throw error;
    }
  }

  async start() {
    if (this.isRunning) {
      this.logger.warn('El motor ya está ejecutándose');
      return;
    }
    
    this.isRunning = true;
    this.logger.info('Iniciando motor de predicción...');
    
    try {
      // Suscribirse a datos de mercado para cada activo
      for (const asset of config.assets) {
        await this.subscribeToAsset(asset);
      }
      
      // Iniciar análisis periódico
      this.startPeriodicAnalysis();
      
      // Iniciar limpieza de datos antiguos
      this.startDataCleanup();
      
      this.logger.info('Motor de predicción iniciado exitosamente');
      
    } catch (error) {
      this.logger.error('Error iniciando motor de predicción:', error);
      this.isRunning = false;
      throw error;
    }
  }

  stop() {
    if (!this.isRunning) {
      this.logger.warn('El motor no está ejecutándose');
      return;
    }
    
    this.isRunning = false;
    this.logger.info('Deteniendo motor de predicción...');
    
    // Limpiar intervalos
    this.intervals.forEach(interval => clearInterval(interval));
    this.intervals.clear();
    
    // Limpiar buffers
    this.candleBuffers.clear();
    this.lastPredictions.clear();
    this.cooldowns.clear();
    
    this.logger.info('Motor de predicción detenido');
  }

  setupConnectorEvents() {
    // Manejar nuevas velas
    this.iqConnector.on('candle', (candleData) => {
      this.handleNewCandle(candleData);
    });
    
    // Manejar cotizaciones en tiempo real
    this.iqConnector.on('quote', (quoteData) => {
      this.handleNewQuote(quoteData);
    });
    
    // Manejar desconexiones
    this.iqConnector.on('connection_failed', () => {
      this.logger.error('Conexión perdida, pausando predicciones');
      this.pause();
    });
  }

  async initializeCandleBuffersEmpty() {
    const assets = ['EURUSD-OTC', 'GBPUSD-OTC', 'GBPJPY-OTC', 'EURJPY-OTC', 'EURGBP-OTC', 'USDCHF-OTC', 'AUDCAD-OTC'];
    
    for (const asset of assets) {
      try {
        this.logger.info(`📊 Inicializando buffer para ${asset} (solo tiempo real)...`);
        
        // Inicializar buffer vacío - se llenará SOLO con velas en tiempo real
        this.candleBuffers.set(asset, []);
        
        this.logger.info(`✅ Buffer listo para ${asset} - Datos históricos en SQLite`);
        
      } catch (error) {
        this.logger.error(`Error inicializando buffer para ${asset}:`, error);
        this.candleBuffers.set(asset, []);
      }
    }
  }

  // NUEVO: Programar actualización diaria automática
  scheduleDailyHistoricalUpdate() {
    try {
      this.logger.info('📅 Configurando actualización diaria automática...');
      
      // Ejecutar cada día a las 00:30 (después de que cierre el mercado)
      const now = new Date();
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 30, 0, 0); // 00:30:00
      
      const msUntilTomorrow = tomorrow.getTime() - now.getTime();
      
      setTimeout(() => {
        this.performDailyHistoricalUpdate();
        
        // Programar para repetir cada 24 horas
        setInterval(() => {
          this.performDailyHistoricalUpdate();
        }, 24 * 60 * 60 * 1000); // 24 horas
        
      }, msUntilTomorrow);
      
      this.logger.info(`📅 Actualización diaria programada para las 00:30 (en ${Math.round(msUntilTomorrow / 1000 / 60)} minutos)`);
      
    } catch (error) {
      this.logger.error('Error programando actualización diaria:', error);
    }
  }

  // NUEVO: Actualización diaria de datos históricos
  async performDailyHistoricalUpdate() {
    try {
      this.logger.info('🌅 INICIANDO ACTUALIZACIÓN DIARIA DE DATOS HISTÓRICOS');
      this.logger.info('📊 Agregando velas del día anterior a la base histórica...');
      
      const assets = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC'];
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      
      for (const asset of assets) {
        try {
          // Aquí se agregarían las velas del día anterior a la base de datos SQLite
          // Por ahora solo log, después implementaremos la lógica de guardado
          this.logger.info(`📈 Actualizando datos históricos para ${asset} (${yesterday.toDateString()})`);
          
          // TODO: Implementar guardado de velas del día anterior en SQLite
          // await this.saveYesterdayCandles(asset, yesterday);
          
        } catch (error) {
          this.logger.error(`❌ Error actualizando ${asset}:`, error.message);
        }
      }
      
      this.logger.info('✅ Actualización diaria completada - Base histórica actualizada');
      
    } catch (error) {
      this.logger.error('❌ Error en actualización diaria:', error);
    }
  }

  async subscribeToAsset(asset) {
    try {
      this.logger.info(`🔔 Suscribiéndose a ${asset}...`);
            // Inicializar con buffer vacío para inicio rápido
        this.candleBuffers.set(asset, []);
        
        // DESACTIVADO: No descargar datos históricos - usar SQLite existente
        this.logger.info(`📊 ${asset}: Usando datos históricos de SQLite + tiempo real`);
      
      // Suscribirse a velas del timeframe principal
      await this.iqConnector.subscribeToCandles(asset, config.timeframes.primary);
      
      // Suscribirse a cotizaciones en tiempo real
      await this.iqConnector.subscribeToQuotes(asset);
      
      this.logger.info(`✅ Suscrito completamente a ${asset}`);
      
    } catch (error) {
      this.logger.error(`❌ Error suscribiéndose a ${asset}:`, error);
    }
  }

  handleNewCandle(candleData) {
    try {
      const asset = candleData.asset;
      if (!this.candleBuffers.has(asset)) {
        this.candleBuffers.set(asset, []);
      }
      
      const buffer = this.candleBuffers.get(asset);
      
      // Agregar nueva vela al buffer
      buffer.push(candleData);
      
      // 💾 GUARDAR AUTOMÁTICAMENTE en base de datos histórica
      if (this.historicalDownloader) {
        this.historicalDownloader.saveRealtimeCandle(candleData);
      }
      
      // Mantener solo las velas necesarias en memoria
      const maxBuffer = config.ai.lookbackPeriod + 100;
      if (buffer.length > maxBuffer) {
        buffer.splice(0, buffer.length - maxBuffer);
      }
      
      // Emitir evento de nueva vela
      this.emit('candle', candleData);
      
      // Verificar si es momento de hacer una predicción
      this.checkPredictionTiming(asset, candleData);
      
      // Verificar predicciones anteriores
      this.checkPreviousPredictions(asset, candleData);
      
    } catch (error) {
      this.logger.error('Error manejando nueva vela:', error);
    }
  }

  // Programar actualizaciones diarias automáticas
  scheduleDailyUpdates() {
    // Ejecutar cada día a las 00:05 (5 minutos después de medianoche)
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 5, 0, 0); // 00:05:00

    const msUntilTomorrow = tomorrow.getTime() - now.getTime();

    setTimeout(() => {
      this.performDailyUpdate();
      
      // Programar para repetir cada 24 horas
      setInterval(() => {
        this.performDailyUpdate();
      }, 24 * 60 * 60 * 1000); // 24 horas
      
    }, msUntilTomorrow);

    this.logger.info(`📅 Actualización diaria programada para las 00:05 (en ${Math.round(msUntilTomorrow / 1000 / 60)} minutos)`);
  }

  // Realizar actualización diaria
  async performDailyUpdate() {
    try {
      this.logger.info('🌅 INICIANDO ACTUALIZACIÓN DIARIA AUTOMÁTICA');
      
      const assets = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC'];
      
      for (const asset of assets) {
        try {
          await this.historicalDownloader.checkForDailyUpdate(asset);
        } catch (error) {
          this.logger.error(`❌ Error actualizando ${asset}:`, error.message);
        }
      }
      
      this.logger.info('✅ Actualización diaria completada');
      
    } catch (error) {
      this.logger.error('❌ Error en actualización diaria:', error);
    }
  }

  handleNewQuote(quoteData) {
    // Emitir cotización para el dashboard en tiempo real
    this.emit('quote', quoteData);
  }

  async checkPredictionTiming(asset, candleData) {
    try {
      // VERIFICAR PRIMERO: ¿Ya hay operación programada para este asset?
      // Acceder al scanner principal para verificar operaciones programadas
      const scanner = global.mainScanner;
      if (scanner && scanner.scheduledOperations && scanner.scheduledOperations.has(asset)) {
        return; // FRENAR - Asset ocupado con operación programada
      }
      
      // NUEVA LÓGICA: SOLO UNA PREDICCIÓN POR MINUTO
      const now = moment();
      const currentMinute = `${now.hour()}:${now.minute()}`;
      const predictionKey = `${asset}_${currentMinute}`;
      
      // VERIFICAR: ¿Ya hicimos predicción para este asset en este minuto?
      if (this.lastPredictions.has(predictionKey)) {
        return; // SILENCIOSO - No spam logs
      }
      
      this.logger.info(`🎯 ANALIZANDO: ${asset} - Minuto ${currentMinute}`);
      
      // Generar predicción
      const prediction = await this.makePredictionOnce(asset);
      
      if (prediction) {
        // MARCAR MINUTO COMO PROCESADO PARA ESTE ASSET
        this.lastPredictions.set(predictionKey, {
          ...prediction,
          timestamp: Date.now(),
          minute: currentMinute
        });
        
        // LIMPIAR PREDICCIONES ANTIGUAS (más de 2 minutos)
        this.cleanOldPredictions();
      }
      
    } catch (error) {
      this.logger.error(`Error verificando timing de predicción para ${asset}:`, error);
    }
  }

  async makePredictionOnce(asset) {
    try {
      const buffer = this.candleBuffers.get(asset);
      
      // SISTEMA HÍBRIDO: Usar datos históricos + tiempo real (mínimo 1 vela)
      const minimumCandles = 1; // Solo necesitamos 1 vela porque tenemos 2 años históricos
      
      if (!buffer || buffer.length < minimumCandles) {
        this.logger.warn(`📊 Datos insuficientes para predicción de ${asset} (${buffer?.length || 0} velas) - Esperando primera vela`);
        return;
      }
      
      this.logger.info(`🔮 PREDICCIÓN HÍBRIDA ${asset}: ${buffer.length} velas reales + 2 años de datos históricos`);
      
      let prediction = null;
      
      // PRIORIDAD: Usar datos históricos (2 años) + tiempo real
      if (this.historicalDataManager) {
        try {
          // Tomar todas las velas disponibles para análisis multi-timeframe
          const realtimeCandles = buffer.slice();
          
          // Hacer predicción híbrida (tiempo real + histórico)
          prediction = await this.historicalDataManager.makePrediction(asset, realtimeCandles);
          
          this.logger.info(`🎯 PREDICCIÓN HÍBRIDA: ${prediction.direction} (${(prediction.confidence * 100).toFixed(1)}%) con 2 años de datos`);
          
        } catch (error) {
          this.logger.warn(`⚠️ Error en predicción híbrida para ${asset}, usando método tradicional:`, error.message);
        }
      } else {
        this.logger.warn(`⚠️ HistoricalDataManager no disponible para ${asset}`);
      }
      
      // Fallback: Usar método tradicional si no hay datos históricos
      if (!prediction) {
        // Realizar análisis técnico tradicional
        const technicalAnalysis = this.technicalAnalyzer.analyze(buffer, asset);
        
        if (!technicalAnalysis) {
          this.logger.warn(`Análisis técnico falló para ${asset}`);
          return;
        }
        
        // Generar predicción con IA tradicional
        prediction = await this.aiPredictor.predict(buffer, technicalAnalysis, asset);
        
        if (prediction) {
          this.logger.info(`📊 PREDICCIÓN TRADICIONAL: ${prediction.direction} (${(prediction.confidence * 100).toFixed(1)}%)`);
        }
      }
      
      if (!prediction) {
        this.logger.info(`No se generó predicción para ${asset} (confianza insuficiente)`);
        return;
      }
      
      // Normalizar formato de predicción
      if (prediction.direction === 'UP') {
        prediction.direction = 'CALL';
      } else if (prediction.direction === 'DOWN') {
        prediction.direction = 'PUT';
      }
      
      // Convertir confianza a decimal si está en porcentaje
      if (prediction.confidence > 1) {
        prediction.confidence = prediction.confidence / 100;
      }
      
      // Agregar información de timing para 1 minuto
      const now = moment();
      const nextMinute = moment().add(1, 'minute');
      
      prediction.currentTime = now.format('HH:mm');
      prediction.nextCandleTime = nextMinute.format('HH:mm');
      prediction.timeframe = '1m';
      prediction.analysisTime = now.format('HH:mm:ss');
      
      // Determinar color de la oportunidad
      prediction.color = prediction.direction === 'CALL' ? 'VERDE' : 'ROJA';
      prediction.signal = prediction.direction === 'CALL' ? 'COMPRA' : 'VENTA';
      
      // Agregar información híbrida si está disponible
      if (prediction.patternType) {
        prediction.hybridInfo = {
          patternType: prediction.patternType,
          greenCandles: prediction.greenCandles,
          redCandles: prediction.redCandles,
          historicalAccuracy: prediction.historicalAccuracy
        };
      }
      
      // Solo emitir si la confianza es suficiente (más permisivo para sistema híbrido)
      if (prediction.confidence >= 0.25) {
        // Guardar predicción
        this.lastPredictions.set(asset, prediction);
        
        // Emitir predicción
        this.logger.info(`🔄 DEBUG: EMITIENDO evento 'prediction' para ${asset} con confianza ${(prediction.confidence * 100).toFixed(1)}%`);
        this.emit('prediction', prediction);
        this.logger.info(`🔄 DEBUG: Evento 'prediction' EMITIDO para ${asset}`);
        
        this.logger.info(`🎯 PREDICCIÓN ${asset}: ${prediction.signal} ${prediction.color} - Próxima vela ${prediction.nextCandleTime} (${(prediction.confidence * 100).toFixed(1)}%)`);
      } else {
        this.logger.info(`⚠️ Confianza insuficiente para ${asset}: ${(prediction.confidence * 100).toFixed(1)}%`);
      }
      
    } catch (error) {
      this.logger.error(`Error generando predicción para ${asset}:`, error);
    }
  }

  // NUEVA: Limpiar predicciones antiguas para evitar acumulación
  cleanOldPredictions() {
    const now = Date.now();
    const twoMinutesAgo = now - (2 * 60 * 1000); // 2 minutos atrás
    
    let cleaned = 0;
    for (const [key, prediction] of this.lastPredictions) {
      if (prediction.timestamp < twoMinutesAgo) {
        this.lastPredictions.delete(key);
        cleaned++;
      }
    }
    
    if (cleaned > 0) {
      this.logger.info(`🧹 Limpiadas ${cleaned} predicciones antiguas`);
    }
  }

  validatePrediction(prediction, technicalAnalysis) {
    // Validar confianza mínima
    if (prediction.confidence < config.prediction.confidence_threshold) {
      return false;
    }
    
    // Validar que el análisis técnico esté alineado
    const technicalSignal = technicalAnalysis.signals?.overall;
    if (technicalSignal && technicalSignal !== prediction.direction.toLowerCase()) {
      // Si las señales no están alineadas, requerir mayor confianza
      if (prediction.confidence < 0.8) {
        return false;
      }
    }
    
    // Validar volatilidad esperada
    const expectedVolatility = technicalAnalysis.timeAnalysis?.volatilityExpected;
    if (expectedVolatility === 'low' && prediction.confidence < 0.75) {
      return false;
    }
    
    return true;
  }

  checkPreviousPredictions(asset, candleData) {
    const lastPrediction = this.lastPredictions.get(asset);
    
    if (!lastPrediction) {
      return;
    }
    
    const predictionTime = moment(lastPrediction.timestamp);
    const candleTime = moment(candleData.timestamp);
    const timeDiff = candleTime.diff(predictionTime, 'seconds');
    
    // Verificar si es la vela siguiente (aproximadamente 1 minuto después)
    if (timeDiff >= 50 && timeDiff <= 70) {
      const actualDirection = candleData.close > candleData.open ? 'CALL' : 'PUT';
      const isCorrect = lastPrediction.direction === actualDirection;
      
      // Actualizar resultado en IA
      this.aiPredictor.updatePredictionResult(lastPrediction.id, actualDirection);
      
      // Actualizar estadísticas
      if (isCorrect) {
        this.stats.correctPredictions++;
      }
      
      // Guardar resultado en base de datos
      this.dataManager.updatePredictionResult(lastPrediction.id, actualDirection, isCorrect);
      
      // Emitir evento de resultado
      this.emit('prediction_result', {
        predictionId: lastPrediction.id,
        asset: asset,
        predicted: lastPrediction.direction,
        actual: actualDirection,
        correct: isCorrect,
        confidence: lastPrediction.confidence
      });
      
      this.logger.info(`Resultado ${asset}: ${isCorrect ? 'CORRECTO' : 'INCORRECTO'} - Predicho: ${lastPrediction.direction}, Real: ${actualDirection}`);
    }
  }

  shouldMakePrediction(asset, currentMinute) {
    // Hacer predicciones cada minuto, pero con lógica específica
    const hour = moment().hour();
    
    // Evitar horas de baja volatilidad
    const lowVolatilityHours = [0, 1, 2, 3, 4, 5, 6, 23];
    if (lowVolatilityHours.includes(hour)) {
      return false;
    }
    
    // Predicciones más frecuentes en horas de alta volatilidad
    const highVolatilityHours = [8, 9, 13, 14, 15, 16, 21, 22];
    if (highVolatilityHours.includes(hour)) {
      return true; // Cada minuto
    }
    
    // Horas normales: cada 2-3 minutos
    return currentMinute % 2 === 0;
  }

  isInCooldown(asset) {
    const cooldownEnd = this.cooldowns.get(asset);
    return cooldownEnd && Date.now() < cooldownEnd;
  }

  setCooldown(asset) {
    const cooldownEnd = Date.now() + config.prediction.cooldown_period;
    this.cooldowns.set(asset, cooldownEnd);
  }

  hasReachedHourlyLimit() {
    const hourlyPredictions = this.getHourlyPredictionCount();
    return hourlyPredictions >= config.prediction.max_predictions_per_hour;
  }

  getHourlyPredictionCount() {
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    let count = 0;
    
    this.lastPredictions.forEach(prediction => {
      if (prediction.timestamp > oneHourAgo) {
        count++;
      }
    });
    
    return count;
  }

  startPeriodicAnalysis() {
    // Análisis cada 30 segundos
    const analysisInterval = setInterval(() => {
      if (this.isRunning) {
        this.performPeriodicAnalysis();
      }
    }, 30000);
    
    this.intervals.set('analysis', analysisInterval);
  }

  startDataCleanup() {
    // Limpieza cada hora
    const cleanupInterval = setInterval(() => {
      if (this.isRunning) {
        this.cleanupOldData();
      }
    }, 60 * 60 * 1000);
    
    this.intervals.set('cleanup', cleanupInterval);
  }

  performPeriodicAnalysis() {
    try {
      // Limpiar cooldowns expirados
      const now = Date.now();
      this.cooldowns.forEach((expiry, asset) => {
        if (now >= expiry) {
          this.cooldowns.delete(asset);
        }
      });
      
      // Emitir estadísticas actualizadas
      this.emit('stats_update', this.getStats());
      
    } catch (error) {
      this.logger.error('Error en análisis periódico:', error);
    }
  }

  cleanupOldData() {
    try {
      const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
      
      // Limpiar predicciones antiguas
      this.lastPredictions.forEach((prediction, asset) => {
        if (prediction.timestamp < oneDayAgo) {
          this.lastPredictions.delete(asset);
        }
      });
      
      this.logger.info('Limpieza de datos antiguos completada');
      
    } catch (error) {
      this.logger.error('Error en limpieza de datos:', error);
    }
  }

  updateStats(prediction) {
    this.stats.totalPredictions++;
    
    const today = moment().format('YYYY-MM-DD');
    const predictionDate = moment(prediction.timestamp).format('YYYY-MM-DD');
    
    if (predictionDate === today) {
      this.stats.predictionsToday++;
    }
  }

  getStats() {
    const accuracy = this.stats.totalPredictions > 0 ? 
      (this.stats.correctPredictions / this.stats.totalPredictions) * 100 : 0;
    
    const uptime = Date.now() - this.stats.startTime;
    
    return {
      ...this.stats,
      accuracy: accuracy,
      uptime: uptime,
      aiStats: this.aiPredictor.getAccuracyStats(),
      activeAssets: Array.from(this.candleBuffers.keys()),
      cooldowns: Array.from(this.cooldowns.keys())
    };
  }

  pause() {
    this.isRunning = false;
    this.logger.info('Motor de predicción pausado');
  }

  resume() {
    this.isRunning = true;
    this.logger.info('Motor de predicción reanudado');
  }

  // Método para obtener predicción manual
  async getManualPrediction(asset) {
    try {
      if (!this.candleBuffers.has(asset)) {
        throw new Error(`Activo ${asset} no disponible`);
      }
      
      return await this.makePredictionOnce(asset);
      
    } catch (error) {
      this.logger.error(`Error en predicción manual para ${asset}:`, error);
      throw error;
    }
  }
}

module.exports = PredictionEngine;
