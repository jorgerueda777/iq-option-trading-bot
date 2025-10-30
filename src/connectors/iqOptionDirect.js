const WebSocket = require('ws');
const axios = require('axios');
const EventEmitter = require('events');
const config = require('../../config/config');
const Logger = require('../utils/logger');

class IQOptionDirect extends EventEmitter {
  constructor() {
    super();
    this.logger = new Logger('IQOptionDirect');
    this.ws = null;
    this.isConnected = false;
    this.ssid = null;
    this.requestId = 1;
    this.subscriptions = new Map();
    this.cookies = '';
    this.baseUrl = 'https://iqoption.com';
    this.apiUrl = 'https://auth.iqoption.com/api/v2/login';
  }

  async connect() {
    try {
      this.logger.info('🚀 CONECTANDO DIRECTAMENTE A IQ OPTION...');
      
      // Método directo de autenticación
      await this.directLogin();
      
      // Conectar WebSocket directo
      await this.connectDirectWebSocket();
      
      this.logger.info('✅ CONECTADO EXITOSAMENTE A IQ OPTION REAL');
      
    } catch (error) {
      this.logger.error('❌ Error conectando a IQ Option:', error.message);
      throw error;
    }
  }

  async directLogin() {
    try {
      this.logger.info('🔐 Autenticación directa a IQ Option...');
      
      // Datos de login exactos para IQ Option
      const loginPayload = {
        identifier: config.iqOption.email,
        password: config.iqOption.password,
        remember: false,
        affiliate_promocode: "",
        client_platform_id: 9
      };

      this.logger.info(`📧 Intentando login con: ${config.iqOption.email}`);

      // Request directo a la API de autenticación
      const response = await axios({
        method: 'POST',
        url: this.apiUrl,
        data: loginPayload,
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'application/json',
          'Accept-Language': 'en-US,en;q=0.9',
          'Origin': 'https://iqoption.com',
          'Referer': 'https://iqoption.com/',
          'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
          'Sec-Ch-Ua-Mobile': '?0',
          'Sec-Ch-Ua-Platform': '"Windows"',
          'Sec-Fetch-Dest': 'empty',
          'Sec-Fetch-Mode': 'cors',
          'Sec-Fetch-Site': 'same-site'
        },
        timeout: 20000,
        validateStatus: function (status) {
          return status >= 200 && status < 500;
        }
      });

      this.logger.info(`📡 Respuesta de IQ Option - Status: ${response.status}`);

      if (response.status === 200 && response.data) {
        this.logger.info('📄 Datos de respuesta:', JSON.stringify(response.data, null, 2));

        // Verificar diferentes formatos de respuesta exitosa
        if (response.data.data && response.data.data.ssid) {
          this.ssid = response.data.data.ssid;
          this.logger.info('✅ SSID obtenido exitosamente');
        } else if (response.data.ssid) {
          this.ssid = response.data.ssid;
          this.logger.info('✅ SSID obtenido exitosamente');
        } else if (response.data.token) {
          this.ssid = response.data.token;
          this.logger.info('✅ Token obtenido exitosamente');
        } else if (response.data.result && response.data.result.ssid) {
          this.ssid = response.data.result.ssid;
          this.logger.info('✅ SSID del resultado obtenido');
        } else {
          // Buscar cualquier campo que parezca un token/ssid
          const responseStr = JSON.stringify(response.data);
          const possibleTokens = responseStr.match(/"([a-f0-9]{32,}|[A-Za-z0-9+/]{40,}={0,2})"/g);
          
          if (possibleTokens && possibleTokens.length > 0) {
            this.ssid = possibleTokens[0].replace(/"/g, '');
            this.logger.info('✅ Token extraído de la respuesta');
          } else {
            throw new Error(`Login exitoso pero no se encontró SSID/Token. Respuesta: ${JSON.stringify(response.data)}`);
          }
        }

        // Guardar cookies si las hay
        if (response.headers['set-cookie']) {
          this.cookies = response.headers['set-cookie'].join('; ');
        }

      } else if (response.status === 400 || response.status === 401) {
        this.logger.error('❌ Credenciales incorrectas:', response.data);
        throw new Error(`Credenciales incorrectas: ${response.data.message || 'Email o contraseña inválidos'}`);
      } else {
        throw new Error(`Error de autenticación HTTP ${response.status}: ${response.statusText}`);
      }

    } catch (error) {
      if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
        throw new Error('No se puede conectar a IQ Option. Verifica tu conexión a internet.');
      } else if (error.response) {
        this.logger.error('📄 Error response:', error.response.data);
        throw new Error(`Error de IQ Option: ${error.response.data.message || error.message}`);
      } else {
        throw new Error(`Error de conexión: ${error.message}`);
      }
    }
  }

  async connectDirectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        this.logger.info('🔌 Conectando WebSocket directo a IQ Option...');
        
        // WebSocket directo de IQ Option
        const wsUrl = 'wss://iqoption.com/echo/websocket';
        
        this.ws = new WebSocket(wsUrl, {
          headers: {
            'Origin': 'https://iqoption.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': this.cookies
          }
        });

        let isResolved = false;

        this.ws.on('open', () => {
          this.logger.info('✅ WebSocket CONECTADO a IQ Option');
          this.isConnected = true;
          
          // Enviar autenticación inmediatamente
          this.sendAuth();
          
          // Configurar heartbeat
          this.setupHeartbeat();
          
          if (!isResolved) {
            isResolved = true;
            resolve();
          }
        });

        this.ws.on('message', (data) => {
          this.handleMessage(data);
        });

        this.ws.on('close', (code, reason) => {
          this.logger.warn(`❌ WebSocket cerrado - Código: ${code}, Razón: ${reason}`);
          this.isConnected = false;
        });

        this.ws.on('error', (error) => {
          this.logger.error('❌ Error WebSocket:', error.message);
          if (!isResolved) {
            isResolved = true;
            reject(error);
          }
        });

        // Timeout de 20 segundos
        setTimeout(() => {
          if (!isResolved) {
            isResolved = true;
            reject(new Error('Timeout conectando WebSocket a IQ Option'));
          }
        }, 20000);

      } catch (error) {
        reject(error);
      }
    });
  }

  sendAuth() {
    if (this.ssid) {
      // Mensaje de autenticación para IQ Option
      const authMessage = {
        name: 'ssid',
        msg: this.ssid
      };
      
      this.sendMessage(authMessage);
      this.logger.info('🔑 Autenticación enviada a IQ Option');

      // También enviar mensaje de suscripción a perfil
      setTimeout(() => {
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
      }, 1000);
    }
  }

  setupHeartbeat() {
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

  handleMessage(data) {
    try {
      const message = JSON.parse(data.toString());
      
      // Log mensajes importantes
      if (message.name !== 'heartbeat' && message.name !== 'timeSync') {
        this.logger.info(`📨 IQ Option: ${message.name}`);
      }
      
      // Procesar mensajes específicos
      switch (message.name) {
        case 'profile':
          this.logger.info('✅ PERFIL RECIBIDO - Autenticado en IQ Option');
          this.logger.info(`👤 Usuario: ${message.msg.email || 'N/A'}`);
          break;
          
        case 'candle-generated':
          this.handleCandleData(message.msg);
          break;
          
        case 'quote-generated':
          this.handleQuoteData(message.msg);
          break;
          
        case 'candles':
          this.handleHistoricalCandles(message);
          break;
          
        case 'listInfoData':
          this.logger.info('📋 Lista de activos recibida');
          break;
          
        default:
          // Otros mensajes
          break;
      }
      
      this.emit('message', message);
      
    } catch (error) {
      this.logger.error('Error procesando mensaje de IQ Option:', error.message);
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
      
      this.logger.info(`📊 VELA REAL IQ: ${processedCandle.asset} ${processedCandle.close}`);
      this.emit('candle', processedCandle);
      
    } catch (error) {
      this.logger.error('Error procesando vela de IQ Option:', error.message);
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
      this.logger.error('Error procesando cotización de IQ Option:', error.message);
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
      
      this.logger.info(`📈 SUSCRITO A IQ OPTION: ${asset} (${timeframe}s)`);
      
    } catch (error) {
      this.logger.error(`Error suscribiéndose a ${asset} en IQ Option:`, error.message);
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
      this.logger.info(`💱 SUSCRITO A COTIZACIONES IQ: ${asset}`);
      
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
          reject(new Error('Timeout obteniendo velas de IQ Option'));
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
              
              this.logger.info(`📊 ${candles.length} velas históricas de IQ OPTION para ${asset}`);
              resolve(candles);
            } else {
              reject(new Error('Respuesta inválida de velas históricas de IQ Option'));
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
    // IDs exactos de IQ Option para activos OTC
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
      this.logger.warn('No se puede enviar mensaje - WebSocket no conectado a IQ Option');
    }
  }

  getRequestId() {
    return this.requestId++;
  }

  async disconnect() {
    try {
      this.logger.info('Desconectando de IQ Option...');
      
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      
      this.isConnected = false;
      this.subscriptions.clear();
      
      this.logger.info('Desconectado de IQ Option');
      
    } catch (error) {
      this.logger.error('Error al desconectar de IQ Option:', error.message);
    }
  }

  isConnectionActive() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

module.exports = IQOptionDirect;
