const WebSocket = require('ws');
const axios = require('axios');
const EventEmitter = require('events');
const tough = require('tough-cookie');
const config = require('../../config/config');
const Logger = require('../utils/logger');

class IQOptionAPI extends EventEmitter {
  constructor() {
    super();
    this.logger = new Logger('IQOptionAPI');
    this.ws = null;
    this.isConnected = false;
    this.ssid = null;
    this.requestId = 1;
    this.subscriptions = new Map();
    this.cookieJar = new tough.CookieJar();
    this.baseUrl = 'https://iqoption.com';
  }

  async connect() {
    try {
      this.logger.info('🚀 Conectando a IQ Option API REAL...');
      
      // Paso 1: Obtener página principal para cookies
      await this.getInitialCookies();
      
      // Paso 2: Autenticarse con credenciales reales
      await this.login();
      
      // Paso 3: Conectar WebSocket
      await this.connectWebSocket();
      
      this.logger.info('✅ Conectado exitosamente a IQ Option API REAL');
      
    } catch (error) {
      this.logger.error('❌ Error conectando a IQ Option API:', error.message);
      throw error;
    }
  }

  async getInitialCookies() {
    try {
      this.logger.info('🍪 Obteniendo cookies iniciales...');
      
      const response = await axios.get(this.baseUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.9',
          'Accept-Encoding': 'gzip, deflate, br',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'none'
        },
        timeout: 15000
      });

      // Extraer cookies de la respuesta
      if (response.headers['set-cookie']) {
        response.headers['set-cookie'].forEach(cookie => {
          this.cookieJar.setCookieSync(cookie, this.baseUrl);
        });
        this.logger.info('✅ Cookies iniciales obtenidas');
      }
      
    } catch (error) {
      this.logger.error('Error obteniendo cookies:', error.message);
      throw error;
    }
  }

  async login() {
    try {
      this.logger.info('🔐 Iniciando sesión con credenciales reales...');
      
      if (!config.iqOption.email || !config.iqOption.password) {
        throw new Error('Credenciales no configuradas en .env');
      }

      // Preparar datos de login
      const loginData = {
        email: config.iqOption.email,
        password: config.iqOption.password,
        platform: 'web'
      };

      // Obtener cookies como string
      const cookies = this.cookieJar.getCookieStringSync(this.baseUrl);

      // Realizar login
      const response = await axios({
        method: 'POST',
        url: `${this.baseUrl}/api/login`,
        data: loginData,
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Accept': 'application/json, text/plain, */*',
          'Accept-Language': 'en-US,en;q=0.9',
          'Origin': this.baseUrl,
          'Referer': `${this.baseUrl}/traderoom/`,
          'Cookie': cookies,
          'X-Requested-With': 'XMLHttpRequest'
        },
        timeout: 15000,
        validateStatus: function (status) {
          return status >= 200 && status < 500;
        }
      });

      this.logger.info(`📡 Respuesta login - Status: ${response.status}`);

      // Procesar respuesta
      if (response.status === 200 && response.data) {
        // Verificar diferentes formatos de respuesta
        if (response.data.isSuccessful === true) {
          this.ssid = response.data.ssid;
          this.logger.info('✅ Login exitoso - SSID obtenido');
        } else if (response.data.result === true) {
          this.ssid = response.data.ssid || response.data.session_id;
          this.logger.info('✅ Login exitoso - Sesión iniciada');
        } else if (response.data.success === true) {
          this.ssid = response.data.token || response.data.session_token;
          this.logger.info('✅ Login exitoso - Token obtenido');
        } else {
          // Intentar extraer cualquier token/ssid de la respuesta
          const responseStr = JSON.stringify(response.data);
          const ssidMatch = responseStr.match(/"(?:ssid|session_id|token|session_token)":"([^"]+)"/);
          
          if (ssidMatch) {
            this.ssid = ssidMatch[1];
            this.logger.info('✅ Login exitoso - ID de sesión extraído');
          } else {
            this.logger.error('❌ Respuesta de login:', response.data);
            throw new Error('Login falló: No se pudo obtener ID de sesión');
          }
        }

        // Actualizar cookies con la respuesta
        if (response.headers['set-cookie']) {
          response.headers['set-cookie'].forEach(cookie => {
            this.cookieJar.setCookieSync(cookie, this.baseUrl);
          });
        }

      } else {
        throw new Error(`Login falló - HTTP ${response.status}: ${response.statusText}`);
      }

    } catch (error) {
      this.logger.error('❌ Error en login:', error.message);
      
      if (error.response && error.response.data) {
        this.logger.error('📄 Datos de respuesta:', error.response.data);
      }
      
      throw new Error(`Login falló: ${error.message}`);
    }
  }

  async connectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        this.logger.info('🔌 Conectando WebSocket...');
        
        const wsUrl = 'wss://iqoption.com/echo/websocket';
        const cookies = this.cookieJar.getCookieStringSync(this.baseUrl);
        
        this.ws = new WebSocket(wsUrl, {
          headers: {
            'Origin': 'https://iqoption.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': cookies
          }
        });

        this.ws.on('open', () => {
          this.logger.info('✅ WebSocket conectado');
          this.isConnected = true;
          
          // Enviar autenticación si tenemos SSID
          if (this.ssid) {
            this.authenticate();
          }
          
          // Configurar heartbeat
          this.setupHeartbeat();
          
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
          this.logger.error('Error WebSocket:', error.message);
          reject(error);
        });

        // Timeout
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

  authenticate() {
    if (this.ssid) {
      const authMessage = {
        name: 'ssid',
        msg: this.ssid
      };
      
      this.sendMessage(authMessage);
      this.logger.info('🔑 Autenticación enviada por WebSocket');
    }
  }

  setupHeartbeat() {
    setInterval(() => {
      if (this.isConnected) {
        this.sendHeartbeat();
      }
    }, 30000); // Cada 30 segundos
  }

  sendHeartbeat() {
    const heartbeat = {
      name: 'heartbeat',
      msg: Date.now()
    };
    this.sendMessage(heartbeat);
  }

  handleMessage(data) {
    try {
      const message = JSON.parse(data.toString());
      
      // Log solo mensajes importantes
      if (message.name !== 'heartbeat' && message.name !== 'timeSync') {
        this.logger.debug(`📨 Mensaje: ${message.name}`);
      }
      
      // Procesar mensajes
      switch (message.name) {
        case 'candle-generated':
          this.handleCandleData(message.msg);
          break;
        case 'quote-generated':
          this.handleQuoteData(message.msg);
          break;
        case 'candles':
          this.handleHistoricalCandles(message);
          break;
        case 'profile':
          this.logger.info('✅ Perfil recibido - Autenticación confirmada');
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
      if (!candleData || typeof candleData.active_id === 'undefined') return;
      
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
      
      this.logger.info(`📊 Vela REAL: ${processedCandle.asset} ${processedCandle.close}`);
      this.emit('candle', processedCandle);
      
    } catch (error) {
      this.logger.error('Error procesando vela:', error.message);
    }
  }

  handleQuoteData(quoteData) {
    try {
      if (!quoteData || typeof quoteData.active_id === 'undefined') return;
      
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
      
      this.logger.info(`📈 Suscrito a velas: ${asset} (${timeframe}s)`);
      
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
      this.logger.info(`💱 Suscrito a cotizaciones: ${asset}`);
      
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
              
              this.logger.info(`📊 ${candles.length} velas históricas obtenidas para ${asset}`);
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

  getRequestId() {
    return this.requestId++;
  }

  async disconnect() {
    try {
      this.logger.info('Desconectando de IQ Option API...');
      
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      
      this.isConnected = false;
      this.subscriptions.clear();
      
      this.logger.info('Desconectado de IQ Option API');
      
    } catch (error) {
      this.logger.error('Error al desconectar:', error.message);
    }
  }

  isConnectionActive() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

module.exports = IQOptionAPI;
