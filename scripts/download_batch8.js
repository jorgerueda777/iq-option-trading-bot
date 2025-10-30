const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function downloadBatch8() {
  const logger = new Logger('Batch8');
  
  try {
    logger.info('🔄 BATCH 8: CADCHF-OTC');
    
    const downloader = new HistoricalDownloader(null);
    await downloader.initialize();
    
    const assets = ['CADCHF-OTC'];
    const daysBack = 180;
    
    logger.info(`📊 Procesando ${assets.length} par × ${daysBack} días = ${assets.length * daysBack * 1440} velas`);
    
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
    
    logger.info(`\n🎯 BATCH 8 COMPLETADO:`);
    logger.info(`   📊 Total velas: ${totalSaved.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo: ${minutes} minutos`);
    
    await downloader.close();
    
  } catch (error) {
    logger.error('❌ Error en Batch 8:', error);
    process.exit(1);
  }
}

downloadBatch8()
  .then(() => {
    console.log('\n✅ Batch 8 completado');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Batch 8 falló:', error);
    process.exit(1);
  });
