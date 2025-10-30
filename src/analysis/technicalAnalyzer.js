const { RSI, MACD, BollingerBands, EMA, SMA, Stochastic, WilliamsR } = require('technicalindicators');
const moment = require('moment');
const Logger = require('../utils/logger');
const config = require('../../config/config');

class TechnicalAnalyzer {
  constructor() {
    this.logger = new Logger('TechnicalAnalyzer');
    this.indicators = {};
    this.historicalData = new Map();
  }

  /**
   * Analiza una serie de velas y devuelve indicadores técnicos
   */
  analyze(candles, asset) {
    try {
      if (!candles || candles.length < 3) {  
        throw new Error('Datos insuficientes para análisis técnico');
      }

      // Preparar datos
      const prices = candles.map(c => c.close);
      const highs = candles.map(c => c.high);
      const lows = candles.map(c => c.low);
      const opens = candles.map(c => c.open);
      const volumes = candles.map(c => c.volume || 1);
      
      // Calcular indicadores
      const analysis = {
        asset: asset,
        timestamp: Date.now(),
        candles: candles.length,
        
        // Indicadores de tendencia
        rsi: this.calculateRSI(prices),
        macd: this.calculateMACD(prices),
        bollinger: this.calculateBollingerBands(prices),
        
        // Medias móviles
        ema12: this.calculateEMA(prices, 12),
        ema26: this.calculateEMA(prices, 26),
        ema50: this.calculateEMA(prices, 50),
        sma20: this.calculateSMA(prices, 20),
        sma50: this.calculateSMA(prices, 50),
        sma100: this.calculateSMA(prices, 100),
        
        // Osciladores
        stochastic: this.calculateStochastic(highs, lows, prices),
        williams: this.calculateWilliams(highs, lows, prices),
        
        // Análisis de velas
        candlePatterns: this.analyzeCandlePatterns(candles.slice(-10)),
        
        // Análisis de volumen
        volumeAnalysis: this.analyzeVolume(candles.slice(-20)),
        
        // Soporte y resistencia
        supportResistance: this.findSupportResistance(candles.slice(-50)),
        
        // Análisis temporal
        timeAnalysis: this.analyzeTimePatterns(candles, asset)
      };

      // Generar señales
      analysis.signals = this.generateSignals(analysis);
      
      // Calcular puntuación general
      analysis.score = this.calculateOverallScore(analysis);
      
      this.logger.logTechnicalAnalysis(asset, analysis);
      
      return analysis;
      
    } catch (error) {
      this.logger.error(`Error en análisis técnico de ${asset}:`, error);
      throw error;
    }
  }

  calculateRSI(prices) {
    try {
      const rsiValues = RSI.calculate({
        values: prices,
        period: config.technicalAnalysis.rsi.period
      });
      
      const current = rsiValues[rsiValues.length - 1];
      const previous = rsiValues[rsiValues.length - 2];
      
      return {
        current: current,
        previous: previous,
        trend: current > previous ? 'up' : 'down',
        overbought: current > config.technicalAnalysis.rsi.overbought,
        oversold: current < config.technicalAnalysis.rsi.oversold,
        signal: this.getRSISignal(current)
      };
    } catch (error) {
      this.logger.error('Error calculando RSI:', error);
      return null;
    }
  }

  calculateMACD(prices) {
    try {
      const macdValues = MACD.calculate({
        values: prices,
        fastPeriod: config.technicalAnalysis.macd.fastPeriod,
        slowPeriod: config.technicalAnalysis.macd.slowPeriod,
        signalPeriod: config.technicalAnalysis.macd.signalPeriod,
        SimpleMAOscillator: false,
        SimpleMASignal: false
      });
      
      const current = macdValues[macdValues.length - 1];
      const previous = macdValues[macdValues.length - 2];
      
      if (!current || !previous) return null;
      
      return {
        macd: current.MACD,
        signal: current.signal,
        histogram: current.histogram,
        crossover: this.detectMACDCrossover(current, previous),
        trend: current.MACD > current.signal ? 'bullish' : 'bearish',
        divergence: this.detectMACDDivergence(macdValues.slice(-10), prices.slice(-10))
      };
    } catch (error) {
      this.logger.error('Error calculando MACD:', error);
      return null;
    }
  }

  calculateBollingerBands(prices) {
    try {
      const bbValues = BollingerBands.calculate({
        values: prices,
        period: config.technicalAnalysis.bollinger.period,
        stdDev: config.technicalAnalysis.bollinger.stdDev
      });
      
      const current = bbValues[bbValues.length - 1];
      const currentPrice = prices[prices.length - 1];
      
      if (!current) return null;
      
      const bandwidth = (current.upper - current.lower) / current.middle * 100;
      const position = (currentPrice - current.lower) / (current.upper - current.lower) * 100;
      
      return {
        upper: current.upper,
        middle: current.middle,
        lower: current.lower,
        bandwidth: bandwidth,
        position: position,
        squeeze: bandwidth < 10, // Bollinger Squeeze
        signal: this.getBollingerSignal(currentPrice, current)
      };
    } catch (error) {
      this.logger.error('Error calculando Bollinger Bands:', error);
      return null;
    }
  }

  calculateEMA(prices, period) {
    try {
      const emaValues = EMA.calculate({
        values: prices,
        period: period
      });
      
      return {
        current: emaValues[emaValues.length - 1],
        previous: emaValues[emaValues.length - 2],
        trend: emaValues[emaValues.length - 1] > emaValues[emaValues.length - 2] ? 'up' : 'down'
      };
    } catch (error) {
      this.logger.error(`Error calculando EMA ${period}:`, error);
      return null;
    }
  }

  calculateSMA(prices, period) {
    try {
      const smaValues = SMA.calculate({
        values: prices,
        period: period
      });
      
      return {
        current: smaValues[smaValues.length - 1],
        previous: smaValues[smaValues.length - 2],
        trend: smaValues[smaValues.length - 1] > smaValues[smaValues.length - 2] ? 'up' : 'down'
      };
    } catch (error) {
      this.logger.error(`Error calculando SMA ${period}:`, error);
      return null;
    }
  }

  calculateStochastic(highs, lows, closes) {
    try {
      const stochValues = Stochastic.calculate({
        high: highs,
        low: lows,
        close: closes,
        period: 14,
        signalPeriod: 3
      });
      
      const current = stochValues[stochValues.length - 1];
      
      // Validar que current existe y tiene propiedades
      if (!current || typeof current.k === 'undefined') {
        return {
          k: 50,
          d: 50,
          overbought: false,
          oversold: false,
          signal: 'neutral'
        };
      }
      
      return {
        k: current.k,
        d: current.d,
        overbought: current.k > 80,
        oversold: current.k < 20,
        signal: this.getStochasticSignal(current)
      };
    } catch (error) {
      this.logger.error('Error calculando Stochastic:', error);
      return null;
    }
  }

  calculateWilliams(highs, lows, closes) {
    try {
      const williamsValues = WilliamsR.calculate({
        high: highs,
        low: lows,
        close: closes,
        period: 14
      });
      
      const current = williamsValues[williamsValues.length - 1];
      
      return {
        current: current,
        overbought: current > -20,
        oversold: current < -80,
        signal: current > -20 ? 'sell' : current < -80 ? 'buy' : 'neutral'
      };
    } catch (error) {
      this.logger.error('Error calculando Williams %R:', error);
      return null;
    }
  }

  analyzeCandlePatterns(candles) {
    const patterns = [];
    
    if (candles.length < 3) return patterns;
    
    // Doji
    if (this.isDoji(candles[candles.length - 1])) {
      patterns.push({ name: 'doji', signal: 'neutral', strength: 0.6 });
    }
    
    // Hammer
    if (this.isHammer(candles[candles.length - 1])) {
      patterns.push({ name: 'hammer', signal: 'buy', strength: 0.7 });
    }
    
    // Shooting Star
    if (this.isShootingStar(candles[candles.length - 1])) {
      patterns.push({ name: 'shooting_star', signal: 'sell', strength: 0.7 });
    }
    
    // Engulfing patterns
    const engulfing = this.checkEngulfingPattern(candles.slice(-2));
    if (engulfing) {
      patterns.push(engulfing);
    }
    
    return patterns;
  }

  analyzeVolume(candles) {
    const volumes = candles.map(c => c.volume || 1);
    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    const currentVolume = volumes[volumes.length - 1];
    
    return {
      average: avgVolume,
      current: currentVolume,
      ratio: currentVolume / avgVolume,
      trend: this.getVolumeTrend(volumes),
      signal: currentVolume > avgVolume * 1.5 ? 'high' : currentVolume < avgVolume * 0.5 ? 'low' : 'normal'
    };
  }

  findSupportResistance(candles) {
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    
    // Encontrar niveles de soporte y resistencia usando pivots
    const resistance = Math.max(...highs.slice(-20));
    const support = Math.min(...lows.slice(-20));
    const currentPrice = candles[candles.length - 1].close;
    
    return {
      resistance: resistance,
      support: support,
      currentPrice: currentPrice,
      nearResistance: Math.abs(currentPrice - resistance) / currentPrice < 0.002,
      nearSupport: Math.abs(currentPrice - support) / currentPrice < 0.002,
      range: resistance - support
    };
  }

  analyzeTimePatterns(candles, asset) {
    const now = moment();
    const hour = now.hour();
    const minute = now.minute();
    const dayOfWeek = now.day();
    
    // Analizar patrones históricos por hora
    const hourlyStats = this.getHourlyStatistics(asset, hour);
    
    return {
      hour: hour,
      minute: minute,
      dayOfWeek: dayOfWeek,
      sessionType: this.getSessionType(hour),
      hourlyBias: hourlyStats.bias,
      hourlyAccuracy: hourlyStats.accuracy,
      volatilityExpected: this.getExpectedVolatility(hour, dayOfWeek)
    };
  }

  generateSignals(analysis) {
    const signals = [];
    let bullishScore = 0;
    let bearishScore = 0;
    
    // RSI signals
    if (analysis.rsi) {
      if (analysis.rsi.oversold) {
        signals.push({ type: 'RSI', signal: 'buy', strength: 0.7 });
        bullishScore += 0.7;
      } else if (analysis.rsi.overbought) {
        signals.push({ type: 'RSI', signal: 'sell', strength: 0.7 });
        bearishScore += 0.7;
      }
    }
    
    // MACD signals
    if (analysis.macd && analysis.macd.crossover) {
      const signal = analysis.macd.crossover === 'bullish' ? 'buy' : 'sell';
      signals.push({ type: 'MACD', signal: signal, strength: 0.8 });
      
      if (signal === 'buy') bullishScore += 0.8;
      else bearishScore += 0.8;
    }
    
    // Bollinger Bands signals
    if (analysis.bollinger) {
      if (analysis.bollinger.signal === 'buy') {
        signals.push({ type: 'Bollinger', signal: 'buy', strength: 0.6 });
        bullishScore += 0.6;
      } else if (analysis.bollinger.signal === 'sell') {
        signals.push({ type: 'Bollinger', signal: 'sell', strength: 0.6 });
        bearishScore += 0.6;
      }
    }
    
    // Moving Average signals
    if (analysis.ema12 && analysis.ema26) {
      if (analysis.ema12.current > analysis.ema26.current) {
        bullishScore += 0.5;
      } else {
        bearishScore += 0.5;
      }
    }
    
    // Candlestick pattern signals
    analysis.candlePatterns.forEach(pattern => {
      signals.push({ type: 'Pattern', signal: pattern.signal, strength: pattern.strength });
      
      if (pattern.signal === 'buy') bullishScore += pattern.strength;
      else if (pattern.signal === 'sell') bearishScore += pattern.strength;
    });
    
    // Determinar señal general
    const totalScore = bullishScore + bearishScore;
    const confidence = Math.abs(bullishScore - bearishScore) / Math.max(totalScore, 1);
    
    return {
      signals: signals,
      overall: bullishScore > bearishScore ? 'buy' : 'sell',
      confidence: confidence,
      bullishScore: bullishScore,
      bearishScore: bearishScore
    };
  }

  calculateOverallScore(analysis) {
    let score = 0;
    let maxScore = 0;
    
    // RSI score
    if (analysis.rsi) {
      maxScore += 1;
      if (analysis.rsi.signal === 'buy' || analysis.rsi.signal === 'sell') {
        score += analysis.rsi.oversold || analysis.rsi.overbought ? 1 : 0.5;
      }
    }
    
    // MACD score
    if (analysis.macd) {
      maxScore += 1;
      if (analysis.macd.crossover) {
        score += 1;
      } else if (analysis.macd.trend === 'bullish' || analysis.macd.trend === 'bearish') {
        score += 0.5;
      }
    }
    
    // Bollinger score
    if (analysis.bollinger) {
      maxScore += 1;
      if (analysis.bollinger.signal !== 'neutral') {
        score += 0.7;
      }
    }
    
    // Pattern score
    if (analysis.candlePatterns.length > 0) {
      maxScore += 1;
      score += Math.min(analysis.candlePatterns.length * 0.3, 1);
    }
    
    return maxScore > 0 ? (score / maxScore) * 100 : 0;
  }

  // Métodos auxiliares
  getRSISignal(rsi) {
    if (rsi > 70) return 'sell';
    if (rsi < 30) return 'buy';
    return 'neutral';
  }

  getBollingerSignal(price, bands) {
    if (price <= bands.lower) return 'buy';
    if (price >= bands.upper) return 'sell';
    return 'neutral';
  }

  getStochasticSignal(stoch) {
    if (stoch.k < 20 && stoch.d < 20) return 'buy';
    if (stoch.k > 80 && stoch.d > 80) return 'sell';
    return 'neutral';
  }

  detectMACDCrossover(current, previous) {
    if (!current || !previous) return null;
    
    if (previous.MACD <= previous.signal && current.MACD > current.signal) {
      return 'bullish';
    }
    if (previous.MACD >= previous.signal && current.MACD < current.signal) {
      return 'bearish';
    }
    return null;
  }

  detectMACDDivergence(macdValues, prices) {
    // Implementación simplificada de divergencia
    if (macdValues.length < 5 || prices.length < 5) return null;
    
    const recentMacd = macdValues.slice(-3);
    const recentPrices = prices.slice(-3);
    
    const macdTrend = recentMacd[2].MACD > recentMacd[0].MACD ? 'up' : 'down';
    const priceTrend = recentPrices[2] > recentPrices[0] ? 'up' : 'down';
    
    if (macdTrend !== priceTrend) {
      return macdTrend === 'up' ? 'bullish_divergence' : 'bearish_divergence';
    }
    
    return null;
  }

  isDoji(candle) {
    const bodySize = Math.abs(candle.close - candle.open);
    const range = candle.high - candle.low;
    return bodySize / range < 0.1;
  }

  isHammer(candle) {
    const bodySize = Math.abs(candle.close - candle.open);
    const lowerShadow = Math.min(candle.open, candle.close) - candle.low;
    const upperShadow = candle.high - Math.max(candle.open, candle.close);
    
    return lowerShadow > bodySize * 2 && upperShadow < bodySize * 0.5;
  }

  isShootingStar(candle) {
    const bodySize = Math.abs(candle.close - candle.open);
    const lowerShadow = Math.min(candle.open, candle.close) - candle.low;
    const upperShadow = candle.high - Math.max(candle.open, candle.close);
    
    return upperShadow > bodySize * 2 && lowerShadow < bodySize * 0.5;
  }

  checkEngulfingPattern(candles) {
    if (candles.length < 2) return null;
    
    const [prev, curr] = candles;
    const prevBody = Math.abs(prev.close - prev.open);
    const currBody = Math.abs(curr.close - curr.open);
    
    // Bullish engulfing
    if (prev.close < prev.open && curr.close > curr.open && 
        curr.open < prev.close && curr.close > prev.open) {
      return { name: 'bullish_engulfing', signal: 'buy', strength: 0.8 };
    }
    
    // Bearish engulfing
    if (prev.close > prev.open && curr.close < curr.open && 
        curr.open > prev.close && curr.close < prev.open) {
      return { name: 'bearish_engulfing', signal: 'sell', strength: 0.8 };
    }
    
    return null;
  }

  getVolumeTrend(volumes) {
    if (volumes.length < 3) return 'neutral';
    
    const recent = volumes.slice(-3);
    if (recent[2] > recent[1] && recent[1] > recent[0]) return 'increasing';
    if (recent[2] < recent[1] && recent[1] < recent[0]) return 'decreasing';
    return 'neutral';
  }

  getSessionType(hour) {
    if (hour >= 0 && hour < 8) return 'asian';
    if (hour >= 8 && hour < 16) return 'european';
    if (hour >= 16 && hour < 24) return 'american';
    return 'overlap';
  }

  getHourlyStatistics(asset, hour) {
    // Aquí se implementaría la lógica para obtener estadísticas históricas
    // Por ahora devolvemos valores por defecto
    return {
      bias: 'neutral',
      accuracy: 0.5,
      avgMovement: 0.001
    };
  }

  getExpectedVolatility(hour, dayOfWeek) {
    // Volatilidad esperada basada en sesiones de trading
    const highVolatilityHours = [8, 9, 13, 14, 15, 16, 21, 22];
    const highVolatilityDays = [1, 2, 3, 4]; // Lunes a Jueves
    
    let volatility = 'low';
    
    if (highVolatilityHours.includes(hour) && highVolatilityDays.includes(dayOfWeek)) {
      volatility = 'high';
    } else if (highVolatilityHours.includes(hour) || highVolatilityDays.includes(dayOfWeek)) {
      volatility = 'medium';
    }
    
    return volatility;
  }
}

module.exports = TechnicalAnalyzer;
