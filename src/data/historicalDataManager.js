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

  // NUEVO: Analizar TODOS los patrones históricos para hora/minuto/día específicos
  async analyzeCompleteHistoricalPatterns(asset, currentHour, currentMinute, currentDay) {
    try {
      this.logger.info(`🔍 Analizando TODOS los patrones históricos para ${asset} en ${currentHour}:${currentMinute} (día ${currentDay})`);
      
      // CONSULTA SQL MEJORADA: Analizar patrones por hora específica CON RANGO
      const hourlyQuery = `
        SELECT 
          COUNT(*) as total_occurrences,
          SUM(CASE 
            WHEN (SELECT close FROM candles c2 WHERE c2.asset = ? AND c2.timestamp = c1.timestamp + 60000) > c1.close 
            THEN 1 ELSE 0 
          END) as up_movements,
          AVG(c1.close) as avg_price,
          AVG(ABS(c1.close - c1.open)) as avg_volatility,
          AVG(CASE 
            WHEN (SELECT close FROM candles c2 WHERE c2.asset = ? AND c2.timestamp = c1.timestamp + 60000) > c1.close 
            THEN ((SELECT close FROM candles c2 WHERE c2.asset = ? AND c2.timestamp = c1.timestamp + 60000) - c1.close) / c1.close * 100
            ELSE (c1.close - (SELECT close FROM candles c2 WHERE c2.asset = ? AND c2.timestamp = c1.timestamp + 60000)) / c1.close * 100
          END) as avg_movement_strength
        FROM candles c1 
        WHERE c1.asset = ? 
        AND c1.hour = ? 
        AND (c1.minute BETWEEN ? - 2 AND ? + 2)
        AND EXISTS (SELECT 1 FROM candles c2 WHERE c2.asset = ? AND c2.timestamp = c1.timestamp + 60000)
      `;
      
      const hourlyPattern = await this.db.get(hourlyQuery, [asset, asset, asset, asset, asset, currentHour, currentMinute, currentMinute, asset]);
      
      // CONSULTA SQL: Patrones por día de la semana
      const dailyQuery = `
        SELECT 
          COUNT(*) as total_occurrences,
          SUM(CASE 
            WHEN (SELECT close FROM candles c2 WHERE c2.asset = ? AND c2.timestamp = c1.timestamp + 60000) > c1.close 
            THEN 1 ELSE 0 
          END) as up_movements,
          AVG(ABS(c1.close - c1.open)) as avg_volatility
        FROM candles c1 
        WHERE c1.asset = ? 
        AND c1.day_of_week = ?
        AND c1.hour = ?
        AND EXISTS (SELECT 1 FROM candles c2 WHERE c2.asset = ? AND c2.timestamp = c1.timestamp + 60000)
      `;
      
      const dailyPattern = await this.db.get(dailyQuery, [asset, asset, currentDay, currentHour, asset]);
      
      // CONSULTA SQL: Patrones de secuencias (últimas 5 velas)
      const sequenceQuery = `
        SELECT 
          COUNT(*) as total_sequences,
          SUM(CASE WHEN next_up = 1 THEN 1 ELSE 0 END) as successful_predictions
        FROM (
          SELECT 
            c1.timestamp,
            CASE WHEN c6.close > c5.close THEN 1 ELSE 0 END as next_up
          FROM candles c1
          JOIN candles c2 ON c2.asset = c1.asset AND c2.timestamp = c1.timestamp + 60000
          JOIN candles c3 ON c3.asset = c1.asset AND c3.timestamp = c1.timestamp + 120000  
          JOIN candles c4 ON c4.asset = c1.asset AND c4.timestamp = c1.timestamp + 180000
          JOIN candles c5 ON c5.asset = c1.asset AND c5.timestamp = c1.timestamp + 240000
          JOIN candles c6 ON c6.asset = c1.asset AND c6.timestamp = c1.timestamp + 300000
          WHERE c1.asset = ?
          AND c1.hour = ?
          AND c1.minute >= ? - 5 AND c1.minute <= ? + 5
        )
      `;
      
      const sequencePattern = await this.db.get(sequenceQuery, [asset, currentHour, currentMinute, currentMinute]);
      
      // CALCULAR PREDICCIÓN MEJORADA BASADA EN PATRONES HISTÓRICOS MASIVOS
      const hourlyAccuracy = hourlyPattern.total_occurrences > 0 ? 
        (hourlyPattern.up_movements / hourlyPattern.total_occurrences) * 100 : 50;
      
      const dailyAccuracy = dailyPattern.total_occurrences > 0 ? 
        (dailyPattern.up_movements / dailyPattern.total_occurrences) * 100 : 50;
      
      const sequenceAccuracy = sequencePattern.total_sequences > 0 ? 
        (sequencePattern.successful_predictions / sequencePattern.total_sequences) * 100 : 50;
      
      // NUEVA LÓGICA: Calcular fuerza de señal basada en datos robustos
      const minOccurrences = 100; // Mínimo para considerar señal confiable
      const totalOccurrences = hourlyPattern.total_occurrences + dailyPattern.total_occurrences + sequencePattern.total_sequences;
      
      // DECISIÓN HISTÓRICA MEJORADA CON MÚLTIPLES FACTORES
      let weightedAccuracy = (hourlyAccuracy * 0.5) + (dailyAccuracy * 0.3) + (sequenceAccuracy * 0.2);
      
      // BONUS POR DATOS ROBUSTOS
      const dataRobustness = Math.min(totalOccurrences / minOccurrences, 3.0); // Max 3x bonus
      
      // BONUS POR CONSISTENCIA ENTRE PATRONES
      const patternConsistency = 100 - Math.abs(hourlyAccuracy - dailyAccuracy);
      const consistencyBonus = patternConsistency > 80 ? 5 : patternConsistency > 60 ? 3 : 0;
      
      // BONUS POR FUERZA DE MOVIMIENTO HISTÓRICO
      const movementStrength = hourlyPattern.avg_movement_strength || 0;
      const strengthBonus = Math.abs(movementStrength) > 0.5 ? 3 : Math.abs(movementStrength) > 0.3 ? 2 : 0;
      
      // APLICAR MEJORAS
      if (Math.abs(weightedAccuracy - 50) > 3) { // Solo si hay tendencia clara
        weightedAccuracy += (weightedAccuracy > 50 ? 1 : -1) * (consistencyBonus + strengthBonus);
        weightedAccuracy *= dataRobustness;
      }
      
      // DECISIÓN FINAL MEJORADA
      const historicalDirection = weightedAccuracy > 55 ? 'UP' : weightedAccuracy < 45 ? 'DOWN' : 'NEUTRAL';
      let historicalConfidence = Math.abs(weightedAccuracy - 50) * 1.5; // Más sensible
      
      // BOOST DE CONFIANZA POR DATOS MASIVOS
      if (totalOccurrences > 1000) {
        historicalConfidence *= 1.2; // 20% más confianza con muchos datos
      }
      
      historicalConfidence = Math.min(historicalConfidence, 85); // Cap máximo
      
      this.logger.info(`📊 PATRONES HISTÓRICOS ${asset}: ${hourlyPattern.total_occurrences} ocurrencias horarias, ${dailyPattern.total_occurrences} diarias, ${sequencePattern.total_sequences} secuencias`);
      this.logger.info(`🎯 PREDICCIÓN HISTÓRICA: ${historicalDirection} (${historicalConfidence.toFixed(1)}% confianza)`);
      
      return {
        direction: historicalDirection,
        confidence: historicalConfidence,
        hourlyAccuracy: hourlyAccuracy,
        dailyAccuracy: dailyAccuracy,
        sequenceAccuracy: sequenceAccuracy,
        totalPatterns: hourlyPattern.total_occurrences + dailyPattern.total_occurrences + sequencePattern.total_sequences,
        avgVolatility: (hourlyPattern.avg_volatility + dailyPattern.avg_volatility) / 2
      };
      
    } catch (error) {
      this.logger.error(`❌ Error analizando patrones históricos completos:`, error);
      return {
        direction: 'NEUTRAL',
        confidence: 0,
        totalPatterns: 0,
        avgVolatility: 0
      };
    }
  }

  // NUEVO: Obtener velas históricas recientes para análisis
  async getRecentHistoricalCandles(asset, limit = 100) {
    try {
      const query = `
        SELECT timestamp, open, high, low, close, volume
        FROM candles 
        WHERE asset = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
      `;
      
      const rows = await this.db.all(query, [asset, limit]);
      
      // Convertir a formato de velas y ordenar cronológicamente
      const candles = rows.reverse().map(row => ({
        timestamp: row.timestamp,
        open: row.open,
        high: row.high,
        low: row.low,
        close: row.close,
        volume: row.volume || 0
      }));
      
      return candles;
      
    } catch (error) {
      this.logger.error(`❌ Error obteniendo velas históricas para ${asset}:`, error);
      return []; // Retornar array vacío en caso de error
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

  // NUEVO: Análisis Multi-Timeframe COMPLETO usando TODOS los datos históricos
  async performMultiTimeframeAnalysis(asset, realtimeCandles) {
    try {
      const currentTime = new Date();
      const currentHour = currentTime.getHours();
      const currentMinute = currentTime.getMinutes();
      const currentDay = currentTime.getDay(); // 0=Domingo, 1=Lunes, etc.
      
      this.logger.info(`🔍 ANÁLISIS COMPLETO ${asset}: Usando TODOS los datos históricos (${currentHour}:${currentMinute}, día ${currentDay})`);
      
      // 1. ANÁLISIS DE PATRONES HISTÓRICOS MASIVOS (TODOS LOS DATOS)
      const historicalPatterns = await this.analyzeCompleteHistoricalPatterns(asset, currentHour, currentMinute, currentDay);
      
      // 2. ANÁLISIS TÉCNICO CON DATOS RECIENTES (MÚLTIPLES TIMEFRAMES)
      const recentCandles = {
        short: await this.getRecentHistoricalCandles(asset, 60),    // 1 hora
        medium: await this.getRecentHistoricalCandles(asset, 720),  // 12 horas
        long: await this.getRecentHistoricalCandles(asset, 2880)    // 48 horas
      };
      
      // 3. COMBINAR CON TIEMPO REAL
      const analysis = {
        // Análisis técnico tradicional
        short: this.analyzeTimeframe([...recentCandles.short, ...realtimeCandles], 5),
        medium: this.analyzeTimeframe([...recentCandles.medium, ...realtimeCandles], 15),
        long: this.analyzeTimeframe([...recentCandles.long, ...realtimeCandles], 60),
        
        // Análisis histórico masivo (NUEVO)
        historical: historicalPatterns,
        
        // Volatilidad y calidad
        volatility: this.calculateVolatility([...recentCandles.short, ...realtimeCandles]),
        quality: 0
      };

      // 4. CALCULAR CALIDAD HÍBRIDA (técnico + histórico)
      analysis.quality = this.calculateHybridQuality(analysis);
      
      this.logger.info(`📊 Análisis completo: ${recentCandles.short.length + recentCandles.medium.length + recentCandles.long.length} velas técnicas + ${historicalPatterns.totalPatterns} patrones históricos`);
      
      return analysis;
      
    } catch (error) {
      this.logger.error(`❌ Error en análisis completo para ${asset}:`, error);
      throw error;
    }
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

  // NUEVO: Calcular calidad híbrida (técnico + histórico)
  calculateHybridQuality(analysis) {
    let quality = 0;
    let factors = 0;
    
    // Factor 1: Calidad técnica tradicional
    const technicalQuality = this.calculateSignalQuality(analysis);
    quality += technicalQuality * 0.4; // 40% peso técnico
    factors++;
    
    // Factor 2: Confianza histórica
    if (analysis.historical && analysis.historical.confidence > 0) {
      quality += analysis.historical.confidence * 0.6; // 60% peso histórico
      factors++;
      
      // Bonus por muchos patrones históricos
      if (analysis.historical.totalPatterns > 1000) {
        quality += 10; // Bonus por datos robustos
      }
      
      // Bonus por consistencia entre patrones
      const patternConsistency = Math.abs(analysis.historical.hourlyAccuracy - analysis.historical.dailyAccuracy);
      if (patternConsistency < 10) { // Patrones consistentes
        quality += 5;
      }
    }
    
    // Factor 3: Alineación técnico-histórica
    if (analysis.historical && analysis.medium) {
      const technicalDirection = analysis.medium.direction;
      const historicalDirection = analysis.historical.direction;
      
      if (technicalDirection === historicalDirection && technicalDirection !== 'NEUTRAL') {
        quality += 15; // Gran bonus por alineación
      } else if (technicalDirection !== 'NEUTRAL' && historicalDirection !== 'NEUTRAL' && technicalDirection !== historicalDirection) {
        quality -= 10; // Penalty por conflicto
      }
    }
    
    return Math.max(0, Math.min(100, quality / Math.max(1, factors)));
  }

  // Tomar decisión basada en análisis multi-timeframe HÍBRIDO
  makeMultiTimeframeDecision(analysis, historicalPatterns) {
    const { short, medium, long, historical, quality, volatility } = analysis;
    
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
    
    // Voto del timeframe largo (peso: 15%)
    if (long.direction === 'UP') upVotes += 0.15;
    else if (long.direction === 'DOWN') downVotes += 0.15;
    else neutralVotes += 0.15;
    
    // NUEVO: Voto histórico (peso: 35% - MÁS IMPORTANTE)
    if (historical && historical.direction === 'UP') upVotes += 0.35;
    else if (historical && historical.direction === 'DOWN') downVotes += 0.35;
    else neutralVotes += 0.35;
    
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

  // Filtros de calidad MEJORADOS Y RELAJADOS para aprovechar datos históricos
  passesQualityFilters(analysis, decision) {
    // Filtro 1: Calidad mínima SÚPER RELAJADA para datos históricos
    if (analysis.quality < 15) {
      return false;
    }
    
    // Filtro 2: Confianza mínima RELAJADA especialmente para histórico
    let minConfidence = 35; // Base relajada
    
    // BONUS: Si tiene datos históricos fuertes, relajar más
    if (analysis.historical && analysis.historical.totalPatterns > 500) {
      minConfidence = 25; // Súper relajado con muchos datos
    }
    
    if (decision.confidence < minConfidence) {
      return false;
    }
    
    // Filtro 3: Volatilidad SÚPER RELAJADA
    if (analysis.volatility < 0.05 || analysis.volatility > 20.0) {
      return false;
    }
    
    // Filtro 4: NUEVO - Priorizar señales históricas fuertes
    if (analysis.historical && analysis.historical.confidence > 30) {
      return true; // Pasa automáticamente si histórico es fuerte
    }
    
    // Filtro 5: Alineación SÚPER RELAJADA
    const directions = [analysis.short.direction, analysis.medium.direction, analysis.long.direction];
    const upCount = directions.filter(d => d === 'UP').length;
    const downCount = directions.filter(d => d === 'DOWN').length;
    
    // Permitir incluso con solo histórico alineado
    if (analysis.historical && analysis.historical.direction !== 'NEUTRAL') {
      return true;
    }
    
    if (upCount < 1 && downCount < 1) {
      return false; // No hay suficiente alineación
    }
    
    // Filtro 6: Niveles importantes RELAJADO
    if (analysis.medium && analysis.medium.levels && analysis.medium.levels.nearLevel !== 'NONE') {
      // Permitir si hay datos históricos que lo respalden
      if (analysis.historical && analysis.historical.confidence > 20) {
        return true;
      }
      // O si hay momentum moderado
      if (Math.abs(analysis.short.momentum) < 0.5) {
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
      // ANÁLISIS MULTI-TIMEFRAME CON DATOS HISTÓRICOS
      const analysis = await this.performMultiTimeframeAnalysis(asset, realtimeCandles);
      
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
