const sqlite3 = require('sqlite3').verbose();
const { open } = require('sqlite');
const Logger = require('../utils/logger');

class HistoricalDataManager {
  constructor() {
    this.logger = new Logger('HistoricalData');
    this.db = null;
    this.patternCache = new Map(); // Cache de patrones por asset
  }

  async initialize() {
    try {
      this.logger.info('📊 Conectando a base de datos histórica...');
      
      this.db = await open({
        filename: './data/historical.db',
        driver: sqlite3.Database
      });
      
      this.logger.info('✅ Base de datos histórica conectada');
      
      // Verificar datos disponibles de forma rápida (sin contar todo)
      try {
        const sample = await this.db.get('SELECT COUNT(*) as count FROM candles LIMIT 1');
        this.logger.info('📊 Base de datos verificada - Datos históricos disponibles');
      } catch (error) {
        this.logger.warn('⚠️ No se pudo verificar datos, pero la conexión está activa');
      }
      
    } catch (error) {
      this.logger.error('❌ Error conectando a datos históricos:', error);
      throw error;
    }
  }

  // Obtener estadísticas de datos
  async getDataStats() {
    try {
      const totalCandles = await this.db.get('SELECT COUNT(*) as count FROM candles');
      const assets = await this.db.get('SELECT COUNT(DISTINCT asset) as count FROM candles');
      
      return {
        totalCandles: totalCandles.count,
        assets: assets.count
      };
    } catch (error) {
      this.logger.error('Error obteniendo estadísticas:', error);
      return { totalCandles: 0, assets: 0 };
    }
  }

  // Analizar patrones históricos para un asset
  async analyzeHistoricalPatterns(asset, maxCandles = 50000) {
    try {
      // Verificar cache
      if (this.patternCache.has(asset)) {
        return this.patternCache.get(asset);
      }

      this.logger.info(`🔍 Analizando patrones históricos para ${asset}...`);
      
      // Obtener datos históricos
      const query = `
        SELECT open, high, low, close, volume, timestamp, hour, minute, day_of_week
        FROM candles 
        WHERE asset = ?
        ORDER BY timestamp DESC 
        LIMIT ?
      `;
      
      const candles = await this.db.all(query, [asset, maxCandles]);
      
      if (candles.length < 100) {
        throw new Error(`Insuficientes datos históricos para ${asset}: ${candles.length}`);
      }

      candles.reverse(); // Orden cronológico

      // Analizar patrones de velas
      const patterns = this.findCandlePatterns(candles);
      
      // Guardar en cache
      this.patternCache.set(asset, patterns);
      
      this.logger.info(`✅ ${asset}: ${patterns.totalPatterns.toLocaleString()} patrones analizados (${patterns.accuracy.toFixed(2)}% precisión)`);
      
      return patterns;
      
    } catch (error) {
      this.logger.error(`❌ Error analizando patrones ${asset}:`, error);
      throw error;
    }
  }

  // Encontrar patrones de velas
  findCandlePatterns(candles) {
    let totalPatterns = 0;
    let correctPredictions = 0;
    
    const sequencePatterns = {
      '5green': { total: 0, correct: 0 },
      '4green': { total: 0, correct: 0 },
      '3green': { total: 0, correct: 0 },
      '5red': { total: 0, correct: 0 },
      '4red': { total: 0, correct: 0 },
      '3red': { total: 0, correct: 0 },
      'mixed': { total: 0, correct: 0 }
    };

    const hourlyPatterns = {};
    const dailyPatterns = {};

    // Analizar cada secuencia de 6 velas (5 para patrón + 1 para verificar)
    for (let i = 5; i < candles.length; i++) {
      const pattern = candles.slice(i - 5, i);
      const nextCandle = candles[i];
      
      totalPatterns++;
      
      // Contar velas verdes vs rojas
      let greenCount = 0;
      pattern.forEach(candle => {
        if (candle.close > candle.open) greenCount++;
      });
      
      // Predicción basada en mayoría
      const prediction = greenCount > 2 ? 'UP' : 'DOWN';
      const actualResult = nextCandle.close > pattern[4].close ? 'UP' : 'DOWN';
      
      if (prediction === actualResult) {
        correctPredictions++;
      }
      
      // Clasificar patrón
      let patternType = 'mixed';
      if (greenCount === 5) patternType = '5green';
      else if (greenCount === 4) patternType = '4green';
      else if (greenCount === 3) patternType = '3green';
      else if (greenCount === 0) patternType = '5red';
      else if (greenCount === 1) patternType = '4red';
      else if (greenCount === 2) patternType = '3red';
      
      sequencePatterns[patternType].total++;
      if (prediction === actualResult) {
        sequencePatterns[patternType].correct++;
      }
      
      // Patrones por hora
      const hour = pattern[4].hour;
      if (!hourlyPatterns[hour]) {
        hourlyPatterns[hour] = { total: 0, correct: 0, upCount: 0 };
      }
      hourlyPatterns[hour].total++;
      if (prediction === actualResult) hourlyPatterns[hour].correct++;
      if (actualResult === 'UP') hourlyPatterns[hour].upCount++;
      
      // Patrones por día
      const day = pattern[4].day_of_week;
      if (!dailyPatterns[day]) {
        dailyPatterns[day] = { total: 0, correct: 0, upCount: 0 };
      }
      dailyPatterns[day].total++;
      if (prediction === actualResult) dailyPatterns[day].correct++;
      if (actualResult === 'UP') dailyPatterns[day].upCount++;
    }

    // Calcular precisiones
    for (const pattern in sequencePatterns) {
      const p = sequencePatterns[pattern];
      p.accuracy = p.total > 0 ? (p.correct / p.total) * 100 : 0;
    }

    for (const hour in hourlyPatterns) {
      const h = hourlyPatterns[hour];
      h.accuracy = h.total > 0 ? (h.correct / h.total) * 100 : 0;
      h.upTendency = h.total > 0 ? (h.upCount / h.total) * 100 : 50;
    }

    for (const day in dailyPatterns) {
      const d = dailyPatterns[day];
      d.accuracy = d.total > 0 ? (d.correct / d.total) * 100 : 0;
      d.upTendency = d.total > 0 ? (d.upCount / d.total) * 100 : 50;
    }

    return {
      accuracy: totalPatterns > 0 ? (correctPredictions / totalPatterns) * 100 : 0,
      totalPatterns: totalPatterns,
      correctPredictions: correctPredictions,
      sequencePatterns: sequencePatterns,
      hourlyPatterns: hourlyPatterns,
      dailyPatterns: dailyPatterns,
      analyzedCandles: candles.length
    };
  }

  // NUEVO: Análisis Multi-Timeframe para M1 (1 minuto) en IQ Option
  performMultiTimeframeAnalysis(candles) {
    const analysis = {
      short: this.analyzeTimeframe(candles, 5),     // 5 minutos - Momentum inmediato
      medium: this.analyzeTimeframe(candles, 15),   // 15 minutos - Tendencia corta
      long: this.analyzeTimeframe(candles, 60),     // 1 hora - Contexto
      volatility: this.calculateVolatility(candles),
      quality: 0
    };

    // Calcular calidad de la señal
    analysis.quality = this.calculateSignalQuality(analysis);
    
    return analysis;
  }

  // Analizar un timeframe específico
  analyzeTimeframe(candles, period) {
    const relevantCandles = candles.slice(-Math.min(period, candles.length));
    
    if (relevantCandles.length < 5) {
      return { direction: 'NEUTRAL', strength: 0, confidence: 0 };
    }

    // Análisis de momentum
    const momentum = this.calculateMomentum(relevantCandles);
    
    // Análisis de tendencia
    const trend = this.calculateTrend(relevantCandles);
    
    // Análisis de soporte/resistencia
    const levels = this.findSupportResistance(relevantCandles);
    
    // Análisis de patrones de velas
    const candlePattern = this.analyzeCandlePatterns(relevantCandles);
    
    return {
      direction: trend.direction,
      strength: trend.strength,
      momentum: momentum,
      levels: levels,
      pattern: candlePattern,
      confidence: this.calculateTimeframeConfidence(trend, momentum, levels, candlePattern)
    };
  }

  // Calcular momentum (velocidad de cambio de precio)
  calculateMomentum(candles) {
    if (candles.length < 3) return 0;
    
    const recent = candles.slice(-3);
    const older = candles.slice(-6, -3);
    
    const recentAvg = recent.reduce((sum, c) => sum + c.close, 0) / recent.length;
    const olderAvg = older.length > 0 ? older.reduce((sum, c) => sum + c.close, 0) / older.length : recentAvg;
    
    return ((recentAvg - olderAvg) / olderAvg) * 100;
  }

  // Calcular tendencia principal
  calculateTrend(candles) {
    if (candles.length < 5) return { direction: 'NEUTRAL', strength: 0 };
    
    const prices = candles.map(c => c.close);
    const firstHalf = prices.slice(0, Math.floor(prices.length / 2));
    const secondHalf = prices.slice(Math.floor(prices.length / 2));
    
    const firstAvg = firstHalf.reduce((a, b) => a + b) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b) / secondHalf.length;
    
    const change = ((secondAvg - firstAvg) / firstAvg) * 100;
    
    return {
      direction: change > 0.1 ? 'UP' : change < -0.1 ? 'DOWN' : 'NEUTRAL',
      strength: Math.abs(change),
      change: change
    };
  }

  // Encontrar niveles de soporte y resistencia
  findSupportResistance(candles) {
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    
    const resistance = Math.max(...highs);
    const support = Math.min(...lows);
    const currentPrice = candles[candles.length - 1].close;
    
    const distanceToResistance = ((resistance - currentPrice) / currentPrice) * 100;
    const distanceToSupport = ((currentPrice - support) / currentPrice) * 100;
    
    return {
      resistance: resistance,
      support: support,
      distanceToResistance: distanceToResistance,
      distanceToSupport: distanceToSupport,
      nearLevel: distanceToResistance < 0.5 ? 'RESISTANCE' : distanceToSupport < 0.5 ? 'SUPPORT' : 'NONE'
    };
  }

  // Analizar patrones de velas
  analyzeCandlePatterns(candles) {
    if (candles.length < 5) return { pattern: 'INSUFFICIENT', strength: 0 };
    
    const last5 = candles.slice(-5);
    let greenCount = 0;
    let redCount = 0;
    let dojiCount = 0;
    
    last5.forEach(candle => {
      const bodySize = Math.abs(candle.close - candle.open);
      const shadowSize = candle.high - candle.low;
      
      if (bodySize < shadowSize * 0.1) {
        dojiCount++; // Doji (indecisión)
      } else if (candle.close > candle.open) {
        greenCount++;
      } else {
        redCount++;
      }
    });
    
    let pattern = 'MIXED';
    let strength = 0;
    
    if (greenCount >= 4) {
      pattern = 'STRONG_BULLISH';
      strength = 0.8;
    } else if (redCount >= 4) {
      pattern = 'STRONG_BEARISH';
      strength = 0.8;
    } else if (greenCount >= 3) {
      pattern = 'BULLISH';
      strength = 0.6;
    } else if (redCount >= 3) {
      pattern = 'BEARISH';
      strength = 0.6;
    } else if (dojiCount >= 2) {
      pattern = 'INDECISION';
      strength = 0.3;
    }
    
    return { pattern, strength, greenCount, redCount, dojiCount };
  }

  // Calcular confianza del timeframe
  calculateTimeframeConfidence(trend, momentum, levels, candlePattern) {
    let confidence = 50; // Base
    
    // Bonus por tendencia clara
    if (trend.strength > 0.5) confidence += 15;
    if (trend.strength > 1.0) confidence += 10;
    
    // Bonus por momentum alineado
    if ((trend.direction === 'UP' && momentum > 0) || (trend.direction === 'DOWN' && momentum < 0)) {
      confidence += 10;
    }
    
    // Penalty por estar cerca de niveles importantes
    if (levels.nearLevel !== 'NONE') confidence -= 5;
    
    // Bonus por patrones de velas fuertes
    confidence += candlePattern.strength * 20;
    
    return Math.max(30, Math.min(85, confidence));
  }

  // Calcular volatilidad
  calculateVolatility(candles) {
    if (candles.length < 10) return 0;
    
    const returns = [];
    for (let i = 1; i < candles.length; i++) {
      const returnRate = (candles[i].close - candles[i-1].close) / candles[i-1].close;
      returns.push(returnRate);
    }
    
    const avgReturn = returns.reduce((a, b) => a + b) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - avgReturn, 2), 0) / returns.length;
    
    return Math.sqrt(variance) * 100; // Volatilidad en porcentaje
  }

  // Calcular calidad general de la señal
  calculateSignalQuality(analysis) {
    let quality = 0;
    let factors = 0;
    
    // Factor 1: Alineación de timeframes
    const directions = [analysis.short.direction, analysis.medium.direction, analysis.long.direction];
    const upCount = directions.filter(d => d === 'UP').length;
    const downCount = directions.filter(d => d === 'DOWN').length;
    
    if (upCount >= 2 || downCount >= 2) {
      quality += 30; // Bonus por alineación
      if (upCount === 3 || downCount === 3) quality += 20; // Bonus extra por alineación total
    }
    factors++;
    
    // Factor 2: Volatilidad óptima
    if (analysis.volatility > 0.5 && analysis.volatility < 3.0) {
      quality += 20; // Volatilidad ideal para trading
    } else if (analysis.volatility < 0.3) {
      quality -= 15; // Mercado muy plano
    } else if (analysis.volatility > 5.0) {
      quality -= 10; // Mercado muy volátil
    }
    factors++;
    
    // Factor 3: Fuerza de la tendencia media
    if (analysis.medium.strength > 1.0) {
      quality += 15;
    }
    factors++;
    
    // Factor 4: Momentum consistente
    const momentumStrong = Math.abs(analysis.short.momentum) > 0.5;
    if (momentumStrong) quality += 10;
    factors++;
    
    return Math.max(0, Math.min(100, quality / factors * 100));
  }

  // Tomar decisión basada en análisis multi-timeframe
  makeMultiTimeframeDecision(analysis, historicalPatterns) {
    const { short, medium, long, quality, volatility } = analysis;
    
    // Contar votos por dirección
    let upVotes = 0;
    let downVotes = 0;
    let neutralVotes = 0;
    
    // Voto del timeframe corto (peso: 30%)
    if (short.direction === 'UP') upVotes += 0.3;
    else if (short.direction === 'DOWN') downVotes += 0.3;
    else neutralVotes += 0.3;
    
    // Voto del timeframe medio (peso: 50% - más importante)
    if (medium.direction === 'UP') upVotes += 0.5;
    else if (medium.direction === 'DOWN') downVotes += 0.5;
    else neutralVotes += 0.5;
    
    // Voto del timeframe largo (peso: 20%)
    if (long.direction === 'UP') upVotes += 0.2;
    else if (long.direction === 'DOWN') downVotes += 0.2;
    else neutralVotes += 0.2;
    
    // Determinar dirección final
    const finalDirection = upVotes > downVotes ? 'UP' : 'DOWN';
    const directionStrength = Math.abs(upVotes - downVotes);
    
    // Calcular confianza multi-timeframe
    let confidence = 50; // Base
    
    // Bonus por alineación de timeframes
    confidence += directionStrength * 30;
    
    // Bonus por calidad de señal
    confidence += (quality / 100) * 20;
    
    // Bonus por volatilidad óptima
    if (volatility > 0.5 && volatility < 3.0) {
      confidence += 10;
    }
    
    // Bonus por momentum fuerte
    if (Math.abs(short.momentum) > 0.5) {
      confidence += 5;
    }
    
    // Bonus por tendencia media fuerte
    if (medium.strength > 1.0) {
      confidence += 10;
    }
    
    return {
      direction: finalDirection,
      confidence: Math.max(35, Math.min(90, confidence)),
      strength: directionStrength,
      quality: quality,
      analysis: analysis
    };
  }

  // Filtros de calidad para máxima precisión (RELAJADOS PARA M1)
  passesQualityFilters(analysis, decision) {
    // Filtro 1: Calidad mínima de señal (RELAJADO: 40 -> 25)
    if (analysis.quality < 25) {
      return false;
    }
    
    // Filtro 2: Confianza mínima (RELAJADO: 60 -> 45%)
    if (decision.confidence < 45) {
      return false;
    }
    
    // Filtro 3: Volatilidad no debe ser extrema (RELAJADO)
    if (analysis.volatility < 0.1 || analysis.volatility > 12.0) {
      return false;
    }
    
    // Filtro 4: Al menos 1 timeframe debe estar alineado (RELAJADO: 2 -> 1)
    const directions = [analysis.short.direction, analysis.medium.direction, analysis.long.direction];
    const upCount = directions.filter(d => d === 'UP').length;
    const downCount = directions.filter(d => d === 'DOWN').length;
    
    if (upCount < 1 && downCount < 1) {
      return false; // No hay suficiente alineación
    }
    
    // Filtro 5: Evitar trading cerca de niveles importantes
    if (analysis.medium.levels && analysis.medium.levels.nearLevel !== 'NONE') {
      // Permitir solo si hay momentum fuerte para romper el nivel
      if (Math.abs(analysis.short.momentum) < 1.0) {
        return false;
      }
    }
    
    return true; // Pasa todos los filtros
  }

  // NUEVO: Hacer predicción M1 (1 minuto) para IQ Option
  async makePrediction(asset, realtimeCandles) {
    // Con datos históricos, solo necesitamos 1 vela en tiempo real
    if (realtimeCandles.length < 1) {
      throw new Error('Se necesita al menos 1 vela en tiempo real');
    }
    
    try {
      // ANÁLISIS MULTI-TIMEFRAME
      const analysis = this.performMultiTimeframeAnalysis(realtimeCandles);
      
      const currentCandle = realtimeCandles[realtimeCandles.length - 1];
      
      // DECISIÓN MULTI-TIMEFRAME INTELIGENTE
      const decision = this.makeMultiTimeframeDecision(analysis, {});
      
      // FILTROS DE CALIDAD PARA MÁXIMA PRECISIÓN
      if (!this.passesQualityFilters(analysis, decision)) {
        this.logger.info(`⚠️ ${asset}: Señal rechazada por filtros de calidad`);
        return null; // No hacer predicción si no pasa los filtros
      }

      // CREAR PREDICCIÓN FINAL DE MÁXIMA PRECISIÓN
      const prediction = {
        asset: asset,
        direction: decision.direction,
        confidence: decision.confidence,
        timestamp: Date.now(),
        currentPrice: currentCandle.close,
        
        // Información del análisis M1 multi-timeframe
        multiTimeframe: {
          short: `${analysis.short.direction} (${analysis.short.confidence.toFixed(1)}%) - 5min`,
          medium: `${analysis.medium.direction} (${analysis.medium.confidence.toFixed(1)}%) - 15min`,
          long: `${analysis.long.direction} (${analysis.long.confidence.toFixed(1)}%) - 1h`,
          quality: analysis.quality.toFixed(1),
          volatility: analysis.volatility.toFixed(2)
        },
        
        // Información técnica detallada
        technicalInfo: {
          momentum: analysis.short.momentum.toFixed(3),
          trendStrength: analysis.medium.strength.toFixed(2),
          supportResistance: analysis.medium.levels ? {
            support: analysis.medium.levels.support.toFixed(5),
            resistance: analysis.medium.levels.resistance.toFixed(5),
            nearLevel: analysis.medium.levels.nearLevel
          } : null,
          candlePattern: analysis.short.pattern.pattern
        },
        
        // Razón de la predicción
        reasoning: this.generateReasoning(analysis, decision),
        
        // Metadatos
        metadata: {
          systemType: 'M1_MULTI_TIMEFRAME_PRECISION',
          timeframe: '1_MINUTE',
          candlesAnalyzed: realtimeCandles.length,
          filtersApplied: 5,
          historicalAccuracy: historicalPatterns.accuracy,
          nextCandleTime: new Date(Date.now() + 60000).toLocaleTimeString() // Próxima vela en 1 minuto
        }
      };

      this.logger.info(`🎯 PREDICCIÓN DE MÁXIMA PRECISIÓN: ${asset} → ${decision.direction} (${decision.confidence.toFixed(1)}%)`);
      this.logger.info(`📊 Calidad: ${analysis.quality.toFixed(1)}% | Volatilidad: ${analysis.volatility.toFixed(2)}%`);
      this.logger.info(`🔍 Timeframes: ${analysis.short.direction}/${analysis.medium.direction}/${analysis.long.direction}`);
      
      return prediction;
      
    } catch (error) {
      this.logger.error(`❌ Error haciendo predicción multi-timeframe ${asset}:`, error);
      throw error;
    }
  }

  // Generar explicación de la predicción
  generateReasoning(analysis, decision) {
    const reasons = [];
    
    // Razón principal por alineación de timeframes
    const directions = [analysis.short.direction, analysis.medium.direction, analysis.long.direction];
    const upCount = directions.filter(d => d === 'UP').length;
    const downCount = directions.filter(d => d === 'DOWN').length;
    
    if (upCount >= 2) {
      reasons.push(`${upCount}/3 timeframes alcistas`);
    } else if (downCount >= 2) {
      reasons.push(`${downCount}/3 timeframes bajistas`);
    }
    
    // Razón por momentum
    if (Math.abs(analysis.short.momentum) > 0.5) {
      reasons.push(`Momentum ${analysis.short.momentum > 0 ? 'alcista' : 'bajista'} fuerte`);
    }
    
    // Razón por tendencia
    if (analysis.medium.strength > 1.0) {
      reasons.push(`Tendencia ${analysis.medium.direction.toLowerCase()} sólida`);
    }
    
    // Razón por volatilidad
    if (analysis.volatility > 0.5 && analysis.volatility < 3.0) {
      reasons.push('Volatilidad óptima');
    }
    
    // Razón por patrón de velas
    if (analysis.short.pattern.strength > 0.6) {
      reasons.push(`Patrón ${analysis.short.pattern.pattern.toLowerCase()}`);
    }
    
    return reasons.join(', ');
  }

  // NUEVO: Guardar velas del día anterior en la base histórica
  async saveDailyCandles(asset, candles, date) {
    try {
      if (!candles || candles.length === 0) {
        this.logger.warn(`⚠️ No hay velas para guardar de ${asset} del ${date.toDateString()}`);
        return;
      }

      this.logger.info(`💾 Guardando ${candles.length} velas de ${asset} del ${date.toDateString()}`);

      const insertQuery = `
        INSERT OR REPLACE INTO candles 
        (asset, timestamp, open, high, low, close, volume, hour, minute, day_of_week)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;

      let savedCount = 0;
      for (const candle of candles) {
        const candleDate = new Date(candle.timestamp);
        
        await this.db.run(insertQuery, [
          asset,
          candle.timestamp,
          candle.open,
          candle.high,
          candle.low,
          candle.close,
          candle.volume || 0,
          candleDate.getHours(),
          candleDate.getMinutes(),
          candleDate.getDay()
        ]);
        
        savedCount++;
      }

      this.logger.info(`✅ ${savedCount} velas guardadas para ${asset} del ${date.toDateString()}`);
      
      // Limpiar cache de patrones para que se recalcule con los nuevos datos
      if (this.patternCache.has(asset)) {
        this.patternCache.delete(asset);
        this.logger.info(`🔄 Cache de patrones limpiado para ${asset}`);
      }

    } catch (error) {
      this.logger.error(`❌ Error guardando velas diarias para ${asset}:`, error);
      throw error;
    }
  }

  // NUEVO: Obtener estadísticas de la base de datos
  async getDatabaseStats() {
    try {
      const query = `
        SELECT 
          asset,
          COUNT(*) as total_candles,
          MIN(timestamp) as first_candle,
          MAX(timestamp) as last_candle
        FROM candles 
        GROUP BY asset
        ORDER BY total_candles DESC
      `;
      
      const stats = await this.db.all(query);
      
      return stats.map(stat => ({
        asset: stat.asset,
        totalCandles: stat.total_candles,
        firstCandle: new Date(stat.first_candle),
        lastCandle: new Date(stat.last_candle),
        daysOfData: Math.ceil((stat.last_candle - stat.first_candle) / (1000 * 60 * 60 * 24))
      }));
      
    } catch (error) {
      this.logger.error('Error obteniendo estadísticas de la base:', error);
      return [];
    }
  }

  async close() {
    if (this.db) {
      await this.db.close();
      this.logger.info('📊 Base de datos histórica cerrada');
    }
  }
}

module.exports = HistoricalDataManager;
