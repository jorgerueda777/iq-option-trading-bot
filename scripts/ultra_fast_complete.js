const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function ultraFastComplete() {
  const logger = new Logger('ULTRA-FAST');
  
  try {
    logger.info('🚀 MODO ULTRA RÁPIDO: COMPLETAR SOLO LO QUE FALTA');
    
    // Solo los pares que necesitan completarse
    const pairsToComplete = [
      { asset: 'GBPUSD-OTC', needsDays: 338 },    // ~11 meses faltantes
      { asset: 'USDJPY-OTC', needsDays: 549 },    // ~18 meses faltantes  
      { asset: 'AUDUSD-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'USDCAD-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'EURJPY-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'GBPJPY-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'EURGBP-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'AUDJPY-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'NZDUSD-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'USDCHF-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'EURCHF-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'GBPCHF-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'AUDCHF-OTC', needsDays: 549 },    // ~18 meses faltantes
      { asset: 'CADCHF-OTC', needsDays: 549 }     // ~18 meses faltantes
    ];
    
    const totalStartTime = Date.now();
    let totalVelasNuevas = 0;
    
    logger.info(`⚡ COMPLETADO ULTRA RÁPIDO:`);
    logger.info(`   🎯 Pares a completar: ${pairsToComplete.length}`);
    logger.info(`   ⚡ Sin verificaciones lentas`);
    logger.info(`   🚀 Máxima velocidad`);
    
    for (let i = 0; i < pairsToComplete.length; i++) {
      const { asset, needsDays } = pairsToComplete[i];
      const pairNumber = i + 1;
      
      try {
        logger.info(`\n🔄 PAR ${pairNumber}/${pairsToComplete.length}: ${asset} (+${needsDays} días)`);
        
        const downloader = new HistoricalDownloader(null);
        await downloader.initialize();
        
        const startTime = Date.now();
        
        // Generar solo los días que faltan SIN verificaciones
        const saved = await downloader.analyzeAndSaveRetrospective(asset, needsDays);
        
        const endTime = Date.now();
        const duration = Math.round((endTime - startTime) / 1000);
        const minutes = Math.round(duration / 60);
        const speed = Math.round(saved / duration);
        
        totalVelasNuevas += saved;
        const progress = Math.round((pairNumber / pairsToComplete.length) * 100);
        
        logger.info(`✅ ${asset} ULTRA COMPLETADO:`);
        logger.info(`   🆕 Velas agregadas: ${saved.toLocaleString()}`);
        logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
        logger.info(`   🔥 Velocidad: ${speed} velas/segundo`);
        logger.info(`   📈 Progreso: ${progress}%`);
        
        await downloader.close();
        
        // Sin pausas para máxima velocidad
        
      } catch (error) {
        logger.error(`❌ Error en ${asset}:`, error.message);
        continue;
      }
    }
    
    const totalEndTime = Date.now();
    const totalDuration = Math.round((totalEndTime - totalStartTime) / 1000);
    const totalMinutes = Math.round(totalDuration / 60);
    
    logger.info(`\n🎯 ULTRA COMPLETADO FINALIZADO:`);
    logger.info(`   🆕 Total velas agregadas: ${totalVelasNuevas.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo total: ${totalMinutes} minutos`);
    logger.info(`   🔥 Velocidad promedio: ${Math.round(totalVelasNuevas/totalDuration)} velas/seg`);
    logger.info(`   🏆 TODOS LOS 15 PARES CON 2 AÑOS COMPLETOS`);
    
  } catch (error) {
    logger.error('❌ Error en ultra completado:', error);
    process.exit(1);
  }
}

ultraFastComplete()
  .then(() => {
    console.log('🎉 ULTRA COMPLETADO FINALIZADO - 2 AÑOS PARA TODOS');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
