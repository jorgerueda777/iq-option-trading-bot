const SimpleAI = require('../src/ai/simpleAI');
const Logger = require('../src/utils/logger');

class AllPairsPredictor {
  constructor() {
    this.logger = new Logger('AllPairs');
    this.ai = new SimpleAI();
    this.isRunning = false;
    
    // TODOS LOS 15 PARES
    this.allAssets = [
      'EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'USDCAD-OTC',
      'EURJPY-OTC', 'GBPJPY-OTC', 'EURGBP-OTC', 'AUDJPY-OTC', 'NZDUSD-OTC',
      'USDCHF-OTC', 'EURCHF-OTC', 'GBPCHF-OTC', 'AUDCHF-OTC', 'CADCHF-OTC'
    ];
    
    this.predictions = [];
    this.roundCount = 0;
  }

  async initialize() {
    this.logger.info('🚀 INICIALIZANDO IA PARA TODOS LOS PARES');
    await this.ai.initialize();
    
    // Entrenar modelos para todos los pares
    this.logger.info(`🎯 Entrenando modelos para ${this.allAssets.length} pares...`);
    
    for (let i = 0; i < this.allAssets.length; i++) {
      const asset = this.allAssets[i];
      try {
        this.logger.info(`🔄 [${i + 1}/${this.allAssets.length}] Entrenando ${asset}...`);
        await this.ai.trainModel(asset);
        this.logger.info(`✅ ${asset} listo`);
      } catch (error) {
        this.logger.error(`❌ Error entrenando ${asset}:`, error.message);
      }
    }
    
    this.logger.info('✅ Todos los modelos listos');
  }

  async makePredictions() {
    const predictions = [];
    const timestamp = new Date().toLocaleString();
    
    this.logger.info(`\n🔮 === RONDA ${++this.roundCount} === ${timestamp} ===`);
    
    for (const asset of this.allAssets) {
      try {
        const prediction = await this.ai.predict(asset);
        predictions.push(prediction);
        
        // Log compacto
        const direction = prediction.direction === 'UP' ? '📈' : '📉';
        const confidence = prediction.confidence.toFixed(1);
        const priceChange = prediction.price_change_percent.toFixed(3);
        
        this.logger.info(`${direction} ${asset}: ${prediction.direction} (${confidence}%) ${priceChange}%`);
        
      } catch (error) {
        this.logger.error(`❌ ${asset}: Error - ${error.message}`);
      }
    }
    
    return predictions;
  }

  analyzeMarket(predictions) {
    const upCount = predictions.filter(p => p.direction === 'UP').length;
    const downCount = predictions.filter(p => p.direction === 'DOWN').length;
    const avgConfidence = predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length;
    
    // Mejores oportunidades (alta confianza)
    const highConfidence = predictions
      .filter(p => p.confidence >= 60)
      .sort((a, b) => b.confidence - a.confidence);
    
    // Señales extremas (muy alta confianza)
    const extremeSignals = predictions
      .filter(p => p.confidence >= 75)
      .sort((a, b) => b.confidence - a.confidence);
    
    return {
      total: predictions.length,
      up: upCount,
      down: downCount,
      avgConfidence: avgConfidence,
      marketSentiment: upCount > downCount ? 'ALCISTA' : 'BAJISTA',
      highConfidence: highConfidence,
      extremeSignals: extremeSignals
    };
  }

  displayAnalysis(analysis) {
    this.logger.info(`\n📊 ANÁLISIS DE MERCADO:`);
    this.logger.info(`   📈 UP: ${analysis.up} | 📉 DOWN: ${analysis.down} | 🎯 Promedio: ${analysis.avgConfidence.toFixed(1)}%`);
    this.logger.info(`   🌊 Sentimiento: ${analysis.marketSentiment}`);
    
    if (analysis.extremeSignals.length > 0) {
      this.logger.info(`\n🚨 SEÑALES EXTREMAS (>75% confianza):`);
      analysis.extremeSignals.forEach((signal, index) => {
        const direction = signal.direction === 'UP' ? '📈' : '📉';
        this.logger.info(`   ${index + 1}. ${direction} ${signal.asset}: ${signal.confidence.toFixed(1)}% - ${signal.reasoning}`);
      });
    }
    
    if (analysis.highConfidence.length > 0) {
      this.logger.info(`\n🎯 ALTA CONFIANZA (>60%):`);
      analysis.highConfidence.slice(0, 5).forEach((signal, index) => {
        const direction = signal.direction === 'UP' ? '📈' : '📉';
        this.logger.info(`   ${index + 1}. ${direction} ${signal.asset}: ${signal.confidence.toFixed(1)}%`);
      });
    } else {
      this.logger.info(`\n⚠️ No hay señales de alta confianza en este momento`);
    }
  }

  async runContinuous(intervalMinutes = 1) {
    this.isRunning = true;
    this.logger.info(`🔄 INICIANDO PREDICCIONES CONTINUAS CADA ${intervalMinutes} MINUTO(S)`);
    this.logger.info(`📊 Monitoreando ${this.allAssets.length} pares simultáneamente`);
    
    const runRound = async () => {
      if (!this.isRunning) return;
      
      try {
        // Hacer predicciones
        const predictions = await this.makePredictions();
        
        // Analizar mercado
        const analysis = this.analyzeMarket(predictions);
        
        // Mostrar análisis
        this.displayAnalysis(analysis);
        
        // Guardar historial
        this.predictions.push({
          timestamp: Date.now(),
          round: this.roundCount,
          predictions: predictions,
          analysis: analysis
        });
        
        // Mantener solo las últimas 100 rondas
        if (this.predictions.length > 100) {
          this.predictions = this.predictions.slice(-100);
        }
        
      } catch (error) {
        this.logger.error('❌ Error en ronda:', error);
      }
    };
    
    // Primera ronda inmediata
    await runRound();
    
    // Rondas periódicas
    const interval = setInterval(runRound, intervalMinutes * 60 * 1000);
    
    // Manejar cierre
    process.on('SIGINT', () => {
      this.logger.info('\n⏹️ Deteniendo predicciones...');
      this.isRunning = false;
      clearInterval(interval);
      this.ai.close().then(() => {
        this.logger.info('✅ Sistema detenido');
        process.exit(0);
      });
    });
    
    // Mantener el proceso vivo
    process.stdin.resume();
  }
}

async function runAllPairs() {
  const logger = new Logger('Main');
  
  try {
    logger.info('🚀 INICIANDO IA PARA TODOS LOS PARES');
    
    const predictor = new AllPairsPredictor();
    await predictor.initialize();
    
    // Ejecutar predicciones cada 1 minuto
    await predictor.runContinuous(1);
    
  } catch (error) {
    logger.error('❌ Error:', error);
    process.exit(1);
  }
}

runAllPairs();
