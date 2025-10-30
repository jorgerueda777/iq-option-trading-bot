const mongoose = require('mongoose');
const fs = require('fs').promises;
const path = require('path');
const Logger = require('../utils/logger');
const config = require('../../config/config');

// Esquemas de MongoDB
const CandleSchema = new mongoose.Schema({
  asset: { type: String, required: true, index: true },
  timestamp: { type: Date, required: true, index: true },
  open: { type: Number, required: true },
  high: { type: Number, required: true },
  low: { type: Number, required: true },
  close: { type: Number, required: true },
  volume: { type: Number, default: 0 },
  timeframe: { type: Number, default: 60 }
}, {
  timestamps: true
});

const PredictionSchema = new mongoose.Schema({
  predictionId: { type: String, required: true, unique: true, index: true },
  asset: { type: String, required: true, index: true },
  direction: { type: String, enum: ['CALL', 'PUT'], required: true },
  confidence: { type: Number, required: true, min: 0, max: 1 },
  callProbability: { type: Number, required: true },
  putProbability: { type: Number, required: true },
  timestamp: { type: Date, required: true, index: true },
  hour: { type: Number, required: true },
  minute: { type: Number, required: true },
  technicalScore: { type: Number },
  indicators: {
    rsi: Number,
    macd_signal: String,
    bollinger_position: Number,
    overall_signal: String,
    confidence: Number
  },
  historicalAccuracy: { type: Number },
  result: {
    actual: { type: String, enum: ['CALL', 'PUT'] },
    correct: { type: Boolean },
    verifiedAt: { type: Date }
  }
}, {
  timestamps: true
});

const PerformanceSchema = new mongoose.Schema({
  date: { type: Date, required: true, index: true },
  asset: { type: String, required: true, index: true },
  hour: { type: Number, required: true },
  totalPredictions: { type: Number, default: 0 },
  correctPredictions: { type: Number, default: 0 },
  accuracy: { type: Number, default: 0 },
  avgConfidence: { type: Number, default: 0 },
  profitability: { type: Number, default: 0 }
}, {
  timestamps: true
});

class DataManager {
  constructor() {
    this.logger = new Logger('DataManager');
    this.isConnected = false;
    this.models = {};
    
    // Configurar índices compuestos
    CandleSchema.index({ asset: 1, timestamp: 1 });
    PredictionSchema.index({ asset: 1, timestamp: 1 });
    PerformanceSchema.index({ date: 1, asset: 1, hour: 1 });
  }

  async initialize() {
    try {
      this.logger.info('Inicializando gestor de datos...');
      
      // Conectar a MongoDB
      await this.connectToDatabase();
      
      // Inicializar modelos
      this.initializeModels();
      
      // Crear directorios locales si no existen
      await this.createDirectories();
      
      this.logger.info('Gestor de datos inicializado correctamente');
      
    } catch (error) {
      this.logger.error('Error inicializando gestor de datos:', error);
      throw error;
    }
  }

  async connectToDatabase() {
    try {
      if (config.database.mongodb) {
        await mongoose.connect(config.database.mongodb, {
          useNewUrlParser: true,
          useUnifiedTopology: true,
          maxPoolSize: 10,
          serverSelectionTimeoutMS: 5000,
          socketTimeoutMS: 45000,
        });
        
        this.isConnected = true;
        this.logger.info('Conectado a MongoDB');
        
        // Configurar eventos de conexión
        mongoose.connection.on('error', (error) => {
          this.logger.error('Error de conexión MongoDB:', error);
        });
        
        mongoose.connection.on('disconnected', () => {
          this.logger.warn('Desconectado de MongoDB');
          this.isConnected = false;
        });
        
        mongoose.connection.on('reconnected', () => {
          this.logger.info('Reconectado a MongoDB');
          this.isConnected = true;
        });
        
      } else {
        this.logger.warn('MongoDB no configurado, usando almacenamiento local');
      }
      
    } catch (error) {
      this.logger.error('Error conectando a MongoDB:', error);
      this.logger.info('Continuando con almacenamiento local');
    }
  }

  initializeModels() {
    if (this.isConnected) {
      this.models.Candle = mongoose.model('Candle', CandleSchema);
      this.models.Prediction = mongoose.model('Prediction', PredictionSchema);
      this.models.Performance = mongoose.model('Performance', PerformanceSchema);
      
      this.logger.info('Modelos de MongoDB inicializados');
    }
  }

  async createDirectories() {
    const directories = [
      path.resolve('./data/candles'),
      path.resolve('./data/predictions'),
      path.resolve('./data/performance'),
      path.resolve('./data/backups')
    ];
    
    for (const dir of directories) {
      try {
        await fs.mkdir(dir, { recursive: true });
      } catch (error) {
        this.logger.error(`Error creando directorio ${dir}:`, error);
      }
    }
  }

  async saveCandle(candleData) {
    try {
      if (this.isConnected && this.models.Candle) {
        // Guardar en MongoDB
        const candle = new this.models.Candle({
          asset: candleData.asset,
          timestamp: new Date(candleData.timestamp),
          open: candleData.open,
          high: candleData.high,
          low: candleData.low,
          close: candleData.close,
          volume: candleData.volume || 0,
          timeframe: candleData.timeframe || 60
        });
        
        await candle.save();
      }
      
      // Guardar también localmente como backup
      await this.saveCandleLocally(candleData);
      
    } catch (error) {
      this.logger.error('Error guardando vela:', error);
      // Intentar guardar localmente si MongoDB falla
      await this.saveCandleLocally(candleData);
    }
  }

  async saveCandleLocally(candleData) {
    try {
      const date = new Date(candleData.timestamp).toISOString().split('T')[0];
      const filename = `${candleData.asset}_${date}.json`;
      const filepath = path.resolve(`./data/candles/${filename}`);
      
      let existingData = [];
      try {
        const fileContent = await fs.readFile(filepath, 'utf8');
        existingData = JSON.parse(fileContent);
      } catch {
        // Archivo no existe, crear nuevo
      }
      
      existingData.push(candleData);
      
      // Mantener solo las últimas 1000 velas por archivo
      if (existingData.length > 1000) {
        existingData = existingData.slice(-1000);
      }
      
      await fs.writeFile(filepath, JSON.stringify(existingData, null, 2));
      
    } catch (error) {
      this.logger.error('Error guardando vela localmente:', error);
    }
  }

  async savePrediction(prediction) {
    try {
      if (this.isConnected && this.models.Prediction) {
        // Guardar en MongoDB
        const pred = new this.models.Prediction({
          predictionId: prediction.id,
          asset: prediction.asset,
          direction: prediction.direction,
          confidence: prediction.confidence,
          callProbability: prediction.callProbability,
          putProbability: prediction.putProbability,
          timestamp: new Date(prediction.timestamp),
          hour: prediction.hour,
          minute: prediction.minute,
          technicalScore: prediction.technicalScore,
          indicators: prediction.indicators,
          historicalAccuracy: prediction.historicalAccuracy
        });
        
        await pred.save();
      }
      
      // Guardar también localmente
      await this.savePredictionLocally(prediction);
      
      this.logger.info(`Predicción ${prediction.id} guardada`);
      
    } catch (error) {
      this.logger.error('Error guardando predicción:', error);
      await this.savePredictionLocally(prediction);
    }
  }

  async savePredictionLocally(prediction) {
    try {
      const date = new Date(prediction.timestamp).toISOString().split('T')[0];
      const filename = `predictions_${date}.json`;
      const filepath = path.resolve(`./data/predictions/${filename}`);
      
      let existingData = [];
      try {
        const fileContent = await fs.readFile(filepath, 'utf8');
        existingData = JSON.parse(fileContent);
      } catch {
        // Archivo no existe
      }
      
      existingData.push(prediction);
      await fs.writeFile(filepath, JSON.stringify(existingData, null, 2));
      
    } catch (error) {
      this.logger.error('Error guardando predicción localmente:', error);
    }
  }

  async updatePredictionResult(predictionId, actualResult, isCorrect) {
    try {
      if (this.isConnected && this.models.Prediction) {
        // Actualizar en MongoDB
        await this.models.Prediction.updateOne(
          { predictionId: predictionId },
          {
            $set: {
              'result.actual': actualResult,
              'result.correct': isCorrect,
              'result.verifiedAt': new Date()
            }
          }
        );
      }
      
      // Actualizar también localmente
      await this.updatePredictionResultLocally(predictionId, actualResult, isCorrect);
      
      this.logger.info(`Resultado de predicción ${predictionId} actualizado: ${isCorrect ? 'CORRECTO' : 'INCORRECTO'}`);
      
    } catch (error) {
      this.logger.error('Error actualizando resultado de predicción:', error);
    }
  }

  async updatePredictionResultLocally(predictionId, actualResult, isCorrect) {
    try {
      // Buscar en archivos de predicciones recientes
      const today = new Date();
      const dates = [];
      
      // Buscar en los últimos 3 días
      for (let i = 0; i < 3; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
      }
      
      for (const date of dates) {
        const filename = `predictions_${date}.json`;
        const filepath = path.resolve(`./data/predictions/${filename}`);
        
        try {
          const fileContent = await fs.readFile(filepath, 'utf8');
          const predictions = JSON.parse(fileContent);
          
          const predictionIndex = predictions.findIndex(p => p.id === predictionId);
          if (predictionIndex !== -1) {
            predictions[predictionIndex].result = {
              actual: actualResult,
              correct: isCorrect,
              verifiedAt: new Date().toISOString()
            };
            
            await fs.writeFile(filepath, JSON.stringify(predictions, null, 2));
            return;
          }
        } catch {
          // Archivo no existe o error de lectura
        }
      }
      
    } catch (error) {
      this.logger.error('Error actualizando resultado localmente:', error);
    }
  }

  async getCandles(asset, startTime, endTime, limit = 1000) {
    try {
      if (this.isConnected && this.models.Candle) {
        // Obtener de MongoDB
        const candles = await this.models.Candle
          .find({
            asset: asset,
            timestamp: {
              $gte: new Date(startTime),
              $lte: new Date(endTime)
            }
          })
          .sort({ timestamp: 1 })
          .limit(limit)
          .lean();
        
        return candles.map(candle => ({
          asset: candle.asset,
          timestamp: candle.timestamp.getTime(),
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
          volume: candle.volume,
          timeframe: candle.timeframe
        }));
      }
      
      // Fallback a archivos locales
      return await this.getCandlesLocally(asset, startTime, endTime, limit);
      
    } catch (error) {
      this.logger.error('Error obteniendo velas:', error);
      return await this.getCandlesLocally(asset, startTime, endTime, limit);
    }
  }

  async getCandlesLocally(asset, startTime, endTime, limit) {
    try {
      const candles = [];
      const start = new Date(startTime);
      const end = new Date(endTime);
      
      // Iterar por días en el rango
      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        const date = d.toISOString().split('T')[0];
        const filename = `${asset}_${date}.json`;
        const filepath = path.resolve(`./data/candles/${filename}`);
        
        try {
          const fileContent = await fs.readFile(filepath, 'utf8');
          const dayCandles = JSON.parse(fileContent);
          
          // Filtrar por rango de tiempo
          const filteredCandles = dayCandles.filter(candle => {
            const candleTime = new Date(candle.timestamp);
            return candleTime >= start && candleTime <= end;
          });
          
          candles.push(...filteredCandles);
          
        } catch {
          // Archivo no existe
        }
      }
      
      // Ordenar por timestamp y limitar
      candles.sort((a, b) => a.timestamp - b.timestamp);
      return candles.slice(0, limit);
      
    } catch (error) {
      this.logger.error('Error obteniendo velas localmente:', error);
      return [];
    }
  }

  async getPredictions(asset = null, startTime = null, endTime = null, limit = 100) {
    try {
      if (this.isConnected && this.models.Prediction) {
        const query = {};
        
        if (asset) query.asset = asset;
        if (startTime && endTime) {
          query.timestamp = {
            $gte: new Date(startTime),
            $lte: new Date(endTime)
          };
        }
        
        const predictions = await this.models.Prediction
          .find(query)
          .sort({ timestamp: -1 })
          .limit(limit)
          .lean();
        
        return predictions;
      }
      
      // Fallback a archivos locales
      return await this.getPredictionsLocally(asset, startTime, endTime, limit);
      
    } catch (error) {
      this.logger.error('Error obteniendo predicciones:', error);
      return await this.getPredictionsLocally(asset, startTime, endTime, limit);
    }
  }

  async getPredictionsLocally(asset, startTime, endTime, limit) {
    try {
      const predictions = [];
      const today = new Date();
      
      // Buscar en los últimos 7 días
      for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        
        const filename = `predictions_${dateStr}.json`;
        const filepath = path.resolve(`./data/predictions/${filename}`);
        
        try {
          const fileContent = await fs.readFile(filepath, 'utf8');
          const dayPredictions = JSON.parse(fileContent);
          
          // Filtrar por criterios
          const filtered = dayPredictions.filter(pred => {
            if (asset && pred.asset !== asset) return false;
            if (startTime && endTime) {
              const predTime = new Date(pred.timestamp);
              return predTime >= new Date(startTime) && predTime <= new Date(endTime);
            }
            return true;
          });
          
          predictions.push(...filtered);
          
        } catch {
          // Archivo no existe
        }
      }
      
      // Ordenar por timestamp descendente y limitar
      predictions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      return predictions.slice(0, limit);
      
    } catch (error) {
      this.logger.error('Error obteniendo predicciones localmente:', error);
      return [];
    }
  }

  async getPerformanceStats(asset = null, period = 'day') {
    try {
      const now = new Date();
      let startTime;
      
      switch (period) {
        case 'hour':
          startTime = new Date(now.getTime() - 60 * 60 * 1000);
          break;
        case 'day':
          startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
          break;
        case 'week':
          startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case 'month':
          startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        default:
          startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      }
      
      const predictions = await this.getPredictions(asset, startTime, now);
      
      // Calcular estadísticas
      const stats = {
        total: predictions.length,
        correct: 0,
        accuracy: 0,
        avgConfidence: 0,
        byAsset: {},
        byHour: {}
      };
      
      let totalConfidence = 0;
      
      predictions.forEach(pred => {
        if (pred.result && pred.result.correct !== undefined) {
          if (pred.result.correct) {
            stats.correct++;
          }
        }
        
        totalConfidence += pred.confidence;
        
        // Estadísticas por activo
        if (!stats.byAsset[pred.asset]) {
          stats.byAsset[pred.asset] = { total: 0, correct: 0, accuracy: 0 };
        }
        stats.byAsset[pred.asset].total++;
        if (pred.result && pred.result.correct) {
          stats.byAsset[pred.asset].correct++;
        }
        
        // Estadísticas por hora
        const hour = pred.hour;
        if (!stats.byHour[hour]) {
          stats.byHour[hour] = { total: 0, correct: 0, accuracy: 0 };
        }
        stats.byHour[hour].total++;
        if (pred.result && pred.result.correct) {
          stats.byHour[hour].correct++;
        }
      });
      
      // Calcular porcentajes
      if (stats.total > 0) {
        stats.accuracy = (stats.correct / stats.total) * 100;
        stats.avgConfidence = (totalConfidence / stats.total) * 100;
      }
      
      // Calcular accuracy por activo
      Object.keys(stats.byAsset).forEach(asset => {
        const assetStats = stats.byAsset[asset];
        if (assetStats.total > 0) {
          assetStats.accuracy = (assetStats.correct / assetStats.total) * 100;
        }
      });
      
      // Calcular accuracy por hora
      Object.keys(stats.byHour).forEach(hour => {
        const hourStats = stats.byHour[hour];
        if (hourStats.total > 0) {
          hourStats.accuracy = (hourStats.correct / hourStats.total) * 100;
        }
      });
      
      return stats;
      
    } catch (error) {
      this.logger.error('Error obteniendo estadísticas de rendimiento:', error);
      return null;
    }
  }

  async createBackup() {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupDir = path.resolve(`./data/backups/backup_${timestamp}`);
      
      await fs.mkdir(backupDir, { recursive: true });
      
      // Copiar archivos de datos
      const dataDirs = ['candles', 'predictions', 'performance'];
      
      for (const dir of dataDirs) {
        const sourceDir = path.resolve(`./data/${dir}`);
        const targetDir = path.resolve(`${backupDir}/${dir}`);
        
        try {
          await fs.mkdir(targetDir, { recursive: true });
          const files = await fs.readdir(sourceDir);
          
          for (const file of files) {
            const sourcePath = path.join(sourceDir, file);
            const targetPath = path.join(targetDir, file);
            await fs.copyFile(sourcePath, targetPath);
          }
        } catch {
          // Directorio no existe
        }
      }
      
      this.logger.info(`Backup creado en: ${backupDir}`);
      return backupDir;
      
    } catch (error) {
      this.logger.error('Error creando backup:', error);
      throw error;
    }
  }

  async close() {
    try {
      if (this.isConnected) {
        await mongoose.connection.close();
        this.isConnected = false;
        this.logger.info('Conexión a base de datos cerrada');
      }
    } catch (error) {
      this.logger.error('Error cerrando conexión:', error);
    }
  }
}

module.exports = DataManager;
