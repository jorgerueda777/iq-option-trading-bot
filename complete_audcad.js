const HistoricalDownloader = require('./src/utils/historicalDownloader');
const IQOptionOTCConnector = require('./src/connectors/iqOptionOTC');
const Logger = require('./src/utils/logger');

async function completeAUDCAD() {
  const logger = new Logger('AUDCAD-Completer');
  const iqConnector = new IQOptionOTCConnector();
  const downloader = new HistoricalDownloader(iqConnector);
  
  try {
    logger.info('🚀 Completando descarga de AUDCAD-OTC...');
    
    // Inicializar descargador
    await downloader.initialize();
    logger.info('✅ Base de datos inicializada');
    
    // Verificar datos actuales
    const result = await downloader.db.get(
      'SELECT COUNT(*) as count FROM candles WHERE asset = ?',
      ['AUDCAD-OTC']
    );
    const currentCount = result ? result.count : 0;
    logger.info(`📊 AUDCAD-OTC actual: ${currentCount.toLocaleString()} velas`);
    
    // Descargar 730 días de datos
    logger.info('🔄 Descargando 2 años de datos para AUDCAD-OTC...');
    const candlesCount = await downloader.analyzeAndSaveRetrospective('AUDCAD-OTC', 730);
    
    logger.info(`✅ AUDCAD-OTC completado: ${candlesCount.toLocaleString()} velas descargadas`);
    
    // Verificar datos finales
    const finalResult = await downloader.db.get(
      'SELECT COUNT(*) as count FROM candles WHERE asset = ?',
      ['AUDCAD-OTC']
    );
    const finalCount = finalResult ? finalResult.count : 0;
    logger.info(`📊 AUDCAD-OTC final: ${finalCount.toLocaleString()} velas en base de datos`);
    
    logger.info('🎉 ¡AUDCAD-OTC completado exitosamente!');
    
  } catch (error) {
    logger.error('❌ Error completando AUDCAD-OTC:', error);
  } finally {
    process.exit(0);
  }
}

completeAUDCAD();
