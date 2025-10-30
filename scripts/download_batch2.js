const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function downloadBatch2() {
  const logger = new Logger('Batch2');
  
  try {
    logger.info('🔄 BATCH 2: USDJPY-OTC + AUDUSD-OTC');
    
    const downloader = new HistoricalDownloader(null);
    await downloader.initialize();
    
    const assets = ['USDJPY-OTC', 'AUDUSD-OTC'];
    const daysBack = 180;
    
    logger.info(`📊 Procesando ${assets.length} pares × ${daysBack} días = ${assets.length * daysBack * 1440} velas`);
    
    const startTime = Date.now();
    let totalSaved = 0;
    
    for (let i = 0; i < assets.length; i++) {
      const asset = assets[i];
      try {
        logger.info(`\n🔄 [${i + 1}/${assets.length}] PROCESANDO ${asset}...`);
        const saved = await downloader.analyzeAndSaveRetrospective(asset, daysBack);
        totalSaved += saved;
        
        logger.info(`✅ [${i + 1}/${assets.length}] ${asset} COMPLETADO: ${saved.toLocaleString()} velas`);
        
      } catch (error) {
        logger.error(`❌ [${i + 1}/${assets.length}] ${asset} FALLÓ: ${error.message}`);
      }
    }
    
    const endTime = Date.now();
    const duration = Math.round((endTime - startTime) / 1000);
    const minutes = Math.round(duration / 60);
    
    logger.info(`\n🎯 BATCH 2 COMPLETADO:`);
    logger.info(`   📊 Total velas: ${totalSaved.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo: ${minutes} minutos`);
    
    await downloader.close();
    
  } catch (error) {
    logger.error('❌ Error en Batch 2:', error);
    process.exit(1);
  }
}

downloadBatch2()
  .then(() => {
    console.log('\n✅ Batch 2 completado');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Batch 2 falló:', error);
    process.exit(1);
  });
