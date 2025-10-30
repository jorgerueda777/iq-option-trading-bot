const Logger = require('../utils/logger');

class AIPredictor {
  constructor() {
    this.logger = new Logger('AIPredictor');
    this.isInitialized = false;
  }

  async initialize() {
    try {
      this.logger.info('🤖 Inicializando AI Predictor Simple...');
      this.isInitialized = true;
      this.logger.info('✅ AI Predictor Simple inicializado');
    } catch (error) {
      this.logger.error('❌ Error inicializando AI Predictor:', error);
      throw error;
    }
  }

  async predict(candleBuffer, technicalAnalysis, asset) {
    try {
      if (!this.isInitialized) {
        throw new Error('AI Predictor no está inicializado');
      }

      if (!candleBuffer || candleBuffer.length < 5) {
        return null;
      }

      // ANÁLISIS AVANZADO CON MÚLTIPLES INDICADORES POTENTES
      const recentCandles = candleBuffer.slice(-20); // Más datos para análisis
      const prices = recentCandles.map(c => c.close);
      const highs = recentCandles.map(c => c.high);
      const lows = recentCandles.map(c => c.low);
      const volumes = recentCandles.map(c => c.volume || 1);
      
      // 1. ANÁLISIS DE MOMENTUM AVANZADO
      const momentum = this.calculateAdvancedMomentum(recentCandles);
      
      // 2. ANÁLISIS DE VOLATILIDAD INTELIGENTE
      const volatility = this.calculateSmartVolatility(recentCandles);
      
      // 3. ANÁLISIS DE SOPORTE/RESISTENCIA DINÁMICO
      const supportResistance = this.calculateDynamicLevels(recentCandles);
      
      // 4. ANÁLISIS DE VOLUMEN INTELIGENTE
      const volumeAnalysis = this.analyzeVolumePattern(recentCandles);
      
      // 5. ANÁLISIS DE PATRONES DE VELAS JAPONESAS
      const candlePatterns = this.analyzeCandlePatterns(recentCandles.slice(-5));
      
      // 6. ANÁLISIS DE DIVERGENCIAS
      const divergences = this.detectDivergences(recentCandles);
      
      // SISTEMA DE VOTACIÓN INTELIGENTE
      let votes = {
        call: 0,
        put: 0,
        confidence: 0
      };
      
      // VOTO 1: Momentum (peso 25%)
      if (momentum.direction === 'UP') {
        votes.call += momentum.strength * 0.25;
      } else {
        votes.put += momentum.strength * 0.25;
      }
      
      // VOTO 2: Volatilidad (peso 15%)
      if (volatility.trend === 'INCREASING' && volatility.level < 0.8) {
        votes.confidence += 0.15; // Volatilidad buena para trading
      }
      
      // VOTO 3: Soporte/Resistencia (peso 20%)
      if (supportResistance.signal === 'BOUNCE_UP') {
        votes.call += 0.20;
      } else if (supportResistance.signal === 'BREAK_DOWN') {
        votes.put += 0.20;
      }
      
      // VOTO 4: Volumen (peso 15%)
      if (volumeAnalysis.confirmation === 'STRONG') {
        if (volumeAnalysis.direction === 'UP') {
          votes.call += 0.15;
        } else {
          votes.put += 0.15;
        }
      }
      
      // VOTO 5: Patrones de velas (peso 15%)
      if (candlePatterns.signal === 'BULLISH') {
        votes.call += candlePatterns.strength * 0.15;
      } else if (candlePatterns.signal === 'BEARISH') {
        votes.put += candlePatterns.strength * 0.15;
      }
      
      // VOTO 6: Divergencias (peso 10%)
      if (divergences.type === 'BULLISH') {
        votes.call += divergences.strength * 0.10;
      } else if (divergences.type === 'BEARISH') {
        votes.put += divergences.strength * 0.10;
      }
      
      // DECISIÓN FINAL BASADA EN VOTACIÓN
      const direction = votes.call > votes.put ? 'CALL' : 'PUT';
      let confidence = Math.abs(votes.call - votes.put) + votes.confidence;
      
      // BONUS POR CONFLUENCIA DE SEÑALES
      const signalCount = [momentum, supportResistance, volumeAnalysis, candlePatterns, divergences]
        .filter(s => s.strength > 0.6).length;
      
      if (signalCount >= 3) {
        confidence += 0.15; // Bonus por múltiples señales fuertes
      }

      // Ajustar con análisis técnico si está disponible
      if (technicalAnalysis && technicalAnalysis.signals) {
        const techSignal = technicalAnalysis.signals.overall;
        if (techSignal === direction.toLowerCase()) {
          confidence += 0.1; // Bonus por alineación
        } else {
          confidence -= 0.05; // Penalización menor por divergencia
        }
      }

      // Límites de confianza
      confidence = Math.max(0.3, Math.min(0.8, confidence));

      const prediction = {
        id: `${asset}_${Date.now()}`,
        asset: asset,
        direction: direction,
        confidence: confidence,
        timestamp: Date.now(),
        method: 'simple_pattern',
        patternInfo: {
          momentum: momentum.direction,
          volatility: volatility.level,
          supportResistance: supportResistance.signal,
          volumeAnalysis: volumeAnalysis.confirmation,
          candlePatterns: candlePatterns.signal,
          divergences: divergences.type,
          totalCandles: recentCandles.length
        }
      };

      return prediction;

    } catch (error) {
      this.logger.error(`❌ Error en predicción simple para ${asset}:`, error);
      return null;
    }
  }

  updatePredictionResult(predictionId, actualDirection) {
    // Método para actualizar resultados (implementación básica)
    this.logger.info(`📊 Resultado actualizado para ${predictionId}: ${actualDirection}`);
  }

  // MÉTODO 1: ANÁLISIS DE MOMENTUM AVANZADO
  calculateAdvancedMomentum(candles) {
    if (candles.length < 10) return { direction: 'NEUTRAL', strength: 0 };
    
    const prices = candles.map(c => c.close);
    const recent = prices.slice(-5);
    const older = prices.slice(-10, -5);
    
    const recentAvg = recent.reduce((a, b) => a + b) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b) / older.length;
    
    const momentum = (recentAvg - olderAvg) / olderAvg;
    const strength = Math.min(Math.abs(momentum) * 100, 1.0);
    
    return {
      direction: momentum > 0 ? 'UP' : 'DOWN',
      strength: strength,
      value: momentum
    };
  }

  // MÉTODO 2: ANÁLISIS DE VOLATILIDAD INTELIGENTE
  calculateSmartVolatility(candles) {
    if (candles.length < 10) return { level: 0.5, trend: 'STABLE' };
    
    const ranges = candles.map(c => Math.abs(c.high - c.low) / c.close);
    const recentVol = ranges.slice(-5).reduce((a, b) => a + b) / 5;
    const olderVol = ranges.slice(-10, -5).reduce((a, b) => a + b) / 5;
    
    return {
      level: recentVol,
      trend: recentVol > olderVol * 1.1 ? 'INCREASING' : 
             recentVol < olderVol * 0.9 ? 'DECREASING' : 'STABLE',
      change: (recentVol - olderVol) / olderVol
    };
  }

  // MÉTODO 3: ANÁLISIS DE SOPORTE/RESISTENCIA DINÁMICO
  calculateDynamicLevels(candles) {
    if (candles.length < 15) return { signal: 'NEUTRAL', strength: 0 };
    
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    const currentPrice = candles[candles.length - 1].close;
    
    const resistance = Math.max(...highs.slice(-10));
    const support = Math.min(...lows.slice(-10));
    
    const distToResistance = (resistance - currentPrice) / currentPrice;
    const distToSupport = (currentPrice - support) / currentPrice;
    
    let signal = 'NEUTRAL';
    let strength = 0;
    
    if (distToSupport < 0.002) { // Cerca del soporte
      signal = 'BOUNCE_UP';
      strength = 0.8;
    } else if (distToResistance < 0.002) { // Cerca de resistencia
      signal = 'BOUNCE_DOWN';
      strength = 0.8;
    } else if (currentPrice > resistance) { // Rompió resistencia
      signal = 'BREAK_UP';
      strength = 0.7;
    } else if (currentPrice < support) { // Rompió soporte
      signal = 'BREAK_DOWN';
      strength = 0.7;
    }
    
    return { signal, strength, support, resistance };
  }

  // MÉTODO 4: ANÁLISIS DE VOLUMEN INTELIGENTE
  analyzeVolumePattern(candles) {
    if (candles.length < 10) return { confirmation: 'WEAK', direction: 'NEUTRAL' };
    
    const volumes = candles.map(c => c.volume || 1);
    const prices = candles.map(c => c.close);
    
    const recentVol = volumes.slice(-3).reduce((a, b) => a + b) / 3;
    const avgVol = volumes.reduce((a, b) => a + b) / volumes.length;
    
    const priceChange = prices[prices.length - 1] - prices[prices.length - 4];
    const volIncrease = recentVol > avgVol * 1.2;
    
    return {
      confirmation: volIncrease ? 'STRONG' : 'WEAK',
      direction: priceChange > 0 ? 'UP' : 'DOWN',
      volumeRatio: recentVol / avgVol
    };
  }

  // MÉTODO 5: ANÁLISIS DE PATRONES DE VELAS JAPONESAS
  analyzeCandlePatterns(candles) {
    if (candles.length < 3) return { signal: 'NEUTRAL', strength: 0 };
    
    const last = candles[candles.length - 1];
    const prev = candles[candles.length - 2];
    
    const lastBody = Math.abs(last.close - last.open);
    const lastRange = last.high - last.low;
    const lastBullish = last.close > last.open;
    
    // Detectar patrones específicos
    let signal = 'NEUTRAL';
    let strength = 0;
    
    // Martillo/Doji
    if (lastBody < lastRange * 0.3) {
      signal = 'REVERSAL';
      strength = 0.6;
    }
    // Vela envolvente
    else if (lastBody > lastRange * 0.7) {
      signal = lastBullish ? 'BULLISH' : 'BEARISH';
      strength = 0.8;
    }
    // Secuencia de 3 velas
    else if (candles.length >= 3) {
      const third = candles[candles.length - 3];
      const allBullish = [third, prev, last].every(c => c.close > c.open);
      const allBearish = [third, prev, last].every(c => c.close < c.open);
      
      if (allBullish) {
        signal = 'BULLISH';
        strength = 0.7;
      } else if (allBearish) {
        signal = 'BEARISH';
        strength = 0.7;
      }
    }
    
    return { signal, strength };
  }

  // MÉTODO 6: DETECCIÓN DE DIVERGENCIAS
  detectDivergences(candles) {
    if (candles.length < 10) return { type: 'NONE', strength: 0 };
    
    const prices = candles.map(c => c.close);
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    
    // Calcular RSI simple
    const rsi = this.calculateSimpleRSI(prices);
    
    const recentPriceHigh = Math.max(...prices.slice(-5));
    const olderPriceHigh = Math.max(...prices.slice(-10, -5));
    const recentRSIHigh = Math.max(...rsi.slice(-5));
    const olderRSIHigh = Math.max(...rsi.slice(-10, -5));
    
    let type = 'NONE';
    let strength = 0;
    
    // Divergencia bajista: precio sube, RSI baja
    if (recentPriceHigh > olderPriceHigh && recentRSIHigh < olderRSIHigh) {
      type = 'BEARISH';
      strength = 0.6;
    }
    // Divergencia alcista: precio baja, RSI sube
    else if (recentPriceHigh < olderPriceHigh && recentRSIHigh > olderRSIHigh) {
      type = 'BULLISH';
      strength = 0.6;
    }
    
    return { type, strength };
  }

  // MÉTODO AUXILIAR: RSI SIMPLE
  calculateSimpleRSI(prices, period = 14) {
    if (prices.length < period + 1) return prices.map(() => 50);
    
    const rsi = [];
    for (let i = period; i < prices.length; i++) {
      let gains = 0, losses = 0;
      
      for (let j = i - period + 1; j <= i; j++) {
        const change = prices[j] - prices[j - 1];
        if (change > 0) gains += change;
        else losses -= change;
      }
      
      const avgGain = gains / period;
      const avgLoss = losses / period;
      const rs = avgGain / (avgLoss || 0.001);
      rsi.push(100 - (100 / (1 + rs)));
    }
    
    return rsi;
  }

  getAccuracyStats() {
    // Método para obtener estadísticas de precisión
    return {
      totalPredictions: 0,
      correctPredictions: 0,
      accuracy: 0,
      lastUpdated: Date.now()
    };
  }

  getModelInfo() {
    // Información del modelo
    return {
      type: 'simple_pattern',
      version: '1.0',
      initialized: this.isInitialized
    };
  }
}

module.exports = AIPredictor;
