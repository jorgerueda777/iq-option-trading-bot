const SimpleAI = require('../src/ai/simpleAI');
const Logger = require('../src/utils/logger');

class PredictionRunner {
  constructor() {
    this.logger = new Logger('PredictionRunner');
    this.ai = new SimpleAI();
    this.isRunning = false;
    this.predictions = [];
    this.assets = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC'];
  }

  async initialize() {
    await this.ai.initialize();
    
    // Cargar modelos entrenados
    const fs = require('fs');
    const modelPath = './data/simple_ai_models.json';
    
    if (!fs.existsSync(modelPath)) {
      throw new Error('No se encontraron modelos entrenados. Ejecuta trainSimpleAI.js primero.');
    }
    
    const modelInfo = JSON.parse(fs.readFileSync(modelPath, 'utf8'));
    this.logger.info(`📚 Modelos disponibles: ${modelInfo.models.join(', ')}`);
    
    // Entrenar modelos si no están cargados
    for (const asset of this.assets) {
      if (!this.ai.models.has(asset)) {
        this.logger.info(`🔄 Cargando modelo para ${asset}...`);
        await this.ai.trainModel(asset);
      }
    }
    
    this.logger.info('✅ PredictionRunner inicializado');
  }

  async makePredictions() {
    const predictions = [];
    
    for (const asset of this.assets) {
      try {
        const prediction = await this.ai.predict(asset);
        predictions.push(prediction);
        
        this.logger.info(`🔮 ${asset}: ${prediction.direction} (${prediction.confidence.toFixed(1)}%)`);
        this.logger.info(`   💰 ${prediction.current_price.toFixed(5)} → ${prediction.predicted_price.toFixed(5)} (${prediction.price_change_percent.toFixed(3)}%)`);
        this.logger.info(`   📊 RSI: ${prediction.technical_indicators.rsi.toFixed(1)} | MACD: ${prediction.technical_indicators.macd_line.toFixed(6)}`);
        this.logger.info(`   🔍 ${prediction.reasoning}`);
        
      } catch (error) {
        this.logger.error(`❌ Error prediciendo ${asset}:`, error.message);
      }
    }
    
    return predictions;
  }

  getBestOpportunities(predictions, minConfidence = 70) {
    return predictions
      .filter(p => p.confidence >= minConfidence)
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 5);
  }

  async runContinuous(intervalMinutes = 2) {
    this.isRunning = true;
    this.logger.info(`🔄 Iniciando predicciones continuas cada ${intervalMinutes} minutos`);
    
    const runRound = async () => {
      if (!this.isRunning) return;
      
      try {
        this.logger.info('\n🔮 === NUEVA RONDA DE PREDICCIONES ===');
        const timestamp = new Date().toLocaleString();
        this.logger.info(`⏰ ${timestamp}`);
        
        const predictions = await this.makePredictions();
        
        // Mejores oportunidades
        const opportunities = this.getBestOpportunities(predictions, 65);
        
        if (opportunities.length > 0) {
          this.logger.info('\n🎯 MEJORES OPORTUNIDADES:');
          opportunities.forEach((opp, index) => {
            this.logger.info(`   ${index + 1}. ${opp.asset} ${opp.direction} - ${opp.confidence.toFixed(1)}% confianza`);
            this.logger.info(`      💰 Cambio esperado: ${opp.price_change_percent.toFixed(3)}%`);
          });
        } else {
          this.logger.info('\n⚠️ No hay oportunidades de alta confianza en este momento');
        }
        
        // Estadísticas
        const upPredictions = predictions.filter(p => p.direction === 'UP').length;
        const downPredictions = predictions.filter(p => p.direction === 'DOWN').length;
        const avgConfidence = predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length;
        
        this.logger.info(`\n📊 RESUMEN: ${upPredictions} UP, ${downPredictions} DOWN | Confianza promedio: ${avgConfidence.toFixed(1)}%`);
        
        // Guardar predicciones
        this.predictions.push({
          timestamp: Date.now(),
          predictions: predictions,
          opportunities: opportunities
        });
        
        // Mantener solo las últimas 50 rondas
        if (this.predictions.length > 50) {
          this.predictions = this.predictions.slice(-50);
        }
        
      } catch (error) {
        this.logger.error('❌ Error en ronda de predicciones:', error);
      }
    };
    
    // Ejecutar primera ronda inmediatamente
    await runRound();
    
    // Programar rondas periódicas
    const interval = setInterval(runRound, intervalMinutes * 60 * 1000);
    
    // Manejar cierre
    process.on('SIGINT', () => {
      this.logger.info('\n⏹️ Deteniendo predicciones...');
      this.isRunning = false;
      clearInterval(interval);
      this.ai.close().then(() => {
        this.logger.info('✅ Predicciones detenidas');
        process.exit(0);
      });
    });
  }

  async close() {
    this.isRunning = false;
    await this.ai.close();
  }
}

async function runPredictions() {
  const logger = new Logger('RunPredictions');
  
  try {
    logger.info('🚀 INICIANDO SISTEMA DE PREDICCIONES');
    
    const runner = new PredictionRunner();
    await runner.initialize();
    
    // Ejecutar predicciones continuas
    await runner.runContinuous(2); // Cada 2 minutos
    
  } catch (error) {
    logger.error('❌ Error en sistema de predicciones:', error);
    process.exit(1);
  }
}

runPredictions();
