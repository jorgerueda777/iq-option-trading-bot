const WebSocket = require('ws');
const axios = require('axios');
const EventEmitter = require('events');
const config = require('../../config/config');
const Logger = require('../utils/logger');

class IQOptionOfficial extends EventEmitter {
  constructor() {
    super();
    this.logger = new Logger('IQOptionOfficial');
    this.ws = null;
    this.isConnected = false;
    this.ssid = null;
    this.requestId = 1;
    this.subscriptions = new Map();
    this.session = axios.create();
    
    // URLs oficiales de IQ Option según la configuración
    this.authUrl = 'https://auth.iqoption.com/api/v2/login';
    this.wsUrl = 'wss://ws.iqoption.com/echo/websocket';
    this.baseUrl = 'https://iqoption.com';
  }

  async connect() {
    try {
      this.logger.info('🚀 CONECTANDO A IQ OPTION OFICIAL...');
      
      // Paso 1: Login HTTP oficial
      await this.officialLogin();
      
      // Paso 2: WebSocket oficial
      await this.connectOfficialWebSocket();
      
      this.logger.info('✅ CONECTADO A IQ OPTION OFICIAL');
      
    } catch (error) {
      this.logger.error('❌ Error conectando a IQ Option:', error.message);
      throw error;
    }
  }

  async officialLogin() {
    try {
      this.logger.info('🔐 Login oficial a IQ Option...');
      
      // Verificar credenciales
      if (!config.iqOption.email || !config.iqOption.password) {
        throw new Error('❌ Credenciales no configuradas en .env');
      }

      // Configurar sesión con cookies de plataforma
      this.session.defaults.headers.common['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
      
      // Payload oficial según documentación
      const loginPayload = {
        identifier: config.iqOption.email,
        password: config.iqOption.password,
        remember: false,
        affiliate_promocode: ""
      };

      this.logger.info(`📧 Autenticando: ${config.iqOption.email}`);

      // Request oficial a auth.iqoption.com
      const response = await this.session.post(this.authUrl, loginPayload, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Origin': 'https://iqoption.com',
          'Referer': 'https://iqoption.com/'
        },
        timeout: 20000
      });

      this.logger.info(`📡 Respuesta oficial - Status: ${response.status}`);
      this.logger.info('📄 Respuesta completa:', JSON.stringify(response.data, null, 2));

      if (response.status === 200 && response.data) {
        // Verificar diferentes formatos de respuesta exitosa
        if (response.data.isSuccessful === true || response.data.code === 'success') {
          // Extraer SSID de cookies o respuesta
          if (response.headers['set-cookie']) {
            const ssidCookie = response.headers['set-cookie'].find(cookie => 
              cookie.includes('ssid=')
            );
            
            if (ssidCookie) {
              this.ssid = ssidCookie.match(/ssid=([^;]+)/)[1];
              this.logger.info('✅ SSID extraído de cookies');
            }
          }
          
          // También buscar en el resultado o directamente en data
          if (!this.ssid && response.data.result && response.data.result.ssid) {
            this.ssid = response.data.result.ssid;
            this.logger.info('✅ SSID extraído de resultado');
          } else if (!this.ssid && response.data.ssid) {
            this.ssid = response.data.ssid;
            this.logger.info('✅ SSID extraído directamente de respuesta');
          }

          if (!this.ssid) {
            throw new Error('No se pudo obtener SSID de la respuesta');
          }

          // Configurar cookies de sesión
          this.setupSessionCookies();
          
          this.logger.info('✅ LOGIN OFICIAL EXITOSO');
          
        } else {
          const errorMsg = response.data.message || response.data.error || 'Credenciales incorrectas';
          this.logger.error('❌ Estructura de respuesta no reconocida:', response.data);
          throw new Error(`❌ Login falló: ${errorMsg}`);
        }
      } else {
        throw new Error(`❌ Error HTTP ${response.status}: ${response.statusText}`);
      }

    } catch (error) {
      if (error.code === 'ENOTFOUND') {
        throw new Error('❌ No se puede conectar a IQ Option. Verifica tu conexión a internet.');
      } else if (error.response && error.response.status === 400) {
        throw new Error('❌ Credenciales incorrectas. Verifica email y contraseña.');
      } else if (error.response) {
        this.logger.error('📄 Error response status:', error.response.status);
        this.logger.error('📄 Error response data:', error.response.data);
        this.logger.error('📄 Error response headers:', error.response.headers);
        throw new Error(`❌ Error de IQ Option: ${error.response.data.message || error.message}`);
      } else {
        this.logger.error('📄 Error completo:', error);
        throw new Error(`❌ Error de conexión: ${error.message}`);
      }
    }
  }

  setupSessionCookies() {
    // Configurar cookies de plataforma según documentación
    this.session.defaults.headers.Cookie = `ssid=${this.ssid}; platform=9`;
  }

  async connectOfficialWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        this.logger.info('🔌 Conectando WebSocket oficial...');
        
        // WebSocket oficial: wss://ws.iqoption.com/echo/websocket
        this.ws = new WebSocket(this.wsUrl, {
          headers: {
            'Origin': 'https://iqoption.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': `ssid=${this.ssid}; platform=9`
          }
        });

        let isResolved = false;

        this.ws.on('open', () => {
          this.logger.info('✅ WebSocket OFICIAL conectado');
          this.isConnected = true;
          
          // Enviar SSID inmediatamente
          this.sendSSID();
          
          // Configurar heartbeat
          this.setupHeartbeat();
          
          if (!isResolved) {
            isResolved = true;
            resolve();
          }
        });

        this.ws.on('message', (data) => {
          this.handleOfficialMessage(data);
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

        // Timeout de 30 segundos
        setTimeout(() => {
          if (!isResolved) {
            isResolved = true;
            reject(new Error('Timeout conectando WebSocket oficial'));
          }
        }, 30000);

      } catch (error) {
        reject(error);
      }
    });
  }

  sendSSID() {
    // Enviar SSID según protocolo oficial
    const ssidMessage = {
      name: 'ssid',
      msg: this.ssid
    };
    
    this.sendMessage(ssidMessage);
    this.logger.info('🔑 SSID enviado al WebSocket oficial');

    // Solicitar perfil para confirmar autenticación
    setTimeout(() => {
      this.requestProfile();
    }, 2000);
  }

  requestProfile() {
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
    this.logger.info('👤 Solicitando perfil oficial...');
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

  handleOfficialMessage(data) {
    try {
      const message = JSON.parse(data.toString());
      
      // Log TODOS los mensajes para debug
      this.logger.info(`📨 IQ OFICIAL: ${message.name}`);
      
      // Log completo de TODOS los mensajes
      this.logger.info(`📄 Mensaje completo:`, JSON.stringify(message, null, 2));
      
      // Procesar mensajes según protocolo oficial
      switch (message.name) {
        case 'profile':
          this.handleProfile(message.msg);
          break;
          
        case 'candle-generated':
          this.handleOfficialCandle(message.msg);
          break;
          
        case 'quote-generated':
          this.handleOfficialQuote(message.msg);
          break;
          
        case 'candles':
          this.handleHistoricalCandles(message);
          break;
          
        case 'listInfoData':
          this.logger.info('📋 Lista de activos oficial recibida');
          break;
          
        case 'timeSync':
          // Sincronización de tiempo
          break;
          
        default:
          // Otros mensajes
          break;
      }
      
      this.emit('message', message);
      
    } catch (error) {
      this.logger.error('Error procesando mensaje oficial:', error.message);
    }
  }

  handleProfile(profileData) {
    if (profileData && profileData.email) {
      this.logger.info('✅ PERFIL OFICIAL CONFIRMADO');
      this.logger.info(`👤 Usuario: ${profileData.email}`);
      this.logger.info(`💰 Balance: ${profileData.balance || 'N/A'}`);
      this.logger.info(`🏛️ Cuenta: ${profileData.demo ? 'DEMO' : 'REAL'}`);
      
      // Ahora que estamos autenticados, suscribirse a datos en tiempo real
      setTimeout(() => {
        this.subscribeToRealTimeData();
      }, 2000);
    }
  }

  subscribeToRealTimeData() {
    // Usar activos regulares de Forex que siempre tienen datos
    const assets = [
      { name: 'EURUSD', id: 1 },
      { name: 'GBPUSD', id: 2 }, 
      { name: 'USDJPY', id: 3 },
      { name: 'AUDUSD', id: 4 }
    ];
    
    assets.forEach(assetInfo => {
      
      // Suscribirse a cotizaciones en tiempo real
      const quoteSubscription = {
        name: 'subscribeMessage',
        msg: {
          name: 'quote-generated',
          params: {
            routingFilters: {
              active_id: assetInfo.id
            }
          }
        }
      };
      
      // Suscribirse a velas
      const candleSubscription = {
        name: 'subscribeMessage', 
        msg: {
          name: 'candle-generated',
          params: {
            routingFilters: {
              active_id: assetInfo.id,
              size: 60
            }
          }
        }
      };
      
      this.sendMessage(quoteSubscription);
      this.sendMessage(candleSubscription);
      
      this.logger.info(`🔔 Suscrito a datos REALES de ${assetInfo.name} (ID: ${assetInfo.id})`);
    });
  }

  handleOfficialCandle(candleData) {
    try {
      if (!candleData || typeof candleData.active_id === 'undefined') return;
      
      const processedCandle = {
        asset: this.getOfficialAssetName(candleData.active_id),
        timestamp: candleData.from * 1000,
        open: parseFloat(candleData.open),
        high: parseFloat(candleData.max),
        low: parseFloat(candleData.min),
        close: parseFloat(candleData.close),
        volume: candleData.volume || 0,
        timeframe: candleData.size || 60
      };
      
      this.logger.info(`📊 VELA OFICIAL: ${processedCandle.asset} ${processedCandle.close}`);
      this.emit('candle', processedCandle);
      
    } catch (error) {
      this.logger.error('Error procesando vela oficial:', error.message);
    }
  }

  handleOfficialQuote(quoteData) {
    try {
      if (!quoteData || typeof quoteData.active_id === 'undefined') {
        this.logger.warn('Datos de cotización inválidos:', quoteData);
        return;
      }
      
      const asset = this.getOfficialAssetName(quoteData.active_id);
      const price = parseFloat(quoteData.value);
      
      if (isNaN(price)) {
        this.logger.warn(`Precio inválido para ${asset}:`, quoteData.value);
        return;
      }
      
      const processedQuote = {
        asset: asset,
        timestamp: Date.now(),
        bid: price,
        ask: price,
        spread: 0
      };
      
      // Log para verificar que recibimos datos reales
      this.logger.info(`💱 COTIZACIÓN REAL: ${asset} = ${price}`);
      
      this.emit('quote', processedQuote);
      
    } catch (error) {
      this.logger.error('Error procesando cotización oficial:', error.message);
    }
  }

  async subscribeToCandles(asset, timeframe = 60) {
    try {
      const activeId = this.getOfficialAssetId(asset);
      
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
      
      this.logger.info(`📈 SUSCRITO OFICIAL: ${asset} (${timeframe}s)`);
      
    } catch (error) {
      this.logger.error(`Error suscribiéndose oficialmente a ${asset}:`, error.message);
    }
  }

  async subscribeToQuotes(asset) {
    try {
      const activeId = this.getOfficialAssetId(asset);
      
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
      this.logger.info(`💱 SUSCRITO A COTIZACIONES OFICIALES: ${asset}`);
      
    } catch (error) {
      this.logger.error(`Error suscribiéndose a cotizaciones oficiales de ${asset}:`, error.message);
    }
  }

  async getCandles(asset, timeframe, count = 100) {
    try {
      const activeId = this.getOfficialAssetId(asset);
      
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
          reject(new Error('Timeout obteniendo velas oficiales'));
        }, 20000);

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
              
              this.logger.info(`📊 ${candles.length} velas históricas OFICIALES para ${asset}`);
              resolve(candles);
            } else {
              reject(new Error('Respuesta inválida de velas históricas oficiales'));
            }
          }
        };

        this.on('message', messageHandler);
        this.sendMessage(message);
      });

    } catch (error) {
      this.logger.error(`Error obteniendo velas históricas oficiales de ${asset}:`, error.message);
      throw error;
    }
  }

  getOfficialAssetId(asset) {
    // IDs oficiales de IQ Option para activos OTC
    const officialAssetMap = {
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

    return officialAssetMap[asset] || 1;
  }

  getOfficialAssetName(activeId) {
    const officialIdToAsset = {
      1: 'EURUSD',
      2: 'GBPUSD', 
      3: 'USDJPY',
      4: 'AUDUSD',
      5: 'USDCAD',
      6: 'EURJPY',
      7: 'GBPJPY',
      8: 'EURGBP',
      9: 'AUDJPY',
      10: 'NZDUSD'
    };

    return officialIdToAsset[activeId] || 'UNKNOWN';
  }

  sendMessage(message) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.logger.warn('No se puede enviar mensaje - WebSocket oficial no conectado');
    }
  }

  getRequestId() {
    return this.requestId++;
  }

  async disconnect() {
    try {
      this.logger.info('Desconectando de IQ Option oficial...');
      
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      
      this.isConnected = false;
      this.subscriptions.clear();
      
      this.logger.info('Desconectado de IQ Option oficial');
      
    } catch (error) {
      this.logger.error('Error al desconectar de IQ Option oficial:', error.message);
    }
  }

  isConnectionActive() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

module.exports = IQOptionOfficial;
