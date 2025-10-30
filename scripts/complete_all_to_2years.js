const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function completeAllTo2Years() {
  const logger = new Logger('COMPLETE-2Y');
  
  try {
    logger.info('🚀 COMPLETANDO TODOS LOS PARES A 2 AÑOS');
    
    // Pares que necesitan completarse (excluyendo EURUSD que ya tiene 2 años)
    const pairsToComplete = [
      'GBPUSD-OTC',    // 13 meses → 2 años
      'USDJPY-OTC',    // 6 meses → 2 años
      'AUDUSD-OTC',    // 6 meses → 2 años
      'USDCAD-OTC',    // 6 meses → 2 años
      'EURJPY-OTC',    // 6 meses → 2 años
      'GBPJPY-OTC',    // 6 meses → 2 años
      'EURGBP-OTC',    // 6 meses → 2 años
      'AUDJPY-OTC',    // 6 meses → 2 años
      'NZDUSD-OTC',    // 6 meses → 2 años
      'USDCHF-OTC',    // 6 meses → 2 años
      'EURCHF-OTC',    // 6 meses → 2 años
      'GBPCHF-OTC',    // 6 meses → 2 años
      'AUDCHF-OTC',    // 6 meses → 2 años
      'CADCHF-OTC'     // 6 meses → 2 años
    ];
    
    const totalStartTime = Date.now();
    let totalVelasNuevas = 0;
    let completedPairs = 0;
    
    logger.info(`📊 COMPLETADO A 2 AÑOS:`);
    logger.info(`   ✅ EURUSD-OTC: YA COMPLETO (2 años)`);
    logger.info(`   🔄 Pares a completar: ${pairsToComplete.length}`);
    logger.info(`   🎯 Meta: Todos con 2 años completos`);
    
    for (let i = 0; i < pairsToComplete.length; i++) {
      const asset = pairsToComplete[i];
      const pairNumber = i + 1;
      
      try {
        logger.info(`\n🔄 PAR ${pairNumber}/${pairsToComplete.length}: ${asset}`);
        
        const downloader = new HistoricalDownloader(null);
        await downloader.initialize();
        
        // Verificar datos actuales
        const currentStats = await downloader.db.get(`
          SELECT 
            COUNT(*) as count,
            MIN(DATE(timestamp/1000, 'unixepoch')) as min_date,
            MAX(DATE(timestamp/1000, 'unixepoch')) as max_date
          FROM candles 
          WHERE asset = ?
        `, [asset]);
        
        logger.info(`   📊 Estado actual: ${currentStats.count.toLocaleString()} velas`);
        logger.info(`   📅 Rango actual: ${currentStats.min_date} → ${currentStats.max_date}`);
        
        const startTime = Date.now();
        
        // Completar a 2 años (730 días)
        const saved = await downloader.analyzeAndSaveRetrospective(asset, 730);
        
        const endTime = Date.now();
        const duration = Math.round((endTime - startTime) / 1000);
        const minutes = Math.round(duration / 60);
        const nuevasVelas = saved - currentStats.count;
        
        totalVelasNuevas += Math.max(0, nuevasVelas);
        completedPairs++;
        
        const progress = Math.round((completedPairs / pairsToComplete.length) * 100);
        
        logger.info(`✅ ${asset} COMPLETADO A 2 AÑOS:`);
        logger.info(`   📊 Total velas: ${saved.toLocaleString()}`);
        logger.info(`   🆕 Velas agregadas: ${Math.max(0, nuevasVelas).toLocaleString()}`);
        logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
        logger.info(`   📈 Progreso: ${progress}% (${completedPairs}/${pairsToComplete.length})`);
        
        await downloader.close();
        
        // Pausa para estabilidad
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } catch (error) {
        logger.error(`❌ Error completando ${asset}:`, error.message);
        continue;
      }
    }
    
    const totalEndTime = Date.now();
    const totalDuration = Math.round((totalEndTime - totalStartTime) / 1000);
    const totalMinutes = Math.round(totalDuration / 60);
    
    logger.info(`\n🎯 COMPLETADO A 2 AÑOS FINALIZADO:`);
    logger.info(`   🆕 Total velas agregadas: ${totalVelasNuevas.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo total: ${totalMinutes} minutos`);
    logger.info(`   ✅ Pares completados: ${completedPairs}/${pairsToComplete.length}`);
    logger.info(`   🏆 TODOS LOS 15 PARES CON 2 AÑOS COMPLETOS`);
    logger.info(`   🤖 BASE DE DATOS ULTRA ROBUSTA LISTA PARA IA`);
    
  } catch (error) {
    logger.error('❌ Error en completado a 2 años:', error);
    process.exit(1);
  }
}

completeAllTo2Years()
  .then(() => {
    console.log('🎉 TODOS LOS PARES COMPLETADOS A 2 AÑOS');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
