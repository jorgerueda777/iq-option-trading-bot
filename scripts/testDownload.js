const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function testDownload() {
  const logger = new Logger('TestRetrospective');
  
  try {
    logger.info('🔄 PROBANDO ANÁLISIS RETROSPECTIVO COMPLETO');
    
    // Inicializar descargador (sin conector IQ)
    const downloader = new HistoricalDownloader(null);
    await downloader.initialize();
    
    logger.info('✅ Base de datos inicializada');
    
    // PROCESAR TODOS LOS PARES SIMULTÁNEAMENTE
    const assets = [
      'EURUSD-OTC',  // Ya tiene datos, se saltará
      'GBPUSD-OTC',
      'USDJPY-OTC', 
      'AUDUSD-OTC',
      'USDCAD-OTC',
      'EURJPY-OTC',
      'GBPJPY-OTC',
      'EURGBP-OTC',
      'AUDJPY-OTC',
      'NZDUSD-OTC',
      'USDCHF-OTC',
      'EURCHF-OTC',
      'GBPCHF-OTC',
      'AUDCHF-OTC',
      'CADCHF-OTC'
    ];
    
    const daysBack = 180; // 6 meses = ~180 días
    
    logger.info(`🚀 PROCESAMIENTO MASIVO PARALELO:`);
    logger.info(`   📊 ${assets.length} pares × ${daysBack} días × 1440 minutos = ${assets.length * daysBack * 1440} velas totales`);
    
    const startTime = Date.now();
    
    try {
      // PROCESAR TODOS LOS PARES SIMULTÁNEAMENTE (INCLUYENDO EURUSD)
      logger.info(`🚀 Iniciando procesamiento simultáneo de ${assets.length} pares...`);
      
      const promises = assets.map(async (asset, index) => {
        try {
          logger.info(`🔄 [${index + 1}/${assets.length}] Iniciando ${asset}...`);
          const saved = await downloader.analyzeAndSaveRetrospective(asset, daysBack);
          logger.info(`✅ [${index + 1}/${assets.length}] ${asset} COMPLETADO: ${saved.toLocaleString()} velas`);
          return { asset, saved, success: true };
        } catch (error) {
          logger.error(`❌ [${index + 1}/${assets.length}] ${asset} FALLÓ: ${error.message}`);
          return { asset, saved: 0, success: false, error: error.message };
        }
      });
      
      // Esperar a que todos terminen simultáneamente
      logger.info(`⏳ Esperando a que completen los ${assets.length} pares...`);
      const results = await Promise.all(promises);
      
      const endTime = Date.now();
      const duration = Math.round((endTime - startTime) / 1000);
      const minutes = Math.round(duration / 60);
      
      // Resumen final
      const successful = results.filter(r => r.success);
      const failed = results.filter(r => !r.success);
      const totalVelas = successful.reduce((sum, r) => sum + r.saved, 0);
      
      logger.info(`\n🎯 PROCESAMIENTO MASIVO COMPLETADO:`);
      logger.info(`   ✅ Exitosos: ${successful.length}/${assets.length} pares`);
      logger.info(`   ❌ Fallidos: ${failed.length}/${assets.length} pares`);
      logger.info(`   📊 Total velas: ${totalVelas.toLocaleString()}`);
      logger.info(`   ⏱️ Tiempo total: ${minutes} minutos (${duration} segundos)`);
      
      if (failed.length > 0) {
        logger.warn(`\n⚠️ Pares que fallaron:`);
        failed.forEach(f => logger.warn(`   - ${f.asset}: ${f.error}`));
      }
      
      // Mostrar estadísticas finales
      const stats = await downloader.getStats();
      logger.info(`\n📈 ESTADÍSTICAS FINALES:`);
      stats.forEach(stat => {
        logger.info(`📊 ${stat.asset}: ${stat.total_candles.toLocaleString()} velas (${stat.oldest_date} → ${stat.newest_date})`);
      });
      
    } catch (error) {
      logger.error(`❌ Error en procesamiento masivo:`, error.message);
    }
    
    // Cerrar base de datos
    await downloader.close();
    logger.info('\n🎉 PRUEBA COMPLETADA');
    
  } catch (error) {
    logger.error('❌ Error en prueba:', error);
    process.exit(1);
  }
}

// Ejecutar
testDownload()
  .then(() => {
    console.log('\n✅ Descarga exitosa');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Descarga falló:', error);
    process.exit(1);
  });
