require('dotenv').config();

module.exports = {
  // Configuración de IQ Option
  iqOption: {
    email: process.env.IQ_EMAIL || '',
    password: process.env.IQ_PASSWORD || '',
    practice: process.env.IQ_PRACTICE === 'true' || true,
    baseUrl: 'https://iqoption.com',
    wsUrl: 'wss://iqoption.com/echo/websocket',
    apiUrl: 'https://iqoption.com/api'
  },

  // Configuración de la IA
  ai: {
    modelPath: './models/prediction_model.json',
    trainingDataPath: './data/training_data.json',
    predictionInterval: 60000, // 1 minuto
    lookbackPeriod: 100, // Número de velas históricas para análisis
    features: [
      'open', 'high', 'low', 'close', 'volume',
      'rsi', 'macd', 'bollinger_upper', 'bollinger_lower',
      'ema_12', 'ema_26', 'sma_50', 'hour', 'minute'
    ],
    epochs: 100,
    batchSize: 32,
    validationSplit: 0.2
  },

  // Activos OTC a monitorear (disponibles 24/7) - LOS 7 QUE FUNCIONAN
  assets: [
    'EURUSD-OTC', 'GBPUSD-OTC', 'GBPJPY-OTC', 'EURJPY-OTC', 'EURGBP-OTC', 'USDCHF-OTC', 'AUDCAD-OTC'
  ],

  // Configuración de timeframes
  timeframes: {
    primary: 60, // 1 minuto
    analysis: [60, 300, 900, 1800] // 1m, 5m, 15m, 30m
  },

  // Configuración del servidor web
  server: {
    port: process.env.PORT || 3000,
    host: process.env.HOST || 'localhost'
  },

  // Configuración de base de datos
  database: {
    mongodb: process.env.MONGODB_URI || 'mongodb://localhost:27017/iq_scanner'
  },

  // Configuración de logging
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    file: './logs/app.log',
    maxSize: '20m',
    maxFiles: 5
  },

  // Configuración de análisis técnico
  technicalAnalysis: {
    rsi: {
      period: 14,
      overbought: 70,
      oversold: 30
    },
    macd: {
      fastPeriod: 12,
      slowPeriod: 26,
      signalPeriod: 9
    },
    bollinger: {
      period: 20,
      stdDev: 2
    },
    ema: {
      periods: [12, 26, 50]
    },
    sma: {
      periods: [20, 50, 100]
    }
  },

  // Configuración de predicción
  prediction: {
    confidence_threshold: 0.7, // Umbral de confianza mínimo
    max_predictions_per_hour: 10,
    cooldown_period: 300000, // 5 minutos entre predicciones del mismo activo
    historical_accuracy_weight: 0.3
  }
};
