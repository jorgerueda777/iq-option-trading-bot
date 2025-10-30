const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function ultraUSDJPY() {
  const logger = new Logger('ULTRA-JPY');
  
  try {
    logger.info('🚀 MODO ULTRA: USDJPY-OTC');
    
    const downloader = new HistoricalDownloader(null);
    await downloader.initialize();
    
    const asset = 'USDJPY-OTC';
    const daysBack = 180;
    
    logger.info(`⚡ Procesando ${asset} - ${daysBack} días a MÁXIMA VELOCIDAD`);
    
    const startTime = Date.now();
    
    const saved = await downloader.analyzeAndSaveRetrospective(asset, daysBack);
    
    const endTime = Date.now();
    const duration = Math.round((endTime - startTime) / 1000);
    const minutes = Math.round(duration / 60);
    
    logger.info(`🎯 ${asset} COMPLETADO:`);
    logger.info(`   📊 Velas: ${saved.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
    logger.info(`   🔥 Velocidad: ${Math.round(saved/duration)} velas/segundo`);
    
    await downloader.close();
    
  } catch (error) {
    logger.error('❌ Error USDJPY:', error);
    process.exit(1);
  }
}

ultraUSDJPY()
  .then(() => {
    console.log('🚀 USDJPY-OTC COMPLETADO');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ USDJPY FALLÓ:', error);
    process.exit(1);
  });
