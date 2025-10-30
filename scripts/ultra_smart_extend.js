const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function ultraSmartExtend() {
  const logger = new Logger('ULTRA-SMART');
  
  try {
    logger.info('🚀 MODO ULTRA INTELIGENTE: SOLO RANGO FALTANTE');
    
    const allAssets = [
      'EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'USDCAD-OTC',
      'EURJPY-OTC', 'GBPJPY-OTC', 'EURGBP-OTC', 'AUDJPY-OTC', 'NZDUSD-OTC',
      'USDCHF-OTC', 'EURCHF-OTC', 'GBPCHF-OTC', 'AUDCHF-OTC', 'CADCHF-OTC'
    ];
    
    // SOLO el rango faltante: Oct 2023 → Abr 2025 (549 días)
    const daysBack = 549; // Solo días nuevos
    const totalStartTime = Date.now();
    let totalVelasNuevas = 0;
    
    logger.info(`📊 EXTENSIÓN INTELIGENTE:`);
    logger.info(`   📅 Rango faltante: Oct 2023 → Abr 2025`);
    logger.info(`   📈 Solo días nuevos: ${daysBack} días`);
    logger.info(`   ⚡ Sin verificaciones innecesarias`);
    logger.info(`   🎯 Velocidad máxima esperada`);
    
    for (let i = 0; i < allAssets.length; i++) {
      const asset = allAssets[i];
      const pairNumber = i + 1;
      
      try {
        logger.info(`\n🔄 PAR ${pairNumber}/15: ${asset} (RANGO FALTANTE)`);
        
        const downloader = new HistoricalDownloader(null);
        await downloader.initialize();
        
        const startTime = Date.now();
        
        // Procesar solo el rango faltante con fecha específica de inicio
        const saved = await downloader.analyzeAndSaveRetrospectiveRange(
          asset, 
          new Date('2023-10-27'), // Fecha inicio
          new Date('2025-04-29')   // Fecha fin
        );
        
        const endTime = Date.now();
        const duration = Math.round((endTime - startTime) / 1000);
        const minutes = Math.round(duration / 60);
        const speed = Math.round(saved / duration);
        
        totalVelasNuevas += saved;
        const progress = Math.round((pairNumber / allAssets.length) * 100);
        
        logger.info(`✅ ${asset} COMPLETADO:`);
        logger.info(`   🆕 Velas nuevas: ${saved.toLocaleString()}`);
        logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
        logger.info(`   🔥 Velocidad: ${speed} velas/segundo`);
        logger.info(`   📈 Progreso: ${progress}%`);
        
        await downloader.close();
        await new Promise(resolve => setTimeout(resolve, 500));
        
      } catch (error) {
        logger.error(`❌ Error procesando ${asset}:`, error.message);
        continue;
      }
    }
    
    const totalEndTime = Date.now();
    const totalDuration = Math.round((totalEndTime - totalStartTime) / 1000);
    const totalMinutes = Math.round(totalDuration / 60);
    
    logger.info(`\n🎯 EXTENSIÓN INTELIGENTE COMPLETADA:`);
    logger.info(`   🆕 Total velas nuevas: ${totalVelasNuevas.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo total: ${totalMinutes} minutos`);
    logger.info(`   🔥 Velocidad promedio: ${Math.round(totalVelasNuevas/totalDuration)} velas/seg`);
    logger.info(`   📅 Cobertura final: 2 años completos`);
    
  } catch (error) {
    logger.error('❌ Error en extensión inteligente:', error);
    process.exit(1);
  }
}

ultraSmartExtend()
  .then(() => {
    console.log('🎉 EXTENSIÓN INTELIGENTE COMPLETADA');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
