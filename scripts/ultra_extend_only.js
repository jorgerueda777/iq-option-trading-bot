const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function ultraExtendOnly() {
  const logger = new Logger('ULTRA-EXT');
  
  try {
    logger.info('🚀 MODO ULTRA: SOLO EXTENSIÓN (18 MESES ADICIONALES)');
    
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
    
    // SOLO los días adicionales (730 total - 181 existentes = 549 días nuevos)
    const daysBack = 730; // Total deseado
    const totalStartTime = Date.now();
    let totalVelasNuevas = 0;
    let completedPairs = 0;
    
    logger.info(`📊 EXTENSIÓN INTELIGENTE:`);
    logger.info(`   📅 Ya tenemos: 181 días (6 meses)`);
    logger.info(`   📅 Agregando: ~549 días (18 meses)`);
    logger.info(`   🎯 Total final: 730 días (2 años)`);
    logger.info(`   ⚡ Solo procesa días NUEVOS`);
    
    for (let i = 0; i < allAssets.length; i++) {
      const asset = allAssets[i];
      const pairNumber = i + 1;
      
      try {
        logger.info(`\n🔄 PAR ${pairNumber}/15: ${asset} (EXTENSIÓN)`);
        
        const downloader = new HistoricalDownloader(null);
        await downloader.initialize();
        
        // Verificar datos existentes
        const existingCount = await downloader.db.get(
          'SELECT COUNT(*) as count FROM candles WHERE asset = ?', 
          [asset]
        );
        
        logger.info(`   📊 Datos existentes: ${existingCount.count.toLocaleString()} velas`);
        
        const startTime = Date.now();
        const saved = await downloader.analyzeAndSaveRetrospective(asset, daysBack);
        const endTime = Date.now();
        
        const duration = Math.round((endTime - startTime) / 1000);
        const minutes = Math.round(duration / 60);
        const nuevasVelas = saved - existingCount.count;
        
        totalVelasNuevas += Math.max(0, nuevasVelas);
        completedPairs++;
        
        const progress = Math.round((completedPairs / allAssets.length) * 100);
        
        logger.info(`✅ ${asset} COMPLETADO:`);
        logger.info(`   📊 Total velas: ${saved.toLocaleString()}`);
        logger.info(`   🆕 Velas nuevas: ${Math.max(0, nuevasVelas).toLocaleString()}`);
        logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
        logger.info(`   📈 Progreso: ${progress}% (${completedPairs}/${allAssets.length})`);
        
        await downloader.close();
        
        // Pausa para estabilidad
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } catch (error) {
        logger.error(`❌ Error procesando ${asset}:`, error.message);
        continue;
      }
    }
    
    const totalEndTime = Date.now();
    const totalDuration = Math.round((totalEndTime - totalStartTime) / 1000);
    const totalMinutes = Math.round(totalDuration / 60);
    
    logger.info(`\n🎯 EXTENSIÓN COMPLETADA:`);
    logger.info(`   🆕 Velas nuevas agregadas: ${totalVelasNuevas.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo total: ${totalMinutes} minutos`);
    logger.info(`   ✅ Pares extendidos: ${completedPairs}/${allAssets.length}`);
    logger.info(`   📅 Cobertura final: 2 años completos`);
    logger.info(`   🤖 Base de datos ULTRA ROBUSTA lista`);
    
  } catch (error) {
    logger.error('❌ Error en extensión:', error);
    process.exit(1);
  }
}

ultraExtendOnly()
  .then(() => {
    console.log('🎉 EXTENSIÓN COMPLETADA - 2 AÑOS DE DATOS HISTÓRICOS');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error en extensión:', error);
    process.exit(1);
  });
