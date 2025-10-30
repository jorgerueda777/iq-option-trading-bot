const IQOptionAPI = require('iqoption');
const Logger = require('../utils/logger');

class IQOptionAPIWrapper {
  constructor() {
    this.logger = new Logger('IQOption');
    this.api = null;
    this.isConnected = false;
    this.credentials = {
      email: process.env.IQ_EMAIL || '',
      password: process.env.IQ_PASSWORD || ''
    };
    this.activeOperations = new Map();
  }

  async initialize() {
    try {
      this.logger.info('🔌 Inicializando conexión con IQ Option...');
      
      if (!this.credentials.email || !this.credentials.password) {
        throw new Error('Credenciales de IQ Option no configuradas. Configura IQ_EMAIL e IQ_PASSWORD en variables de entorno.');
      }

      this.api = new IQOptionAPI(this.credentials.email, this.credentials.password);
      
      // Conectar
      await this.connect();
      
      this.logger.info('✅ Conexión con IQ Option establecida');
      
    } catch (error) {
      this.logger.error('❌ Error inicializando IQ Option:', error);
      throw error;
    }
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.api.connect()
        .then(() => {
          this.isConnected = true;
          this.logger.info('🔗 Conectado a IQ Option');
          
          // Configurar cuenta demo/real
          this.api.changeBalance('PRACTICE'); // Cambiar a 'REAL' para cuenta real
          
          resolve();
        })
        .catch((error) => {
          this.isConnected = false;
          this.logger.error('❌ Error conectando a IQ Option:', error);
          reject(error);
        });
    });
  }

  // Ejecutar operación binaria M1
  async placeBinaryOption(params) {
    try {
      if (!this.isConnected) {
        throw new Error('No hay conexión con IQ Option');
      }

      const { asset, amount, direction, duration = 60 } = params;
      
      this.logger.info(`🚀 Ejecutando operación M1:`);
      this.logger.info(`   📈 Asset: ${asset}`);
      this.logger.info(`   💰 Monto: $${amount}`);
      this.logger.info(`   🎯 Dirección: ${direction.toUpperCase()}`);
      this.logger.info(`   ⏱️ Duración: ${duration}s`);

      // Mapear dirección
      const iqDirection = direction.toLowerCase() === 'up' ? 'call' : 'put';
      
      // Ejecutar operación
      const result = await this.api.trade({
        active: asset,
        amount: amount,
        direction: iqDirection,
        duration: duration
      });

      if (result && result.id) {
        // Guardar operación activa
        this.activeOperations.set(result.id, {
          id: result.id,
          asset: asset,
          amount: amount,
          direction: iqDirection,
          startTime: new Date(),
          duration: duration,
          status: 'active'
        });

        this.logger.info(`✅ Operación ejecutada - ID: ${result.id}`);
        
        return {
          success: true,
          id: result.id,
          message: 'Operación ejecutada exitosamente'
        };
      } else {
        throw new Error('No se pudo ejecutar la operación');
      }

    } catch (error) {
      this.logger.error('❌ Error ejecutando operación:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Obtener resultado de operación
  async getOperationResult(operationId) {
    try {
      const operation = this.activeOperations.get(operationId);
      if (!operation) {
        throw new Error(`Operación ${operationId} no encontrada`);
      }

      // Verificar si ya pasó el tiempo
      const elapsed = Date.now() - operation.startTime.getTime();
      if (elapsed < operation.duration * 1000) {
        return null; // Aún no termina
      }

      // Obtener resultado de IQ Option
      const result = await this.api.getPositions('binary-option');
      const position = result.find(pos => pos.id === operationId);

      if (position) {
        const operationResult = {
          id: operationId,
          win: position.win === 'win',
          profit: position.win === 'win' ? position.win_amount : -position.amount,
          closePrice: position.close_quote,
          openPrice: position.open_quote
        };

        // Remover de operaciones activas
        this.activeOperations.delete(operationId);

        this.logger.info(`📊 Resultado obtenido para ${operationId}: ${operationResult.win ? 'WIN' : 'LOSS'}`);
        
        return operationResult;
      }

      return null;

    } catch (error) {
      this.logger.error(`❌ Error obteniendo resultado ${operationId}:`, error);
      return null;
    }
  }

  // Obtener balance
  async getBalance() {
    try {
      if (!this.isConnected) return 0;
      
      const balance = await this.api.getBalance();
      return balance.amount || 0;
    } catch (error) {
      this.logger.error('❌ Error obteniendo balance:', error);
      return 0;
    }
  }

  // Obtener assets disponibles
  async getAvailableAssets() {
    try {
      if (!this.isConnected) return [];
      
      const assets = await this.api.getCandles('EURUSD-OTC', 60, 1, Date.now());
      // Retornar lista de assets comunes
      return [
        'EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC',
        'USDCAD-OTC', 'EURJPY-OTC', 'GBPJPY-OTC', 'EURGBP-OTC'
      ];
    } catch (error) {
      this.logger.error('❌ Error obteniendo assets:', error);
      return [];
    }
  }

  // Verificar si asset está abierto
  async isAssetOpen(asset) {
    try {
      // Obtener datos recientes para verificar si está activo
      const candles = await this.api.getCandles(asset, 60, 1, Date.now());
      return candles && candles.length > 0;
    } catch (error) {
      return false;
    }
  }

  // Obtener velas actuales
  async getCurrentCandles(asset, count = 5) {
    try {
      if (!this.isConnected) {
        throw new Error('No hay conexión con IQ Option');
      }
      
      // Obtener velas de 1 minuto (60 segundos)
      const endTime = Date.now();
      const candles = await this.api.getCandles(asset, 60, count, endTime);
      
      if (!candles || candles.length === 0) {
        this.logger.warn(`⚠️ No se obtuvieron velas para ${asset}`);
        return null;
      }
      
      // Convertir formato si es necesario
      const formattedCandles = candles.map(candle => ({
        open: candle.open,
        high: candle.max,
        low: candle.min,
        close: candle.close,
        volume: candle.volume || 0,
        timestamp: candle.from * 1000 // Convertir a milliseconds
      }));
      
      this.logger.info(`📊 Obtenidas ${formattedCandles.length} velas de ${asset}`);
      return formattedCandles;
      
    } catch (error) {
      this.logger.error(`❌ Error obteniendo velas de ${asset}:`, error);
      return null;
    }
  }

  // Obtener precio actual
  async getCurrentPrice(asset) {
    try {
      const candles = await this.getCurrentCandles(asset, 1);
      if (candles && candles.length > 0) {
        return candles[0].close;
      }
      return null;
    } catch (error) {
      this.logger.error(`❌ Error obteniendo precio de ${asset}:`, error);
      return null;
    }
  }

  // Verificar conexión
  isConnected() {
    return this.isConnected;
  }

  // Cerrar conexión
  async close() {
    try {
      if (this.api && this.isConnected) {
        await this.api.disconnect();
        this.isConnected = false;
        this.logger.info('🔌 Desconectado de IQ Option');
      }
    } catch (error) {
      this.logger.error('❌ Error cerrando conexión:', error);
    }
  }
}

module.exports = IQOptionAPIWrapper;
