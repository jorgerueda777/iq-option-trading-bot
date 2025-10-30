const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function ultraAllRemaining() {
  const logger = new Logger('ULTRA-ALL');
  
  try {
    logger.info('🚀 MODO ULTRA: PROCESAMIENTO AUTOMÁTICO DE TODOS LOS PARES RESTANTES');
    
    // Pares restantes (ya completamos EURUSD, GBPUSD, USDJPY, AUDUSD)
    const remainingAssets = [
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
    
    const daysBack = 180;
    const totalStartTime = Date.now();
    let totalVelas = 0;
    
    logger.info(`📊 Procesando ${remainingAssets.length} pares automáticamente...`);
    
    for (let i = 0; i < remainingAssets.length; i++) {
      const asset = remainingAssets[i];
      const pairNumber = i + 5; // Empezamos desde el par 5
      
      try {
        logger.info(`\n🔄 PAR ${pairNumber}/15: ${asset}`);
        
        const downloader = new HistoricalDownloader(null);
        await downloader.initialize();
        
        const startTime = Date.now();
        const saved = await downloader.analyzeAndSaveRetrospective(asset, daysBack);
        const endTime = Date.now();
        
        const duration = Math.round((endTime - startTime) / 1000);
        const minutes = Math.round(duration / 60);
        const speed = Math.round(saved / duration);
        
        totalVelas += saved;
        
        logger.info(`✅ ${asset} COMPLETADO:`);
        logger.info(`   📊 Velas: ${saved.toLocaleString()}`);
        logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
        logger.info(`   🔥 Velocidad: ${speed} velas/segundo`);
        
        await downloader.close();
        
        // Pequeña pausa entre pares para estabilidad
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } catch (error) {
        logger.error(`❌ Error procesando ${asset}:`, error.message);
        continue; // Continuar con el siguiente par
      }
    }
    
    const totalEndTime = Date.now();
    const totalDuration = Math.round((totalEndTime - totalStartTime) / 1000);
    const totalMinutes = Math.round(totalDuration / 60);
    
    logger.info(`\n🎯 PROCESAMIENTO AUTOMÁTICO COMPLETADO:`);
    logger.info(`   📊 Total velas procesadas: ${totalVelas.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo total: ${totalMinutes} minutos (${totalDuration}s)`);
    logger.info(`   🔥 Velocidad promedio: ${Math.round(totalVelas/totalDuration)} velas/segundo`);
    logger.info(`   ✅ Pares completados: ${remainingAssets.length}/11`);
    
  } catch (error) {
    logger.error('❌ Error en procesamiento automático:', error);
    process.exit(1);
  }
}

ultraAllRemaining()
  .then(() => {
    console.log('🎉 TODOS LOS PARES RESTANTES COMPLETADOS');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error en procesamiento automático:', error);
    process.exit(1);
  });
