const WebSocket = require('ws');
const axios = require('axios');
const EventEmitter = require('events');
const config = require('../../config/config');
const Logger = require('../utils/logger');

class IQOptionRealConnector extends EventEmitter {
  constructor() {
    super();
    this.logger = new Logger('IQRealConnector');
    this.ws = null;
    this.isConnected = false;
    this.sessionId = null;
    this.ssid = null;
    this.requestId = 1;
    this.subscriptions = new Map();
    this.cookies = '';
    this.baseUrl = 'https://iqoption.com';
  }

  async connect() {
    try {
      this.logger.info('Conectando a IQ Option con datos REALES...');
      
      // Paso 1: Obtener cookies de sesión
      await this.getSessionCookies();
      
      // Paso 2: Autenticarse
      await this.authenticate();
      
      // Paso 3: Conectar WebSocket
      await this.connectWebSocket();
      
      this.logger.info('Conectado exitosamente a IQ Option REAL');
      
    } catch (error) {
      this.logger.error('Error al conectar a IQ Option REAL:', error.message);
      throw error;
    }
  }

  async getSessionCookies() {
    try {
      this.logger.info('Obteniendo cookies de sesión...');
      
      const response = await axios.get(`${this.baseUrl}/`, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Accept-Encoding': 'gzip, deflate, br',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1'
        },
        timeout: 15000
      });

      if (response.headers['set-cookie']) {
        this.cookies = response.headers['set-cookie'].join('; ');
        this.logger.info('Cookies de sesión obtenidas');
      }
      
    } catch (error) {
      this.logger.error('Error obteniendo cookies:', error.message);
      throw error;
    }
  }

  async authenticate() {
    try {
      this.logger.info('Autenticando con credenciales reales...');
      
      const loginData = {
        email: config.iqOption.email,
        password: config.iqOption.password,
        platform: 'web'
      };

      // Probar múltiples endpoints
      let response;
      let success = false;
      const endpoints = [
        `${this.baseUrl}/api/login`,
        `${this.baseUrl}/api/v2/login`, 
        `${this.baseUrl}/login`,
        `${this.baseUrl}/auth/login`
      ];

      for (const endpoint of endpoints) {
        try {
          this.logger.info(`Probando endpoint: ${endpoint}`);
          response = await axios.post(endpoint, loginData, {
            headers: {
              'Content-Type': 'application/json',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
              'Accept': 'application/json, text/plain, */*',
              'Accept-Language': 'en-US,en;q=0.9',
              'Origin': this.baseUrl,
              'Referer': `${this.baseUrl}/`,
              'Cookie': this.cookies
            },
            timeout: 15000,
            validateStatus: function (status) {
              return status < 500;
            }
          });

          this.logger.info(`Respuesta de ${endpoint} - Status: ${response.status}`);
          
          if (response.status === 200 && response.data) {
            if (response.data.isSuccessful) {
              this.ssid = response.data.ssid;
              this.logger.info('✅ Autenticación EXITOSA con datos reales');
              
              // Actualizar cookies con la respuesta
              if (response.headers['set-cookie']) {
                this.cookies += '; ' + response.headers['set-cookie'].join('; ');
              }
              
              success = true;
              break;
            }
          }
          
        } catch (endpointError) {
          this.logger.warn(`Endpoint ${endpoint} falló: ${endpointError.message}`);
          continue;
        }
      }

      if (!success) {
        throw new Error('Todos los endpoints de autenticación fallaron. Verifica tus credenciales.');
      }

    } catch (error) {
      this.logger.error('❌ Error en autenticación REAL:', error.message);
      throw new Error(`Autenticación falló: ${error.message}`);
    }
  }

  async connectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        this.logger.info('Conectando WebSocket REAL...');
        
        const wsUrl = `wss://iqoption.com/echo/websocket`;
        
        this.ws = new WebSocket(wsUrl, {
          headers: {
            'Origin': 'https://iqoption.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': this.cookies
          }
        });

        this.ws.on('open', () => {
          this.logger.info('✅ WebSocket REAL conectado');
          this.isConnected = true;
          
          // Enviar autenticación por WebSocket
          this.sendAuth();
          
          resolve();
        });

        this.ws.on('message', (data) => {
          this.handleMessage(data);
        });

        this.ws.on('close', (code, reason) => {
          this.logger.warn(`WebSocket cerrado - Código: ${code}, Razón: ${reason}`);
          this.isConnected = false;
        });

        this.ws.on('error', (error) => {
          this.logger.error('Error en WebSocket REAL:', error.message);
          reject(error);
        });

        // Timeout de conexión
        setTimeout(() => {
          if (!this.isConnected) {
            reject(new Error('Timeout conectando WebSocket'));
          }
        }, 15000);

      } catch (error) {
        reject(error);
      }
    });
  }

  sendAuth() {
    if (this.ssid) {
      const authMessage = {
        name: 'ssid',
        msg: this.ssid
      };
      
      this.sendMessage(authMessage);
      this.logger.info('Mensaje de autenticación enviado por WebSocket');
    }
  }

  handleMessage(data) {
    try {
      const message = JSON.parse(data.toString());
      
      // Log de mensajes para debug
      if (message.name !== 'heartbeat') {
        this.logger.debug(`Mensaje recibido: ${message.name}`);
      }
      
      // Manejar diferentes tipos de mensajes
      switch (message.name) {
        case 'candle-generated':
          this.handleCandleData(message.msg);
          break;
        case 'quote-generated':
          this.handleQuoteData(message.msg);
          break;
        case 'candles':
          this.handleHistoricalCandles(message.msg);
          break;
        case 'heartbeat':
          this.sendHeartbeat();
          break;
        default:
          // Otros mensajes
          break;
      }
      
      this.emit('message', message);
      
    } catch (error) {
      this.logger.error('Error procesando mensaje:', error.message);
    }
  }

  handleCandleData(candleData) {
    try {
      if (!candleData || !candleData.active_id) return;
      
      const processedCandle = {
        asset: this.getAssetName(candleData.active_id),
        timestamp: candleData.from * 1000,
        open: parseFloat(candleData.open),
        high: parseFloat(candleData.max),
        low: parseFloat(candleData.min),
        close: parseFloat(candleData.close),
        volume: candleData.volume || 0,
        timeframe: candleData.size || 60
      };
      
      this.logger.info(`📊 Nueva vela REAL: ${processedCandle.asset} - ${processedCandle.close}`);
      this.emit('candle', processedCandle);
      
    } catch (error) {
      this.logger.error('Error procesando vela:', error.message);
    }
  }

  handleQuoteData(quoteData) {
    try {
      if (!quoteData || !quoteData.active_id) return;
      
      const processedQuote = {
        asset: this.getAssetName(quoteData.active_id),
        timestamp: Date.now(),
        bid: parseFloat(quoteData.value),
        ask: parseFloat(quoteData.value),
        spread: 0
      };
      
      this.emit('quote', processedQuote);
      
    } catch (error) {
      this.logger.error('Error procesando cotización:', error.message);
    }
  }

  async subscribeToCandles(asset, timeframe = 60) {
    try {
      const activeId = this.getAssetId(asset);
      
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
      
      const subscriptionKey = `${asset}_${timeframe}`;
      this.subscriptions.set(subscriptionKey, { asset, timeframe, activeId });
      
      this.logger.info(`📈 Suscrito a velas REALES: ${asset} (${timeframe}s)`);
      
    } catch (error) {
      this.logger.error(`Error suscribiéndose a ${asset}:`, error.message);
    }
  }

  async subscribeToQuotes(asset) {
    try {
      const activeId = this.getAssetId(asset);
      
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
      this.logger.info(`💱 Suscrito a cotizaciones REALES: ${asset}`);
      
    } catch (error) {
      this.logger.error(`Error suscribiéndose a cotizaciones de ${asset}:`, error.message);
    }
  }

  async getCandles(asset, timeframe, count = 100) {
    try {
      const activeId = this.getAssetId(asset);
      
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
        const timeout = setTimeout(() => {
          reject(new Error('Timeout obteniendo velas históricas'));
        }, 15000);

        const messageHandler = (response) => {
          if (response.request_id === message.request_id) {
            clearTimeout(timeout);
            this.removeListener('message', messageHandler);
            
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
              
              this.logger.info(`📊 Obtenidas ${candles.length} velas históricas REALES para ${asset}`);
              resolve(candles);
            } else {
              reject(new Error('Respuesta inválida de velas históricas'));
            }
          }
        };

        this.on('message', messageHandler);
        this.sendMessage(message);
      });

    } catch (error) {
      this.logger.error(`Error obteniendo velas históricas de ${asset}:`, error.message);
      throw error;
    }
  }

  getAssetId(asset) {
    // IDs reales de IQ Option para activos OTC
    const assetMap = {
      'EURUSD-OTC': 1,
      'GBPUSD-OTC': 2, 
      'USDJPY-OTC': 3,
      'AUDUSD-OTC': 4,
      'USDCAD-OTC': 5,
      'EURJPY-OTC': 6,
      'GBPJPY-OTC': 7,
      'EURGBP-OTC': 8,
      'AUDJPY-OTC': 9,
      'NZDUSD-OTC': 10
    };

    return assetMap[asset] || 1;
  }

  getAssetName(activeId) {
    const idToAsset = {
      1: 'EURUSD-OTC',
      2: 'GBPUSD-OTC',
      3: 'USDJPY-OTC', 
      4: 'AUDUSD-OTC',
      5: 'USDCAD-OTC',
      6: 'EURJPY-OTC',
      7: 'GBPJPY-OTC',
      8: 'EURGBP-OTC',
      9: 'AUDJPY-OTC',
      10: 'NZDUSD-OTC'
    };

    return idToAsset[activeId] || 'UNKNOWN';
  }

  sendMessage(message) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.logger.warn('No se puede enviar mensaje - WebSocket no conectado');
    }
  }

  sendHeartbeat() {
    const heartbeat = {
      name: 'heartbeat',
      msg: Date.now()
    };
    this.sendMessage(heartbeat);
  }

  getRequestId() {
    return this.requestId++;
  }

  async disconnect() {
    try {
      this.logger.info('Desconectando de IQ Option REAL...');
      
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      
      this.isConnected = false;
      this.subscriptions.clear();
      
      this.logger.info('Desconectado de IQ Option REAL');
      
    } catch (error) {
      this.logger.error('Error al desconectar:', error.message);
    }
  }

  isConnectionActive() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

module.exports = IQOptionRealConnector;
