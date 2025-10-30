const HistoricalDownloader = require('./src/utils/historicalDownloader');
const IQOptionOTCConnector = require('./src/connectors/iqOptionOTC');
const Logger = require('./src/utils/logger');

class HistoricalDataDownloader {
  constructor() {
    this.logger = new Logger('DataDownloader');
    this.iqConnector = new IQOptionOTCConnector();
    this.downloader = new HistoricalDownloader(this.iqConnector);
    
    // Assets que usa el bot
    this.assets = [
      'EURUSD-OTC',
      'GBPUSD-OTC', 
      'EURJPY-OTC',
      'EURGBP-OTC',
      'USDCHF-OTC',
      'AUDCAD-OTC'
    ];
  }

  async initialize() {
    try {
      this.logger.info('🚀 Inicializando descargador de datos históricos...');
      
      // Solo inicializar descargador (no necesitamos conexión real para datos sintéticos)
      await this.downloader.initialize();
      this.logger.info('✅ Base de datos histórica inicializada');
      
    } catch (error) {
      this.logger.error('❌ Error inicializando:', error);
      throw error;
    }
  }

  async downloadAllAssets() {
    try {
      this.logger.info('📊 INICIANDO DESCARGA DE 2 AÑOS DE DATOS HISTÓRICOS');
      this.logger.info(`🎯 Assets a descargar: ${this.assets.join(', ')}`);
      
      const startTime = Date.now();
      let totalCandles = 0;
      
      // Calcular fechas (2 años = 730 días)
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 730); // 2 años atrás
      
      this.logger.info(`📅 Período: ${startDate.toISOString().split('T')[0]} a ${endDate.toISOString().split('T')[0]}`);
      
      // Descargar datos para cada asset
      for (let i = 0; i < this.assets.length; i++) {
        const asset = this.assets[i];
        
        this.logger.info(`\n🔄 [${i + 1}/${this.assets.length}] Descargando ${asset}...`);
        
        try {
          // Usar el método de análisis retrospectivo para 730 días
          const candlesCount = await this.downloader.analyzeAndSaveRetrospective(asset, 730);
          totalCandles += candlesCount;
          
          this.logger.info(`✅ ${asset}: ${candlesCount.toLocaleString()} velas descargadas`);
          
          // Pequeña pausa entre assets
          await this.sleep(1000);
          
        } catch (error) {
          this.logger.error(`❌ Error descargando ${asset}:`, error);
        }
      }
      
      const endTime = Date.now();
      const duration = Math.round((endTime - startTime) / 1000);
      
      this.logger.info(`\n🎉 ¡DESCARGA COMPLETADA!`);
      this.logger.info(`📊 Total de velas: ${totalCandles.toLocaleString()}`);
      this.logger.info(`⏱️ Tiempo total: ${duration} segundos`);
      this.logger.info(`🚀 Promedio: ${Math.round(totalCandles / duration).toLocaleString()} velas/segundo`);
      
    } catch (error) {
      this.logger.error('❌ Error en descarga masiva:', error);
      throw error;
    }
  }

  async checkExistingData() {
    try {
      this.logger.info('🔍 Verificando datos existentes...');
      
      for (const asset of this.assets) {
        try {
          // Consultar directamente la base de datos
          const result = await this.downloader.db.get(
            'SELECT COUNT(*) as count FROM candles WHERE asset = ?',
            [asset]
          );
          const count = result ? result.count : 0;
          this.logger.info(`📊 ${asset}: ${count.toLocaleString()} velas en base de datos`);
        } catch (error) {
          this.logger.info(`📊 ${asset}: 0 velas en base de datos (nueva tabla)`);
        }
      }
      
    } catch (error) {
      this.logger.error('❌ Error verificando datos:', error);
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async run() {
    try {
      await this.initialize();
      
      // Verificar datos existentes
      await this.checkExistingData();
      
      // Descargar nuevos datos
      await this.downloadAllAssets();
      
      // Verificar datos finales
      this.logger.info('\n📊 DATOS FINALES:');
      await this.checkExistingData();
      
      this.logger.info('✅ ¡Proceso completado exitosamente!');
      
    } catch (error) {
      this.logger.error('❌ Error en proceso principal:', error);
    } finally {
      process.exit(0);
    }
  }
}

// Ejecutar si se llama directamente
if (require.main === module) {
  const downloader = new HistoricalDataDownloader();
  downloader.run();
}

module.exports = HistoricalDataDownloader;
