const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function ultra2YearsAll() {
  const logger = new Logger('ULTRA-2Y');
  
  try {
    logger.info('🚀 MODO ULTRA: 2 AÑOS COMPLETOS PARA TODOS LOS PARES');
    
    // Todos los 15 pares OTC
    const allAssets = [
      'EURUSD-OTC',
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
    
    const daysBack = 730; // 2 años completos
    const totalStartTime = Date.now();
    let totalVelas = 0;
    let completedPairs = 0;
    
    logger.info(`📊 EXPANSIÓN A 2 AÑOS:`);
    logger.info(`   📅 Período: 730 días (2 años)`);
    logger.info(`   🎯 Pares: ${allAssets.length}`);
    logger.info(`   📈 Velas esperadas: ~${(allAssets.length * daysBack * 1440).toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo estimado: 30-40 minutos`);
    
    for (let i = 0; i < allAssets.length; i++) {
      const asset = allAssets[i];
      const pairNumber = i + 1;
      
      try {
        logger.info(`\n🔄 PAR ${pairNumber}/15: ${asset} (2 AÑOS)`);
        
        const downloader = new HistoricalDownloader(null);
        await downloader.initialize();
        
        const startTime = Date.now();
        const saved = await downloader.analyzeAndSaveRetrospective(asset, daysBack);
        const endTime = Date.now();
        
        const duration = Math.round((endTime - startTime) / 1000);
        const minutes = Math.round(duration / 60);
        const speed = Math.round(saved / duration);
        
        totalVelas += saved;
        completedPairs++;
        
        const progress = Math.round((completedPairs / allAssets.length) * 100);
        
        logger.info(`✅ ${asset} COMPLETADO:`);
        logger.info(`   📊 Velas: ${saved.toLocaleString()}`);
        logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
        logger.info(`   🔥 Velocidad: ${speed} velas/segundo`);
        logger.info(`   📈 Progreso total: ${progress}% (${completedPairs}/${allAssets.length})`);
        
        await downloader.close();
        
        // Pequeña pausa para estabilidad
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } catch (error) {
        logger.error(`❌ Error procesando ${asset}:`, error.message);
        continue;
      }
    }
    
    const totalEndTime = Date.now();
    const totalDuration = Math.round((totalEndTime - totalStartTime) / 1000);
    const totalMinutes = Math.round(totalDuration / 60);
    
    logger.info(`\n🎯 EXPANSIÓN A 2 AÑOS COMPLETADA:`);
    logger.info(`   📊 Total velas procesadas: ${totalVelas.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo total: ${totalMinutes} minutos (${totalDuration}s)`);
    logger.info(`   🔥 Velocidad promedio: ${Math.round(totalVelas/totalDuration)} velas/segundo`);
    logger.info(`   ✅ Pares completados: ${completedPairs}/${allAssets.length}`);
    logger.info(`   🎯 Cobertura: 2 años completos (730 días)`);
    logger.info(`   🤖 Base de datos ULTRA ROBUSTA para IA`);
    
  } catch (error) {
    logger.error('❌ Error en expansión a 2 años:', error);
    process.exit(1);
  }
}

ultra2YearsAll()
  .then(() => {
    console.log('🎉 EXPANSIÓN A 2 AÑOS COMPLETADA - BASE DE DATOS ULTRA ROBUSTA');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error en expansión a 2 años:', error);
    process.exit(1);
  });
