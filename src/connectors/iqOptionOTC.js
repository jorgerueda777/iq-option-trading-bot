const WebSocket = require('ws');
const axios = require('axios');
const EventEmitter = require('events');
const config = require('../../config/config');
const Logger = require('../utils/logger');

class IQOptionOTC extends EventEmitter {
  constructor() {
    super();
    this.logger = new Logger('IQOptionOTC');
    this.ws = null;
    this.isConnected = false;
    this.ssid = null;
    this.requestId = 1;
    this.subscriptions = new Map();
    this.session = axios.create();
    
    // URLs oficiales de IQ Option
    this.authUrl = 'https://auth.iqoption.com/api/v2/login';
    this.wsUrl = 'wss://ws.iqoption.com/echo/websocket';
    this.baseUrl = 'https://iqoption.com';
    
    // IDs específicos para activos OTC de IQ Option
    this.otcAssets = {
      'EURUSD-OTC': 76,
      'GBPUSD-OTC': 77,
      'USDJPY-OTC': 78,
      'AUDUSD-OTC': 79,
      'USDCAD-OTC': 80,
      'EURJPY-OTC': 81,
      'GBPJPY-OTC': 82,
      'EURGBP-OTC': 83,
      'AUDJPY-OTC': 84,
      'NZDUSD-OTC': 85,
      'USDCHF-OTC': 86,
      'EURCHF-OTC': 87,
      'GBPCHF-OTC': 88,
      'AUDCHF-OTC': 89,
      'CADCHF-OTC': 90,
      'AUDCAD-OTC': 91
    };
  }

  async connect() {
    try {
      this.logger.info('🚀 CONECTANDO A ACTIVOS OTC DE IQ OPTION...');
      
      // Login oficial
      await this.authenticateOTC();
      
      // WebSocket OTC
      await this.connectOTCWebSocket();
      
      this.logger.info('✅ CONECTADO A OTC DE IQ OPTION');
      
    } catch (error) {
      this.logger.error('❌ Error conectando a OTC IQ Option:', error.message);
      throw error;
    }
  }

  async authenticateOTC() {
    try {
      this.logger.info('🔐 Autenticando para OTC de IQ Option...');
      
      const loginPayload = {
        identifier: config.iqOption.email,
        password: config.iqOption.password,
        remember: false,
        affiliate_promocode: ""
      };

      this.logger.info(`📧 Login OTC: ${config.iqOption.email}`);

      const response = await this.session.post(this.authUrl, loginPayload, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Origin': 'https://iqoption.com',
          'Referer': 'https://iqoption.com/',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        timeout: 20000
      });

      this.logger.info(`📡 Respuesta OTC - Status: ${response.status}`);

      if (response.status === 200 && response.data) {
        if (response.data.isSuccessful === true || response.data.code === 'success') {
          
          // Extraer SSID
          if (response.headers['set-cookie']) {
            const ssidCookie = response.headers['set-cookie'].find(cookie => 
              cookie.includes('ssid=')
            );
            
            if (ssidCookie) {
              this.ssid = ssidCookie.match(/ssid=([^;]+)/)[1];
              this.logger.info('✅ SSID OTC obtenido de cookies');
            }
          }
          
          if (!this.ssid && response.data.ssid) {
            this.ssid = response.data.ssid;
            this.logger.info('✅ SSID OTC obtenido de respuesta');
          }

          if (!this.ssid) {
            throw new Error('No se pudo obtener SSID para OTC');
          }

          this.setupOTCCookies();
          this.logger.info('✅ LOGIN OTC EXITOSO');
          
        } else {
          throw new Error(`Login OTC falló: ${response.data.message || 'Credenciales incorrectas'}`);
        }
      } else {
        throw new Error(`Error HTTP OTC ${response.status}: ${response.statusText}`);
      }

    } catch (error) {
      this.logger.error('❌ Error autenticación OTC:', error.message);
      throw error;
    }
  }

  setupOTCCookies() {
    this.session.defaults.headers.Cookie = `ssid=${this.ssid}; platform=9`;
  }

  async connectOTCWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        this.logger.info('🔌 Conectando WebSocket OTC...');
        
        this.ws = new WebSocket(this.wsUrl, {
          headers: {
            'Origin': 'https://iqoption.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': `ssid=${this.ssid}; platform=9`
          }
        });

        let isResolved = false;

        this.ws.on('open', () => {
          this.logger.info('✅ WebSocket OTC conectado');
          this.isConnected = true;
          
          this.sendOTCAuth();
          this.setupOTCHeartbeat();
          
          if (!isResolved) {
            isResolved = true;
            resolve();
          }
        });

        this.ws.on('message', (data) => {
          this.handleOTCMessage(data);
        });

        this.ws.on('close', (code, reason) => {
          this.logger.warn(`❌ WebSocket OTC cerrado - Código: ${code}`);
          this.isConnected = false;
        });

        this.ws.on('error', (error) => {
          this.logger.error('❌ Error WebSocket OTC:', error.message);
          if (!isResolved) {
            isResolved = true;
            reject(error);
          }
        });

        setTimeout(() => {
          if (!isResolved) {
            isResolved = true;
            reject(new Error('Timeout conectando WebSocket OTC'));
          }
        }, 30000);

      } catch (error) {
        reject(error);
      }
    });
  }

  sendOTCAuth() {
    const authMessage = {
      name: 'ssid',
      msg: this.ssid
    };
    
    this.sendMessage(authMessage);
    this.logger.info('🔑 Autenticación OTC enviada');

    // Solicitar perfil OTC
    setTimeout(() => {
      this.requestOTCProfile();
    }, 2000);
  }

  requestOTCProfile() {
    const profileMessage = {
      name: 'sendMessage',
      msg: {
        name: 'get-profile',
        version: '1.0',
        body: {}
      },
      request_id: this.getRequestId()
    };
    
    this.sendMessage(profileMessage);
    this.logger.info('👤 Solicitando perfil OTC...');
  }

  setupOTCHeartbeat() {
    setInterval(() => {
      if (this.isConnected) {
        const heartbeat = {
          name: 'heartbeat',
          msg: Date.now()
        };
        this.sendMessage(heartbeat);
      }
    }, 30000);
  }

  handleOTCMessage(data) {
    try {
      const message = JSON.parse(data.toString());
      
      // Log solo mensajes importantes
      if (message.name !== 'heartbeat' && message.name !== 'timeSync') {
        // SILENCIOSO - No spam de eventos
      }
      
      switch (message.name) {
        case 'profile':
          this.handleOTCProfile(message.msg);
          break;
          
        case 'candle-generated':
          this.handleOTCCandle(message.msg);
          break;
          
        case 'quote-generated':
          this.handleOTCQuote(message.msg);
          break;
          
        case 'candles':
          this.handleOTCHistoricalCandles(message);
          break;
          
        case 'listInfoData':
          this.handleOTCAssetList(message.msg);
          break;
          
        default:
          break;
      }
      
      this.emit('message', message);
      
    } catch (error) {
      this.logger.error('Error procesando mensaje OTC:', error.message);
    }
  }

  handleOTCProfile(profileData) {
    if (profileData && profileData.email) {
      this.logger.info('✅ PERFIL OTC CONFIRMADO');
      this.logger.info(`👤 Usuario OTC: ${profileData.email}`);
      this.logger.info(`💰 Balance OTC: ${profileData.balance || 'N/A'}`);
      this.logger.info(`🏛️ Cuenta OTC: ${profileData.demo ? 'DEMO' : 'REAL'}`);
      
      // Suscribirse a activos OTC
      setTimeout(() => {
        this.subscribeToOTCAssets();
      }, 3000);
    }
  }

  subscribeToOTCAssets() {
    this.logger.info('🔔 Suscribiéndose a activos OTC...');
    
    // Suscribirse a los 7 activos OTC que funcionan
    const mainOTCAssets = ['EURUSD-OTC', 'GBPUSD-OTC', 'GBPJPY-OTC', 'EURJPY-OTC', 'EURGBP-OTC', 'USDCHF-OTC', 'AUDCAD-OTC'];
    
    mainOTCAssets.forEach(asset => {
      const activeId = this.otcAssets[asset];
      
      if (activeId) {
        // Suscripción a cotizaciones OTC
        const quoteSubscription = {
          name: 'subscribeMessage',
          msg: {
            name: 'quote-generated',
            params: {
              routingFilters: {
                active_id: activeId
              }
            }
          }
        };
        
        // Suscripción a velas OTC
        const candleSubscription = {
          name: 'subscribeMessage', 
          msg: {
            name: 'candle-generated',
            params: {
              routingFilters: {
                active_id: activeId,
                size: 60
              }
            }
          }
        };
        
        this.sendMessage(quoteSubscription);
        this.sendMessage(candleSubscription);
        
        this.logger.info(`🎯 Suscrito a OTC: ${asset} (ID: ${activeId})`);
      }
    });
  }

  handleOTCCandle(candleData) {
    try {
      if (!candleData || typeof candleData.active_id === 'undefined') {
        return;
      }
      
      const asset = this.getOTCAssetName(candleData.active_id);
      
      if (!asset || asset === 'UNKNOWN') {
        return;
      }
      
      const processedCandle = {
        asset: asset,
        timestamp: candleData.from * 1000,
        open: parseFloat(candleData.open),
        high: parseFloat(candleData.max),
        low: parseFloat(candleData.min),
        close: parseFloat(candleData.close),
        volume: candleData.volume || 0,
        timeframe: candleData.size || 60
      };
      
      this.logger.info(`📊 VELA OTC: ${asset} ${processedCandle.close}`);
      this.emit('candle', processedCandle);
      
    } catch (error) {
      this.logger.error('Error procesando vela OTC:', error.message);
    }
  }

  handleOTCQuote(quoteData) {
    try {
      if (!quoteData || typeof quoteData.active_id === 'undefined') {
        return;
      }
      
      const asset = this.getOTCAssetName(quoteData.active_id);
      
      if (!asset || asset === 'UNKNOWN') {
        return;
      }
      
      const price = parseFloat(quoteData.value);
      
      if (isNaN(price)) {
        return;
      }
      
      const processedQuote = {
        asset: asset,
        timestamp: Date.now(),
        bid: price,
        ask: price,
        spread: 0
      };
      
      // SILENCIOSO - No spam de cotizaciones
      this.emit('quote', processedQuote);
      
      // SOLUCIÓN: Crear velas artificiales cada minuto
      this.createArtificialCandle(asset, price);
      
    } catch (error) {
      this.logger.error('Error procesando cotización OTC:', error.message);
    }
  }

  // NUEVO: Crear velas artificiales a partir de cotizaciones
  createArtificialCandle(asset, price) {
    const now = Date.now();
    const currentMinute = Math.floor(now / 60000) * 60000; // Redondear al minuto
    
    if (!this.candleBuffer) {
      this.candleBuffer = new Map();
    }
    
    if (!this.candleBuffer.has(asset)) {
      this.candleBuffer.set(asset, {
        timestamp: currentMinute,
        open: price,
        high: price,
        low: price,
        close: price,
        prices: [price]
      });
      return;
    }
    
    const candle = this.candleBuffer.get(asset);
    
    // Si es el mismo minuto, actualizar la vela
    if (candle.timestamp === currentMinute) {
      candle.high = Math.max(candle.high, price);
      candle.low = Math.min(candle.low, price);
      candle.close = price;
      candle.prices.push(price);
    } else {
      // Nuevo minuto: emitir vela completa y crear nueva
      const completedCandle = {
        asset: asset,
        timestamp: candle.timestamp,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.prices.length,
        timeframe: 60
      };
      
      this.logger.info(`📊 VELA ARTIFICIAL: ${asset} ${completedCandle.close}`);
      this.emit('candle', completedCandle);
      
      // Crear nueva vela para el nuevo minuto
      this.candleBuffer.set(asset, {
        timestamp: currentMinute,
        open: price,
        high: price,
        low: price,
        close: price,
        prices: [price]
      });
    }
  }

  handleOTCAssetList(listData) {
    if (listData && listData.length > 0) {
      this.logger.info('📋 Lista de activos OTC recibida');
      
      // Buscar activos OTC disponibles
      listData.forEach(asset => {
        if (asset.name && asset.name.includes('OTC')) {
          this.logger.info(`🎯 Activo OTC disponible: ${asset.name} (ID: ${asset.id})`);
        }
      });
    }
  }

  async subscribeToCandles(asset, timeframe = 60) {
    const activeId = this.otcAssets[asset];
    
    if (!activeId) {
      this.logger.warn(`Activo OTC no encontrado: ${asset}`);
      return;
    }
    
    const subscribeMessage = {
      name: 'subscribeMessage',
      msg: {
        name: 'candle-generated',
        params: {
          routingFilters: {
            active_id: activeId,
            size: timeframe
          }
        }
      }
    };

    this.sendMessage(subscribeMessage);
    this.logger.info(`📈 Suscrito a velas OTC: ${asset} (${timeframe}s)`);
  }

  async subscribeToQuotes(asset) {
    const activeId = this.otcAssets[asset];
    
    if (!activeId) {
      this.logger.warn(`Activo OTC no encontrado: ${asset}`);
      return;
    }
    
    const subscribeMessage = {
      name: 'subscribeMessage',
      msg: {
        name: 'quote-generated',
        params: {
          routingFilters: {
            active_id: activeId
          }
        }
      }
    };

    this.sendMessage(subscribeMessage);
    this.logger.info(`💱 Suscrito a cotizaciones OTC: ${asset}`);
  }

  // Método REST para obtener datos históricos REALES
  async getCandlesREST(asset, timeframe, count = 100) {
    try {
      const activeId = this.otcAssets[asset];
      
      if (!activeId) {
        throw new Error(`Activo OTC no encontrado: ${asset}`);
      }

      const endTime = Math.floor(Date.now() / 1000);
      const startTime = endTime - (count * 60); // 60 segundos por vela

      this.logger.info(`📊 Solicitando ${count} velas históricas via REST para ${asset}...`);

      // Probar diferentes endpoints de IQ Option
      const endpoints = [
        'https://iqoption.com/api/getcandles',
        'https://iqoption.com/api/candles',
        'https://iqoption.com/api/v2/candles',
        'https://iqoption.com/api/candles/candles.json'
      ];

      let response = null;
      let lastError = null;

      for (const endpoint of endpoints) {
        try {
          this.logger.info(`🔍 Probando endpoint: ${endpoint}`);
          
          response = await this.session.get(endpoint, {
            params: {
              active_id: activeId,
              size: timeframe,
              from: startTime,
              to: endTime,
              count: count
            },
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
            timeout: 60000
          });

          if (response.status === 200 && response.data) {
            this.logger.info(`✅ Endpoint funcional encontrado: ${endpoint}`);
            break;
          }

        } catch (error) {
          lastError = error;
          this.logger.warn(`❌ Endpoint ${endpoint} falló: ${error.message}`);
          continue;
        }
      }

      if (!response || response.status !== 200) {
        throw new Error(`Todos los endpoints fallaron. Último error: ${lastError?.message}`);
      }

      if (response.data && response.data.candles) {
        const candles = response.data.candles.map(candle => ({
          asset: asset,
          timestamp: candle.from * 1000,
          open: parseFloat(candle.open),
          high: parseFloat(candle.max),
          low: parseFloat(candle.min),
          close: parseFloat(candle.close),
          volume: candle.volume || 0
        }));

        this.logger.info(`✅ Descarga REST exitosa: ${candles.length} velas históricas para ${asset}`);
        return candles;
      } else {
        throw new Error('Respuesta REST inválida - sin datos de velas');
      }

    } catch (error) {
      this.logger.error(`❌ Error en descarga REST para ${asset}:`, error.message);
      throw error;
    }
  }

  async getCandles(asset, timeframe, count = 100) {
    const activeId = this.otcAssets[asset];
    
    if (!activeId) {
      throw new Error(`Activo OTC no encontrado: ${asset}`);
    }
    
    const message = {
      name: 'sendMessage',
      msg: {
        name: 'get-candles',
        version: '1.0',
        body: {
          active_id: activeId,
          size: timeframe,
          to: Math.floor(Date.now() / 1000),
          count: count
        }
      },
      request_id: this.getRequestId()
    };

    return new Promise((resolve, reject) => {
      // Timeout muy generoso para descargas históricas
      const timeoutDuration = count > 5000 ? 300000 : count > 1000 ? 180000 : count > 100 ? 120000 : 60000;
      const timeout = setTimeout(() => {
        reject(new Error(`Timeout obteniendo ${count} velas OTC después de ${timeoutDuration/1000}s`));
      }, timeoutDuration);

      const messageHandler = (response) => {
        if (response.request_id === message.request_id) {
          clearTimeout(timeout);
          this.removeListener('message', messageHandler);
          
          // Log de la respuesta para debug
          this.logger.info(`📨 Respuesta get-candles para ${asset}:`, JSON.stringify(response, null, 2));
          
          if (response.msg && response.msg.candles) {
            const candles = response.msg.candles.map(candle => ({
              asset: asset,
              timestamp: candle.from * 1000,
              open: parseFloat(candle.open),
              high: parseFloat(candle.max),
              low: parseFloat(candle.min),
              close: parseFloat(candle.close),
              volume: candle.volume || 0
            }));
            
            this.logger.info(`📊 ${candles.length} velas históricas OTC para ${asset}`);
            resolve(candles);
          } else {
            reject(new Error('Respuesta inválida de velas OTC'));
          }
        }
      };

      this.on('message', messageHandler);
      this.sendMessage(message);
    });
  }

  // Método alternativo 1: get-history
  async getCandlesHistory(asset, timeframe, count = 100) {
    const activeId = this.otcAssets[asset];
    
    if (!activeId) {
      throw new Error(`Activo OTC no encontrado: ${asset}`);
    }
    
    const message = {
      name: 'sendMessage',
      msg: {
        name: 'get-history',
        version: '1.0',
        body: {
          active_id: activeId,
          size: timeframe,
          to: Math.floor(Date.now() / 1000),
          count: count
        }
      },
      request_id: this.getRequestId()
    };

    return new Promise((resolve, reject) => {
      const timeoutDuration = 120000; // 2 minutos
      const timeout = setTimeout(() => {
        reject(new Error(`Timeout get-history ${count} velas después de ${timeoutDuration/1000}s`));
      }, timeoutDuration);

      const messageHandler = (response) => {
        if (response.request_id === message.request_id) {
          clearTimeout(timeout);
          this.removeListener('message', messageHandler);
          
          this.logger.info(`📨 Respuesta get-history para ${asset}:`, JSON.stringify(response, null, 2));
          
          if (response.msg && response.msg.history) {
            const candles = response.msg.history.map(candle => ({
              asset: asset,
              timestamp: candle.from * 1000,
              open: parseFloat(candle.open),
              high: parseFloat(candle.max),
              low: parseFloat(candle.min),
              close: parseFloat(candle.close),
              volume: candle.volume || 0
            }));
            
            resolve(candles);
          } else {
            reject(new Error('Respuesta get-history inválida'));
          }
        }
      };

      this.on('message', messageHandler);
      this.sendMessage(message);
    });
  }

  // Método alternativo 2: candles-history
  async getCandlesHistoryAlt(asset, timeframe, count = 100) {
    const activeId = this.otcAssets[asset];
    
    if (!activeId) {
      throw new Error(`Activo OTC no encontrado: ${asset}`);
    }
    
    const message = {
      name: 'sendMessage',
      msg: {
        name: 'candles-history',
        version: '1.0',
        body: {
          active_id: activeId,
          timeframe: timeframe,
          to: Math.floor(Date.now() / 1000),
          count: count
        }
      },
      request_id: this.getRequestId()
    };

    return new Promise((resolve, reject) => {
      const timeoutDuration = 120000;
      const timeout = setTimeout(() => {
        reject(new Error(`Timeout candles-history ${count} velas después de ${timeoutDuration/1000}s`));
      }, timeoutDuration);

      const messageHandler = (response) => {
        if (response.request_id === message.request_id) {
          clearTimeout(timeout);
          this.removeListener('message', messageHandler);
          
          this.logger.info(`📨 Respuesta candles-history para ${asset}:`, JSON.stringify(response, null, 2));
          
          if (response.msg && (response.msg.candles || response.msg.data)) {
            const candleData = response.msg.candles || response.msg.data;
            const candles = candleData.map(candle => ({
              asset: asset,
              timestamp: candle.from * 1000,
              open: parseFloat(candle.open),
              high: parseFloat(candle.max),
              low: parseFloat(candle.min),
              close: parseFloat(candle.close),
              volume: candle.volume || 0
            }));
            
            resolve(candles);
          } else {
            reject(new Error('Respuesta candles-history inválida'));
          }
        }
      };

      this.on('message', messageHandler);
      this.sendMessage(message);
    });
  }

  // Método para cargar datos históricos por lotes
  async getCandlesBatch(asset, timeframe, totalCount = 525600) {
    const batchSize = 1000; // Reducir a 1000 velas por lote para mayor confiabilidad
    const batches = Math.ceil(totalCount / batchSize);
    let allCandles = [];
    
    this.logger.info(`📊 Cargando ${totalCount} velas en ${batches} lotes de ${batchSize} velas cada uno...`);
    
    for (let i = 0; i < batches; i++) {
      const currentBatchSize = Math.min(batchSize, totalCount - (i * batchSize));
      const fromTime = Math.floor(Date.now() / 1000) - ((i + 1) * batchSize * 60); // 60 segundos por vela
      
      try {
        this.logger.info(`📦 Cargando lote ${i + 1}/${batches} (${currentBatchSize} velas)...`);
        
        const batchCandles = await this.getCandlesREST(asset, timeframe, currentBatchSize);
        
        if (batchCandles && batchCandles.length > 0) {
          allCandles = [...batchCandles, ...allCandles]; // Más recientes al final
          this.logger.info(`✅ Lote ${i + 1} completado: ${batchCandles.length} velas`);
        }
        
        // Pausa entre lotes para no sobrecargar la API
        if (i < batches - 1) {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
      } catch (error) {
        this.logger.error(`❌ Error en lote ${i + 1}:`, error.message);
        // Continuar con el siguiente lote
      }
    }
    
    this.logger.info(`🎯 Carga completa: ${allCandles.length} velas de ${totalCount} solicitadas`);
    return allCandles;
  }

  getOTCAssetName(activeId) {
    const idToAsset = {};
    
    // Invertir el mapeo
    Object.keys(this.otcAssets).forEach(asset => {
      idToAsset[this.otcAssets[asset]] = asset;
    });

    return idToAsset[activeId] || 'UNKNOWN';
  }

  sendMessage(message) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.logger.warn('No se puede enviar mensaje - WebSocket OTC no conectado');
    }
  }

  getRequestId() {
    return this.requestId++;
  }

  async disconnect() {
    try {
      this.logger.info('Desconectando de OTC IQ Option...');
      
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      
      this.isConnected = false;
      this.subscriptions.clear();
      
      this.logger.info('Desconectado de OTC IQ Option');
      
    } catch (error) {
      this.logger.error('Error al desconectar OTC:', error.message);
    }
  }

  isConnectionActive() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  // NUEVO: Ejecutar operación de trading (MODO DEMO SIMPLIFICADO)
  async buyOption(asset, amount, direction, duration = 60) {
    try {
      this.logger.info(`🤖 EJECUTANDO OPERACIÓN DEMO: ${asset} ${direction} $${amount} (${duration}s)`);
      
      // Verificar conexión - CRÍTICO para operaciones reales
      if (!this.isConnectionActive()) {
        this.logger.error('❌ Sin conexión activa con IQ Option - Intentando reconectar...');
        throw new Error('No hay conexión activa con IQ Option');
      }

      // Obtener ID del asset
      const assetId = this.otcAssets[asset];
      if (!assetId) {
        throw new Error(`Asset ${asset} no encontrado`);
      }

      // Convertir dirección
      const optionType = direction === 'CALL' ? 'call' : 'put';

      // ENVIAR OPERACIÓN REAL A IQ OPTION
      const message = {
        name: 'sendMessage',
        msg: {
          name: 'binary-options.open-option',
          version: '1.0',
          body: {
            user_balance_id: 1, // Balance demo de IQ Option
            active_id: assetId,
            option_type_id: 3, // Turbo options (1 minuto)
            direction: optionType,
            expired: Math.floor(Date.now() / 1000) + duration,
            price: amount,
            value: amount,
            profit_income: 0.85, // 85% payout típico
            time_rate: duration
          }
        },
        request_id: this.getRequestId()
      };

      this.logger.info(`🚀 ENVIANDO OPERACIÓN REAL A IQ OPTION: ${asset} ${direction} $${amount}`);
      this.logger.info(`📊 Request ID: ${message.request_id}`);
      this.logger.info(`📋 DIAGNÓSTICO - Mensaje completo: ${JSON.stringify(message, null, 2)}`);
      this.logger.info(`🎯 DIAGNÓSTICO - Asset ID: ${assetId}, Option Type: ${optionType}`);
      this.logger.info(`🔗 DIAGNÓSTICO - Estado WebSocket: ${this.ws ? this.ws.readyState : 'NO_WS'}`);
      this.logger.info(`📡 DIAGNÓSTICO - isConnected: ${this.isConnected}`);
      
      // Enviar mensaje a IQ Option y ESPERAR RESPUESTA
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          this.logger.error(`❌ TIMEOUT: IQ Option no respondió en 30 segundos para ${asset}`);
          reject(new Error('Timeout - IQ Option no respondió'));
        }, 30000);

        const messageHandler = (data) => {
          try {
            // DIAGNÓSTICO: Capturar TODAS las respuestas relacionadas con operaciones
            if (data.name && (
              data.name.includes('binary') || 
              data.name.includes('option') || 
              data.name.includes('trade') ||
              data.name.includes('open') ||
              data.name.includes('result') ||
              data.request_id === message.request_id
            )) {
              this.logger.info(`🔍 DIAGNÓSTICO - Respuesta relacionada: ${JSON.stringify(data, null, 2)}`);
            }
            
            if (data.request_id === message.request_id) {
              clearTimeout(timeout);
              this.removeListener('message', messageHandler);
              
              if (data.name === 'binary-options.open-option') {
                if (data.msg && data.msg.isSuccessful) {
                  const operationId = data.msg.id || `IQ_${asset}_${message.request_id}`;
                  this.logger.info(`✅ OPERACIÓN CONFIRMADA POR IQ OPTION: ID ${operationId}`);
                  
                  resolve({
                    success: true,
                    id: operationId,
                    message: 'Operación confirmada por IQ Option',
                    asset: asset,
                    direction: direction,
                    amount: amount,
                    duration: duration,
                    iqResponse: data.msg
                  });
                } else {
                  this.logger.error(`❌ IQ OPTION RECHAZÓ LA OPERACIÓN: ${JSON.stringify(data.msg)}`);
                  reject(new Error(`IQ Option rechazó la operación: ${data.msg?.message || 'Error desconocido'}`));
                }
              }
            }
          } catch (error) {
            clearTimeout(timeout);
            this.removeListener('message', messageHandler);
            reject(error);
          }
        };

        this.on('message', messageHandler);
        
        // Enviar mensaje a IQ Option
        this.sendMessage(message);
        this.logger.info(`📤 MENSAJE ENVIADO A IQ OPTION - Esperando respuesta...`);
      });

    } catch (error) {
      this.logger.error(`❌ Error en buyOption:`, error);
      throw error;
    }
  }

  // NUEVO: Obtener resultado de operación
  async getOperationResult(operationId) {
    try {
      // Por ahora retornar un resultado simulado para demo
      // En producción, aquí se consultaría el resultado real
      return {
        win: Math.random() > 0.5, // 50% probabilidad de ganar (demo)
        profit: Math.random() > 0.5 ? 0.85 : -1, // 85% ganancia o pérdida total
        id: operationId
      };
    } catch (error) {
      this.logger.error(`❌ Error obteniendo resultado de operación ${operationId}:`, error);
      return null;
    }
  }
}

module.exports = IQOptionOTC;
