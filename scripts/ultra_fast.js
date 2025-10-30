const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function ultraFast() {
  const logger = new Logger('ULTRA');
  
  try {
    logger.info('🚀 MODO ULTRA RÁPIDO ACTIVADO');
    
    const downloader = new HistoricalDownloader(null);
    await downloader.initialize();
    
    // Solo EURUSD-OTC para máxima velocidad
    const asset = 'EURUSD-OTC';
    const daysBack = 180;
    
    logger.info(`⚡ Procesando ${asset} - ${daysBack} días a MÁXIMA VELOCIDAD`);
    
    const startTime = Date.now();
    
    const saved = await downloader.analyzeAndSaveRetrospective(asset, daysBack);
    
    const endTime = Date.now();
    const duration = Math.round((endTime - startTime) / 1000);
    const minutes = Math.round(duration / 60);
    
    logger.info(`🎯 ULTRA COMPLETADO:`);
    logger.info(`   📊 Velas: ${saved.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
    logger.info(`   🔥 Velocidad: ${Math.round(saved/duration)} velas/segundo`);
    
    await downloader.close();
    
  } catch (error) {
    logger.error('❌ Error ULTRA:', error);
    process.exit(1);
  }
}

ultraFast()
  .then(() => {
    console.log('🚀 ULTRA COMPLETADO');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ ULTRA FALLÓ:', error);
    process.exit(1);
  });
