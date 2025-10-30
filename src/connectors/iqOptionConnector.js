const WebSocket = require('ws');
const axios = require('axios');
const EventEmitter = require('events');
const config = require('../../config/config');
const Logger = require('../utils/logger');

class IQOptionConnector extends EventEmitter {
  constructor() {
    super();
    this.logger = new Logger('IQConnector');
    this.ws = null;
    this.isConnected = false;
    this.sessionId = null;
    this.ssid = null;
    this.requestId = 1;
    this.subscriptions = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 5000;
  }

  async connect() {
    try {
      this.logger.info('Conectando a IQ Option...');
      
      // Primero autenticarse via HTTP
      await this.authenticate();
      
      // Luego conectar WebSocket
      await this.connectWebSocket();
      
      this.logger.info('Conectado exitosamente a IQ Option');
      
    } catch (error) {
      this.logger.error('Error al conectar:', error);
      throw error;
    }
  }

  async authenticate() {
    try {
      // Verificar si hay credenciales configuradas
      if (!config.iqOption.email || !config.iqOption.password) {
        this.logger.warn('Credenciales no configuradas, usando modo demo');
        this.ssid = 'demo_session_' + Date.now();
        return;
      }

      const loginData = {
        email: config.iqOption.email,
        password: config.iqOption.password,
        platform: 'web'
      };

      const response = await axios.post(`${config.iqOption.apiUrl}/login`, loginData, {
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        withCredentials: true,
        timeout: 10000
      });

      if (response.data && response.data.isSuccessful) {
        this.ssid = response.data.ssid;
        this.logger.info('Autenticación exitosa');
      } else {
        throw new Error('Fallo en la autenticación: ' + (response.data?.message || 'Respuesta inválida'));
      }

    } catch (error) {
      this.logger.error('Error en autenticación:', error.message);
      // En modo demo, continuar sin autenticación real
      this.logger.warn('Continuando en modo demo');
      this.ssid = 'demo_session_' + Date.now();
    }
  }

  async connectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        // Si estamos en modo demo, simular conexión
        if (this.ssid.startsWith('demo_session_')) {
          this.logger.info('Iniciando modo demo - simulando WebSocket');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startDemoMode();
          resolve();
          return;
        }

        const wsUrl = `${config.iqOption.wsUrl}?ssid=${this.ssid}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.on('open', () => {
          this.logger.info('WebSocket conectado');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.setupHeartbeat();
          resolve();
        });

        this.ws.on('message', (data) => {
          this.handleMessage(data);
        });

        this.ws.on('close', () => {
          this.logger.warn('WebSocket desconectado');
          this.isConnected = false;
          this.handleReconnect();
        });

        this.ws.on('error', (error) => {
          this.logger.error('Error en WebSocket:', error);
          // En caso de error, cambiar a modo demo
          this.logger.warn('Cambiando a modo demo debido a error de conexión');
          this.startDemoMode();
          resolve();
        });

      } catch (error) {
        // Si hay error, usar modo demo
        this.logger.warn('Error conectando WebSocket, usando modo demo');
        this.startDemoMode();
        resolve();
      }
    });
  }

  handleMessage(data) {
    try {
      const message = JSON.parse(data.toString());
      
      // Manejar diferentes tipos de mensajes
      if (message.name === 'candles') {
        this.handleCandleData(message.msg);
      } else if (message.name === 'quote-generated') {
        this.handleQuoteData(message.msg);
      } else if (message.name === 'heartbeat') {
        // Responder al heartbeat
        this.sendHeartbeat();
      }
      
      this.emit('message', message);
      
    } catch (error) {
      this.logger.error('Error al procesar mensaje:', error);
    }
  }

  handleCandleData(candleData) {
    try {
      const processedCandle = {
        asset: candleData.active_id,
        timestamp: candleData.from * 1000,
        open: candleData.open,
        high: candleData.max,
        low: candleData.min,
        close: candleData.close,
        volume: candleData.volume || 0,
        timeframe: candleData.size
      };
      
      this.emit('candle', processedCandle);
      
    } catch (error) {
      this.logger.error('Error al procesar datos de vela:', error);
    }
  }

  handleQuoteData(quoteData) {
    try {
      const processedQuote = {
        asset: quoteData.active_id,
        timestamp: Date.now(),
        bid: quoteData.value,
        ask: quoteData.value,
        spread: 0
      };
      
      this.emit('quote', processedQuote);
      
    } catch (error) {
      this.logger.error('Error al procesar datos de cotización:', error);
    }
  }

  async subscribeToCandles(asset, timeframe = 60) {
    try {
      const message = {
        name: 'subscribeMessage',
        msg: {
          name: 'candle-generated',
          params: {
            routingFilters: {
              active_id: this.getAssetId(asset),
              size: timeframe
            }
          }
        }
      };

      this.sendMessage(message);
      
      const subscriptionKey = `${asset}_${timeframe}`;
      this.subscriptions.set(subscriptionKey, { asset, timeframe });
      
      this.logger.info(`Suscrito a velas de ${asset} (${timeframe}s)`);
      
    } catch (error) {
      this.logger.error(`Error al suscribirse a velas de ${asset}:`, error);
    }
  }

  async subscribeToQuotes(asset) {
    try {
      const message = {
        name: 'subscribeMessage',
        msg: {
          name: 'quote-generated',
          params: {
            routingFilters: {
              active_id: this.getAssetId(asset)
            }
          }
        }
      };

      this.sendMessage(message);
      this.logger.info(`Suscrito a cotizaciones de ${asset}`);
      
    } catch (error) {
      this.logger.error(`Error al suscribirse a cotizaciones de ${asset}:`, error);
    }
  }

  async getCandles(asset, timeframe, count = 100) {
    try {
      const message = {
        name: 'sendMessage',
        msg: {
          name: 'get-candles',
          version: '1.0',
          body: {
            active_id: this.getAssetId(asset),
            size: timeframe,
            to: Math.floor(Date.now() / 1000),
            count: count
          }
        },
        request_id: this.getRequestId()
      };

      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Timeout al obtener velas'));
        }, 10000);

        const messageHandler = (response) => {
          if (response.request_id === message.request_id) {
            clearTimeout(timeout);
            this.removeListener('message', messageHandler);
            
            if (response.msg && response.msg.candles) {
              const candles = response.msg.candles.map(candle => ({
                asset: asset,
                timestamp: candle.from * 1000,
                open: candle.open,
                high: candle.max,
                low: candle.min,
                close: candle.close,
                volume: candle.volume || 0
              }));
              resolve(candles);
            } else {
              reject(new Error('Respuesta inválida'));
            }
          }
        };

        this.on('message', messageHandler);
        this.sendMessage(message);
      });

    } catch (error) {
      this.logger.error(`Error al obtener velas de ${asset}:`, error);
      throw error;
    }
  }

  getAssetId(asset) {
    // Mapeo de nombres de activos a IDs
    const assetMap = {
      'EURUSD-OTC': 1,
      'GBPUSD-OTC': 2,
      'USDJPY-OTC': 3,
      'AUDUSD-OTC': 4,
      'USDCAD-OTC': 5,
      'EURJPY-OTC': 6,
      'GBPJPY-OTC': 7,
      'EURGBP-OTC': 8
    };

    return assetMap[asset] || 1;
  }

  sendMessage(message) {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.logger.warn('Intento de enviar mensaje sin conexión');
    }
  }

  sendHeartbeat() {
    const heartbeat = {
      name: 'heartbeat',
      msg: Date.now()
    };
    this.sendMessage(heartbeat);
  }

  setupHeartbeat() {
    setInterval(() => {
      if (this.isConnected) {
        this.sendHeartbeat();
      }
    }, 30000); // Cada 30 segundos
  }

  getRequestId() {
    return this.requestId++;
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.logger.info(`Intentando reconectar (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(error => {
          this.logger.error('Error en reconexión:', error);
        });
      }, this.reconnectDelay);
    } else {
      this.logger.error('Máximo número de intentos de reconexión alcanzado');
      this.emit('connection_failed');
    }
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
      
      this.logger.info('Desconectado exitosamente');
      
    } catch (error) {
      this.logger.error('Error al desconectar:', error);
    }
  }

  isConnectionActive() {
    return this.isConnected && (this.ws ? this.ws.readyState === WebSocket.OPEN : true);
  }

  // Modo demo para simular datos
  startDemoMode() {
    this.isConnected = true;
    this.logger.info('Modo demo iniciado - generando datos simulados');
    
    // Generar velas simuladas cada minuto
    setInterval(() => {
      if (this.isConnected) {
        config.assets.forEach(asset => {
          this.generateDemoCandle(asset);
        });
      }
    }, 60000); // Cada minuto

    // Generar cotizaciones simuladas cada 5 segundos
    setInterval(() => {
      if (this.isConnected) {
        config.assets.forEach(asset => {
          this.generateDemoQuote(asset);
        });
      }
    }, 5000); // Cada 5 segundos
  }

  generateDemoCandle(asset) {
    const now = Date.now();
    const basePrice = this.getBasePrice(asset);
    
    // Generar movimiento aleatorio
    const volatility = 0.001; // 0.1%
    const change = (Math.random() - 0.5) * volatility * 2;
    
    const open = basePrice * (1 + change);
    const close = open * (1 + (Math.random() - 0.5) * volatility);
    const high = Math.max(open, close) * (1 + Math.random() * volatility * 0.5);
    const low = Math.min(open, close) * (1 - Math.random() * volatility * 0.5);
    
    const candleData = {
      asset: asset,
      timestamp: now,
      open: parseFloat(open.toFixed(5)),
      high: parseFloat(high.toFixed(5)),
      low: parseFloat(low.toFixed(5)),
      close: parseFloat(close.toFixed(5)),
      volume: Math.floor(Math.random() * 1000) + 100,
      timeframe: 60
    };

    this.handleCandleData(candleData);
  }

  generateDemoQuote(asset) {
    const basePrice = this.getBasePrice(asset);
    const volatility = 0.0005;
    const change = (Math.random() - 0.5) * volatility * 2;
    const price = basePrice * (1 + change);

    const quoteData = {
      asset: asset,
      timestamp: Date.now(),
      bid: parseFloat(price.toFixed(5)),
      ask: parseFloat((price * 1.0001).toFixed(5)),
      spread: 0.0001
    };

    this.handleQuoteData(quoteData);
  }

  getBasePrice(asset) {
    const basePrices = {
      'EURUSD-OTC': 1.0850,
      'GBPUSD-OTC': 1.2650,
      'USDJPY-OTC': 149.50,
      'AUDUSD-OTC': 0.6550,
      'USDCAD-OTC': 1.3750,
      'EURJPY-OTC': 162.25,
      'GBPJPY-OTC': 189.15,
      'EURGBP-OTC': 0.8580
    };
    
    return basePrices[asset] || 1.0000;
  }
}

module.exports = IQOptionConnector;
