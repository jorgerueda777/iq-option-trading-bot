const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const config = require('../config/config');
const Logger = require('./utils/logger');
const IQOptionOTCConnector = require('./connectors/iqOptionOTC');
const IQOptionPythonBridge = require('./connectors/iqOptionPythonBridge');
const IQOptionSimulator = require('./connectors/iqOptionSimulator');
const AIPredictor = require('./ai/predictor_simple');
const TechnicalAnalyzer = require('./analysis/technicalAnalyzer');
const DataManager = require('./data/dataManager');
const HistoricalDataManager = require('./data/historicalDataManager');
const PredictionEngine = require('./engine/predictionEngine');

class IQOptionAIScanner {
  constructor() {
    this.app = express();
    this.server = http.createServer(this.app);
    this.io = socketIo(this.server);
    this.logger = new Logger('IQScanner');
    this.iqConnector = new IQOptionOTCConnector();
    // Inicializar Python Bridge y Blitz Bridge
    this.pythonBridge = new IQOptionPythonBridge(this.logger);
    const IQOptionBlitzBridge = require('./connectors/iqOptionBlitzBridge');
    this.blitzBridge = new IQOptionBlitzBridge(this.logger);
    this.simulator = new IQOptionSimulator(); // NUEVO: Simulador
    this.aiPredictor = new AIPredictor();
    this.technicalAnalyzer = new TechnicalAnalyzer();
    this.historicalDataManager = new HistoricalDataManager();
    this.dataManager = new DataManager();
    this.predictionEngine = new PredictionEngine(this.iqConnector, this.aiPredictor, this.technicalAnalyzer, this.dataManager, this.historicalDataManager);
    this.predictions = new Map();
    this.isRunning = false;
    this.scheduledOperations = new Map(); // Operaciones programadas
    this.activeOperations = new Map(); // Operaciones activas

    this.lastPredictions = new Map();
    
    // NUEVO: Configuración de trading automático CON LIMITADOR
    this.autoTradingEnabled = true; // Activar trading automático
    this.tradingConfig = {
      amount: 1, // $1 por operación
      minConfidence: 25, // ¡BAJADO! Confianza mínima para ejecutar (25%)
      maxSimultaneousOperations: 7, // Máximo 7 operaciones simultáneas (los 7 assets que funcionan)
      operationDuration: 60, // 60 segundos (1 minuto - opciones binarias OTC)
      enabledAssets: ['EURUSD-OTC', 'GBPUSD-OTC', 'GBPJPY-OTC', 'EURJPY-OTC', 'EURGBP-OTC', 'USDCHF-OTC', 'AUDCAD-OTC']
    };

    // Ya no necesitamos limitador - sistema continuo
  }

  async initialize() {
    try {
      this.logger.info('Iniciando IQ Option AI Scanner...');
      
      // Configurar Express
      this.setupExpress();
      
      // Configurar WebSocket
      this.setupWebSocket();
      
      // Iniciar servidor web inmediatamente
      this.listen();
      
      // Conectar a IQ Option en segundo plano
      this.connectInBackground();
      
      // SOLUCIÓN INMEDIATA: Configurar eventos aquí mismo
      this.logger.info(`🔄 DEBUG: Configurando listener para evento 'prediction' EN INITIALIZE`);
      this.predictionEngine.on('prediction', (prediction) => {
        this.handleNewPrediction(prediction);
        
        // ENVIAR SEÑAL AL SITIO WEB
        this.io.emit('prediction', prediction);
      
      // COORDINADOR SIMPLE: Detectar y ordenar ejecución
      if (this.autoTradingEnabled) {
        this.coordinateTrading(prediction);
      } 
      });
      
      this.predictionEngine.on('candle', (candleData) => {
        this.handleNewCandle(candleData);
      });
      
      this.logger.info('Scanner inicializado correctamente');
      
    } catch (error) {
      this.logger.error('Error al inicializar:', error);
      throw error;
    }
  }

  async connectInBackground() {
    try {
      // NUEVO: Inicializar datos históricos PRIMERO
      this.logger.info('📊 Inicializando datos históricos...');
      await this.historicalDataManager.initialize();
      
      // Conectar a IQ Option
      await this.iqConnector.connect();
      
      // CONECTAR PYTHON BRIDGE PARA OPERACIONES REALES
      this.logger.info('🐍 Conectando Python Bridge...');
      await this.pythonBridge.connect();
      this.logger.info('✅ Python Bridge conectado');
      
      // Inicializar IA
      await this.aiPredictor.initialize();
      
      // Inicializar motor de predicción (SOLO tiempo real + históricos existentes)
      this.logger.info('🚀 Iniciando motor de predicción híbrido...');
      this.logger.info('📊 Usando datos históricos existentes (2 años)');
      this.logger.info('⚡ Modo: TIEMPO REAL + BASE HISTÓRICA');
      
      this.predictionEngine.setupConnectorEvents();
      await this.predictionEngine.initializeCandleBuffersEmpty(); // Solo buffers vacíos
      this.predictionEngine.scheduleDailyHistoricalUpdate(); // Actualización diaria automática
      this.predictionEngine.startPeriodicAnalysis();
      
      this.logger.info('✅ Sistema híbrido completamente inicializado');
      this.logger.info('🔄 Datos reales + históricos listos para predicciones');
      
    } catch (error) {
      this.logger.error('Error conectando en segundo plano:', error);
    }
  }

  setupExpress() {
    this.app.use(express.static(path.join(__dirname, '../public')));
    this.app.use(express.json());
    
    // Rutas API
    this.app.get('/api/status', (req, res) => {
      res.json({
        status: this.isRunning ? 'running' : 'stopped',
        predictions: Array.from(this.predictions.values()),
        uptime: process.uptime()
      });
    });
    
    this.app.get('/api/predictions', (req, res) => {
      res.json(Array.from(this.predictions.values()));
    });
    
    this.app.post('/api/start', async (req, res) => {
      try {
        await this.start();
        res.json({ success: true, message: 'Scanner iniciado' });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    this.app.post('/api/stop', (req, res) => {
      this.stop();
      res.json({ success: true, message: 'Scanner detenido' });
    });
  }

  setupWebSocket() {
    this.io.on('connection', (socket) => {
      this.logger.info('Cliente conectado:', socket.id);
      
      // Enviar estado actual
      socket.emit('status', {
        isRunning: this.isRunning,
        predictions: Array.from(this.predictions.values())
      });
      
      socket.on('disconnect', () => {
        this.logger.info('Cliente desconectado:', socket.id);
      });
    });
  }

  async start() {
    if (this.isRunning) {
      this.logger.warn('El scanner ya está ejecutándose');
      return;
    }
    
    this.isRunning = true;
    this.logger.info('Iniciando análisis y predicciones...');
    
    // PRIMERO: Configurar eventos del motor de predicción (ANTES de iniciar)
    this.logger.info(`🔄 DEBUG: Configurando listener para evento 'prediction'`);
    this.logger.info(`🔄 DEBUG: predictionEngine es instancia de EventEmitter: ${this.predictionEngine instanceof require('events').EventEmitter}`);
    this.logger.info(`🔄 DEBUG: predictionEngine tiene método 'on': ${typeof this.predictionEngine.on}`);
    
    this.predictionEngine.on('prediction', (prediction) => {
      this.logger.info(`🔄 DEBUG: *** EVENTO 'prediction' RECIBIDO *** para ${prediction.asset} con ${(prediction.confidence * 100).toFixed(1)}%`);
      this.handleNewPrediction(prediction);
      
      // NUEVO: Ejecutar trading automático si está habilitado
      if (this.autoTradingEnabled) {
        this.logger.info(`🔄 DEBUG: autoTradingEnabled = ${this.autoTradingEnabled}, ejecutando...`);
        this.executeAutoTrade(prediction);
      } else {
        this.logger.info(`🔄 DEBUG: autoTradingEnabled = ${this.autoTradingEnabled}, NO ejecutando`);
      }
    });
    this.logger.info(`🔄 DEBUG: Listener para evento 'prediction' CONFIGURADO`);
    
    this.predictionEngine.on('candle', (candleData) => {
      this.handleNewCandle(candleData);
    });

    // DESPUÉS: Iniciar motor de predicción (DESPUÉS de configurar eventos)
    await this.predictionEngine.start();

    // Configurar eventos del conector IQ Option para cotizaciones en tiempo real
    this.iqConnector.on('quote', (quoteData) => {
      this.handleNewQuote(quoteData);
    });
    
    // Emitir estado a clientes conectados
    this.io.emit('scanner_started');
    
    // NUEVO: Monitorear conexión cada 30 segundos
    this.connectionMonitor = setInterval(() => {
      this.checkConnection();
    }, 30000);
  }
  
  // NUEVO: Verificar y mantener conexión
  async checkConnection() {
    try {
      if (!this.iqConnector.isConnectionActive()) {
        this.logger.warn('⚠️ Conexión perdida con IQ Option - Reconectando...');
        await this.iqConnector.connect();
        this.logger.info('✅ Reconexión automática exitosa');
      }
    } catch (error) {
      this.logger.error('❌ Error en verificación de conexión:', error);
    }
  }

  // NUEVO: Limpiar operaciones expiradas
  cleanExpiredOperations() {
    const now = Date.now();
    const expiredTime = 2 * 60 * 1000; // 2 minutos (más agresivo)
    
    let cleaned = 0;
    for (const [id, operation] of this.activeOperations) {
      if (now - operation.startTime > expiredTime) {
        this.logger.info(`🧹 LIMPIANDO operación expirada: ${id} - ${operation.asset} (${Math.round((now - operation.startTime) / 1000)}s)`);
        this.activeOperations.delete(id);
        cleaned++;
      }
    }
    
    if (cleaned > 0) {
      this.logger.info(`🧹 LIMPIEZA: Eliminadas ${cleaned} operaciones expiradas`);
    }
  }

  stop() {
    if (!this.isRunning) {
      this.logger.warn('El scanner no está ejecutándose');
      return;
    }
    
    this.isRunning = false;
    this.logger.info('Deteniendo scanner...');
    
    // Detener motor de predicción
    this.predictionEngine.stop();
    
    // Emitir estado a clientes conectados
    this.io.emit('scanner_stopped');
  }

  handleNewPrediction(prediction) {
    this.logger.info(`Nueva predicción para ${prediction.asset}:`, {
      direction: prediction.direction,
      confidence: prediction.confidence,
      timestamp: prediction.timestamp
    });
    
    // NUEVO: Log para debugging trading automático
    this.logger.info(`🤖 DEBUG: Evaluando para trading automático - ${prediction.asset} ${prediction.direction} (${(prediction.confidence * 100).toFixed(1)}%)`);
    this.logger.info(`🤖 DEBUG: autoTradingEnabled = ${this.autoTradingEnabled}`);
    
    // Guardar predicción
    this.predictions.set(prediction.id, prediction);
    this.lastPredictions.set(prediction.asset, prediction);
    
    // Emitir a clientes conectados
    this.io.emit('new_prediction', prediction);
    
    // Limpiar predicciones antiguas (mantener solo las últimas 100)
    if (this.predictions.size > 100) {
      const oldestKey = this.predictions.keys().next().value;
      this.predictions.delete(oldestKey);
    }
  }

  handleNewCandle(candleData) {
    // Emitir datos de vela a clientes conectados
    this.io.emit('new_candle', candleData);
    
    // Verificar predicciones anteriores
    this.checkPredictionAccuracy(candleData);
  }

  handleNewQuote(quoteData) {
    // Emitir cotizaciones en tiempo real al dashboard
    this.io.emit('new_quote', quoteData);
    
    this.logger.debug(`💱 Cotización en tiempo real: ${quoteData.asset} ${quoteData.bid}`);
  }

  checkPredictionAccuracy(candleData) {
    const asset = candleData.asset;
    const lastPrediction = this.lastPredictions.get(asset);
    
    if (lastPrediction && this.shouldCheckPrediction(lastPrediction, candleData)) {
      const isCorrect = this.evaluatePrediction(lastPrediction, candleData);
      
      // Actualizar estadísticas de precisión (método no implementado)
      // this.predictionEngine.updateAccuracy(lastPrediction.id, isCorrect);
      
      this.logger.info(`Predicción ${lastPrediction.id} para ${asset}: ${isCorrect ? 'CORRECTA' : 'INCORRECTA'}`);
      
      // Emitir resultado
      this.io.emit('prediction_result', {
        predictionId: lastPrediction.id,
        asset: asset,
        correct: isCorrect,
        actualDirection: candleData.close > candleData.open ? 'CALL' : 'PUT'
      });
    }
  }

  shouldCheckPrediction(prediction, candleData) {
    const predictionTime = new Date(prediction.timestamp);
    const candleTime = new Date(candleData.timestamp);
    const timeDiff = candleTime - predictionTime;
    
    // Verificar si la vela es la siguiente después de la predicción
    return timeDiff >= 60000 && timeDiff <= 120000; // Entre 1 y 2 minutos
  }

  evaluatePrediction(prediction, candleData) {
    const actualDirection = candleData.close > candleData.open ? 'CALL' : 'PUT';
    return prediction.direction === actualDirection;
  }

  async shutdown() {
    this.logger.info('Cerrando aplicación...');
    
    this.stop();
    
    // Cerrar conexiones
    await this.iqConnector.disconnect();
    await this.dataManager.close();
    
    // Cerrar servidor web si existe
    if (this.server) {
      this.server.close();
    }
    
    this.logger.info('Aplicación cerrada correctamente');
  }

  // COORDINADOR SIMPLE: Detectar señales y ejecutar operaciones simultáneas
  async coordinateTrading(prediction) {
    try {
      const { asset, confidence } = prediction;
      
      // Solo procesar assets de la configuración de 7
      const validAssets = ['EURUSD-OTC', 'GBPUSD-OTC', 'GBPJPY-OTC', 'EURJPY-OTC', 'EURGBP-OTC', 'USDCHF-OTC', 'AUDCAD-OTC'];
      
      if (!validAssets.includes(asset)) {
        return; // Asset no válido
      }
      
      // Verificar confianza mínima
      if ((confidence * 100) < this.tradingConfig.minConfidence) {
        return; // Confianza insuficiente
      }
      
      // Contar señales recientes (últimos 30 segundos pero ejecutar solo en segundos 55-59)
      const now = Date.now();
      const currentTime = new Date(now);
      const currentSeconds = currentTime.getSeconds();
      
      // Solo ejecutar en los últimos 5 segundos del minuto (55-59 segundos)
      const shouldExecute = currentSeconds >= 55 || currentSeconds <= 2;
      
      const recentSignals = Array.from(this.predictions.values()).filter(p => {
        const age = now - new Date(p.timestamp).getTime();
        return age < 30000 && // Últimos 30 segundos
               validAssets.includes(p.asset) && 
               (p.confidence * 100) >= this.tradingConfig.minConfidence;
      });
      
      // FILTRAR: Solo UNA señal por asset (la más reciente y con mayor confianza)
      const uniqueSignals = [];
      const assetMap = new Map();
      
      // Ordenar por timestamp (más reciente primero) y confianza (mayor primero)
      const sortedSignals = recentSignals.sort((a, b) => {
        const timeDiff = new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        if (timeDiff !== 0) return timeDiff;
        return (b.confidence * 100) - (a.confidence * 100);
      });
      
      // Tomar solo UNA señal por asset
      for (const signal of sortedSignals) {
        if (!assetMap.has(signal.asset)) {
          assetMap.set(signal.asset, signal);
          uniqueSignals.push(signal);
        }
      }
      
      const finalSignals = uniqueSignals;
      
      this.logger.info(`🎯 COORDINADOR: ${asset} señal detectada (${(confidence * 100).toFixed(1)}%) - Señales brutas: ${recentSignals.length} - Señales únicas: ${finalSignals.length} - Operaciones activas: ${this.activeOperations.size} - Segundos: ${currentSeconds} - Puede ejecutar: ${shouldExecute}`);
      
      // OPERAR EN TODOS LOS MINUTOS (PARES E IMPARES)
      const currentMinute = new Date().getMinutes();
      const nextMinute = (currentMinute + 1) % 60; // Minuto donde VA A EJECUTAR
      const canTradeAnyMinute = true; // ¡CAMBIO: Ahora opera SIEMPRE!
      
      this.logger.info(`⏰ COORDINADOR: Minuto actual: ${currentMinute}, Próximo: ${nextMinute} - ¡PUEDE OPERAR CUALQUIER MINUTO!`);
      
      // EJECUTAR cuando hay 1+ señales únicas, no hay operaciones activas, timing correcto
      if (finalSignals.length >= 1 && this.activeOperations.size === 0 && shouldExecute && canTradeAnyMinute) {
        
        // Marcar como ocupado inmediatamente para evitar ejecuciones múltiples
        this.activeOperations.set('executing', { type: 'preparing', startTime: Date.now() });
        
        const operationsToExecute = Math.min(finalSignals.length, 7); // Máximo 7
        this.logger.info(`🚀 COORDINADOR: ${finalSignals.length} señales únicas detectadas - EJECUTANDO ${operationsToExecute} OPERACIONES`);
        
        // CALCULAR TIMING EXACTO PARA SEGUNDO 54 DEL MINUTO ACTUAL
        const now = new Date();
        const currentSeconds = now.getSeconds();
        const currentMilliseconds = now.getMilliseconds();
        
        // EJECUTAR EN EL SEGUNDO 54 DEL MINUTO ACTUAL
        const targetTime = new Date(now);
        targetTime.setSeconds(54, 0); // Segundo 54, milisegundo 0
        
        // Si ya pasamos el segundo 54, programar para el próximo minuto
        if (currentSeconds >= 54) {
          targetTime.setMinutes(targetTime.getMinutes() + 1); // PRÓXIMO MINUTO (cualquiera)
          targetTime.setSeconds(54, 0);
        }
        
        const millisecondsToTarget = targetTime.getTime() - now.getTime();
        
        this.logger.info(`⏰ COORDINADOR: Ejecutar EXACTAMENTE en el SEGUNDO 54 en ${Math.round(millisecondsToTarget / 1000)}s (${targetTime.toLocaleTimeString()})`);
        this.logger.info(`🕐 DEBUG TIMING: Ahora=${currentSeconds}s, Target=54s, Delay=${Math.round(millisecondsToTarget)}ms`);
        
        // Programar ejecución EXACTA en el segundo 54
        setTimeout(async () => {
          try {
            const executeTime = new Date();
            const actualSeconds = executeTime.getSeconds();
            
            this.logger.info(`🎯 COORDINADOR: *** EJECUTANDO ${operationsToExecute} OPERACIONES AHORA *** ${executeTime.toLocaleTimeString()} (Segundos: ${actualSeconds})`);
            
            // Verificar que estamos ejecutando en el segundo 54
            if (actualSeconds < 52 || actualSeconds > 56) {
              this.logger.warn(`⚠️ COORDINADOR: Ejecución fuera de timing - Segundos: ${actualSeconds} (debería ser 54±2)`);
            } else {
              this.logger.info(`✅ COORDINADOR: Timing perfecto - Ejecutando en segundo ${actualSeconds}`);
            }
            
            // PREPARAR SEÑALES ÚNICAS PARA EJECUCIÓN DINÁMICA
            const signalsToExecute = finalSignals.slice(0, operationsToExecute).map(signal => ({
              asset: signal.asset,
              direction: signal.direction,
              confidence: signal.confidence
            }));
            
            // EJECUTAR OPERACIONES DINÁMICAS
            const result = await this.pythonBridge.executeDynamicTrades(signalsToExecute);
            
            if (result && result.success) {
              this.logger.info(`✅ COORDINADOR: ${operationsToExecute} operaciones ejecutadas exitosamente`);
              
              // ENVIAR EJECUCIONES AL SITIO WEB
              signalsToExecute.forEach(signal => {
                // Invertir la dirección para mostrar lo que realmente se ejecutó
                const executedDirection = signal.direction === 'CALL' ? 'PUT' : 'CALL';
                this.io.emit('execution', {
                  asset: signal.asset,
                  originalDirection: signal.direction,
                  direction: executedDirection,
                  confidence: signal.confidence,
                  timestamp: new Date().toISOString(),
                  inverted: true
                });
              });
              
              // Marcar como ocupado por la cantidad real de operaciones
              for (let i = 0; i < operationsToExecute; i++) {
                this.activeOperations.set(`simul_${Date.now()}_${i}`, {
                  asset: 'MULTIPLE',
                  direction: 'SIMULTANEOUS',
                  amount: 1,
                  confidence: 0.8,
                  startTime: Date.now(),
                  type: 'simultaneous_7'
                });
              }
              
              // LIBERAR INMEDIATAMENTE - NO ESPERAR
              // Las operaciones se ejecutan y el sistema queda libre para el siguiente minuto
              setTimeout(() => {
                this.activeOperations.clear();
                this.logger.info(`🔄 COORDINADOR: Sistema liberado - Listo para nuevas señales INMEDIATAMENTE`);
                
                // ENVIAR ESTADO AL SITIO WEB
                this.io.emit('status', {
                  activeOperations: 0,
                  message: 'Sistema listo - Sin espera'
                });
              }, 5000); // 5 segundos para dar tiempo a que se procesen
              
            } else {
              this.logger.error(`❌ COORDINADOR: Error ejecutando ${operationsToExecute} operaciones: ${result?.message || 'Error desconocido'}`);
            }
            
          } catch (error) {
            this.logger.error('❌ COORDINADOR: Error en ejecución:', error);
          }
        }, millisecondsToTarget);
        
      } else if (finalSignals.length >= 1 && shouldExecute && !isNextMinuteEven) {
        this.logger.info(`⏸️ COORDINADOR: NO EJECUTANDO - Próximo minuto IMPAR (${nextMinute}) - Solo opera en PARES`);
      }
      
    } catch (error) {
      this.logger.error('❌ COORDINADOR: Error:', error);
    }
  }


  // FUNCIÓN ELIMINADA: executeAutoTradeWith7Config
  // RAZÓN: Causaba ejecuciones SIN inversión
  // AHORA SOLO SE USA: executeDynamicTrades (con modo inverso)


  // FUNCIÓN ELIMINADA: executeAutoTrade
  // RAZÓN: También causaba ejecuciones SIN inversión
  // AHORA SOLO SE USA: executeDynamicTrades (con modo inverso)



  // Funciones de validación eliminadas - Ya no se necesitan
  // Solo se usa coordinateTrading() -> executeDynamicTrades() con modo inverso

  // Verificar resultado de la operación
  async checkOperationResult(operationId) {
    try {
      const operation = this.activeOperations.get(operationId);
      if (!operation) {
        return;
      }

      // Obtener resultado de IQ Option
      const result = await this.iqConnector.getOperationResult(operationId);
      
      if (result) {
        const isWin = result.win;
        const profit = result.profit || 0;
        
        this.logger.info(`📊 RESULTADO OPERACIÓN ${operationId}: ${isWin ? 'GANADA' : 'PERDIDA'} - Profit: $${profit}`);
        
        // Emitir resultado
        this.io.emit('auto_trade_result', {
          operationId: operationId,
          asset: operation.asset,
          direction: operation.direction,
          amount: operation.amount,
          result: isWin ? 'WIN' : 'LOSS',
          profit: profit,
          confidence: (operation.confidence * 100).toFixed(1),
          timestamp: new Date().toLocaleTimeString()
        });

        // Remover de operaciones activas
        this.activeOperations.delete(operationId);
      }

    } catch (error) {
      this.logger.error(`❌ Error verificando resultado de operación ${operationId}:`, error);
    }
  }

  setupWebSocketHandlers() {
    this.io.on('connection', (socket) => {
      this.logger.info('Cliente conectado al WebSocket');
      
      socket.on('disconnect', () => {
        this.logger.info('Cliente desconectado del WebSocket');
      });
    });
  }

  setupRoutes() {
    // Servir archivos estáticos
    this.app.use(express.static(path.join(__dirname, '../public')));
    
    // Ruta principal
    this.app.get('/', (req, res) => {
      res.sendFile(path.join(__dirname, '../public/index.html'));
    });
    
    // API para obtener predicciones
    this.app.get('/api/predictions', (req, res) => {
      const predictions = Array.from(this.predictions.values());
      res.json(predictions);
    });
  }

  listen() {
    const port = config.server.port;
    this.setupWebSocketHandlers();
    this.setupRoutes();
    
    // Sistema simplificado - una operación por asset
    
    this.server.listen(port, () => {
      this.logger.info(`Servidor iniciado en puerto ${port}`);
      this.logger.info(`Dashboard disponible en: http://localhost:${port}`);
    });
  }

  async start() {
    // Iniciar el motor de predicción
    await this.predictionEngine.start();
    this.logger.info('🚀 Motor de predicción iniciado');
  }

  // NUEVO: Verificar si ejecutar operaciones simultáneas
  async checkForSimultaneousTrading() {
    try {
      // Contar predicciones recientes (últimos 2 minutos) con alta confianza
      const now = Date.now();
      const recentPredictions = Array.from(this.predictions.values()).filter(p => {
        const predictionAge = now - new Date(p.timestamp).getTime();
        return predictionAge < 120000 && p.confidence >= 0.5; // 2 minutos y 50% confianza
      });

      // Si tenemos 3 o más predicciones de alta confianza, ejecutar operaciones simultáneas
      if (recentPredictions.length >= 3 && this.activeOperations.size < 3) {
        this.logger.info(`🚀 DETECTADAS ${recentPredictions.length} SEÑALES DE ALTA CONFIANZA - EJECUTANDO OPERACIONES SIMULTÁNEAS`);
        
        // Ejecutar operaciones simultáneas usando el script Python
        const result = await this.pythonBridge.executeSimultaneousTrades();
        
        if (result && result.success) {
          this.logger.info(`✅ OPERACIONES SIMULTÁNEAS EJECUTADAS EXITOSAMENTE`);
          
          // Emitir evento de operaciones simultáneas
          this.io.emit('simultaneous_trades_executed', {
            count: 7,
            timestamp: new Date().toLocaleTimeString(),
            predictions: recentPredictions.length
          });
          
          // Marcar operaciones como activas temporalmente
          for (let i = 0; i < 7; i++) {
            this.activeOperations.set(`simultaneous_${Date.now()}_${i}`, {
              asset: this.tradingConfig.enabledAssets[i] || 'MULTIPLE',
              direction: 'MIXED',
              amount: this.tradingConfig.amount,
              confidence: 0.8,
              startTime: Date.now(),
              type: 'simultaneous'
            });
          }
          
        } else {
          this.logger.error(`❌ Error ejecutando operaciones simultáneas: ${result?.message || 'Error desconocido'}`);
        }
      }
    } catch (error) {
      this.logger.error('❌ Error en checkForSimultaneousTrading:', error);
    }
  }

  // Sistema simplificado - no necesita limpieza de minutos procesados
}

// Función principal
async function main() {
  const scanner = new IQOptionAIScanner();
  
  // REGISTRAR COMO GLOBAL PARA QUE EL MOTOR DE PREDICCIÓN PUEDA ACCEDER
  global.mainScanner = scanner;
  
  try {
    await scanner.initialize();
    await scanner.start(); // NUEVO: Iniciar el scanner
    
    // Manejar cierre graceful
    process.on('SIGINT', async () => {
      console.log('\nRecibida señal SIGINT, cerrando aplicación...');
      await scanner.shutdown();
      process.exit(0);
    });
    
    process.on('SIGTERM', async () => {
      console.log('\nRecibida señal SIGTERM, cerrando aplicación...');
      await scanner.shutdown();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('Error fatal:', error);
    process.exit(1);
  }
}

// Ejecutar si es el archivo principal
if (require.main === module) {
  main();
}

module.exports = IQOptionAIScanner;
