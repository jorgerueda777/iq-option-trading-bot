const winston = require('winston');
const path = require('path');
const config = require('../../config/config');

class Logger {
  constructor(component = 'App') {
    this.component = component;
    this.logger = winston.createLogger({
      level: config.logging.level,
      format: winston.format.combine(
        winston.format.timestamp({
          format: 'YYYY-MM-DD HH:mm:ss'
        }),
        winston.format.errors({ stack: true }),
        winston.format.printf(({ level, message, timestamp, stack, ...meta }) => {
          let log = `${timestamp} [${level.toUpperCase()}] [${this.component}]: ${message}`;
          
          if (Object.keys(meta).length > 0) {
            try {
              log += ` ${JSON.stringify(meta, null, 2)}`;
            } catch (error) {
              log += ` [Object with circular reference]`;
            }
          }
          
          if (stack) {
            log += `\n${stack}`;
          }
          
          return log;
        })
      ),
      transports: [
        // Consola
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.timestamp({
              format: 'HH:mm:ss'
            }),
            winston.format.printf(({ level, message, timestamp, ...meta }) => {
              let log = `${timestamp} [${level}] [${this.component}]: ${message}`;
              
              if (Object.keys(meta).length > 0) {
                log += ` ${JSON.stringify(meta, null, 2)}`;
              }
              
              return log;
            })
          )
        }),
        
        // Archivo
        new winston.transports.File({
          filename: path.resolve(config.logging.file),
          maxsize: this.parseSize(config.logging.maxSize),
          maxFiles: config.logging.maxFiles,
          tailable: true
        }),
        
        // Archivo de errores
        new winston.transports.File({
          filename: path.resolve('./logs/error.log'),
          level: 'error',
          maxsize: this.parseSize(config.logging.maxSize),
          maxFiles: config.logging.maxFiles,
          tailable: true
        })
      ]
    });
  }

  parseSize(sizeStr) {
    const units = {
      'b': 1,
      'k': 1024,
      'm': 1024 * 1024,
      'g': 1024 * 1024 * 1024
    };
    
    const match = sizeStr.match(/^(\d+)([bkmg]?)$/i);
    if (!match) return 20 * 1024 * 1024; // Default 20MB
    
    const size = parseInt(match[1]);
    const unit = (match[2] || 'b').toLowerCase();
    
    return size * (units[unit] || 1);
  }

  info(message, meta = {}) {
    this.logger.info(message, meta);
  }

  warn(message, meta = {}) {
    this.logger.warn(message, meta);
  }

  error(message, meta = {}) {
    this.logger.error(message, meta);
  }

  debug(message, meta = {}) {
    this.logger.debug(message, meta);
  }

  verbose(message, meta = {}) {
    this.logger.verbose(message, meta);
  }

  // Métodos específicos para el trading
  logPrediction(prediction) {
    this.info('Nueva predicción generada', {
      asset: prediction.asset,
      direction: prediction.direction,
      confidence: prediction.confidence,
      timestamp: prediction.timestamp,
      indicators: prediction.indicators
    });
  }

  logPredictionResult(predictionId, asset, correct, actualDirection) {
    this.info('Resultado de predicción', {
      predictionId,
      asset,
      correct,
      actualDirection,
      timestamp: new Date().toISOString()
    });
  }

  logTechnicalAnalysis(asset, analysis) {
    this.debug('Análisis técnico completado', {
      asset,
      rsi: analysis.rsi,
      macd: analysis.macd,
      bollinger: analysis.bollinger,
      timestamp: new Date().toISOString()
    });
  }

  logMarketData(asset, candle) {
    this.verbose('Datos de mercado recibidos', {
      asset,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
      volume: candle.volume,
      timestamp: candle.timestamp
    });
  }

  logAITraining(epoch, loss, accuracy) {
    this.info('Entrenamiento de IA', {
      epoch,
      loss: loss.toFixed(6),
      accuracy: accuracy.toFixed(4),
      timestamp: new Date().toISOString()
    });
  }

  logPerformanceMetrics(metrics) {
    this.info('Métricas de rendimiento', {
      totalPredictions: metrics.totalPredictions,
      correctPredictions: metrics.correctPredictions,
      accuracy: metrics.accuracy,
      profitability: metrics.profitability,
      period: metrics.period,
      timestamp: new Date().toISOString()
    });
  }

  // Método para crear un logger hijo con contexto adicional
  child(additionalContext) {
    return new Logger(`${this.component}:${additionalContext}`);
  }
}

module.exports = Logger;
