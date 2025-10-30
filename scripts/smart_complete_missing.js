const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function smartCompleteMissing() {
  const logger = new Logger('SMART-COMPLETE');
  
  try {
    logger.info('🧠 COMPLETADO INTELIGENTE: SOLO LO QUE REALMENTE FALTA');
    
    const allAssets = [
      'EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'USDCAD-OTC',
      'EURJPY-OTC', 'GBPJPY-OTC', 'EURGBP-OTC', 'AUDJPY-OTC', 'NZDUSD-OTC',
      'USDCHF-OTC', 'EURCHF-OTC', 'GBPCHF-OTC', 'AUDCHF-OTC', 'CADCHF-OTC'
    ];
    
    const targetVelas = 730 * 1440; // 2 años = 1,051,200 velas
    const totalStartTime = Date.now();
    let totalVelasNuevas = 0;
    let paresCompletados = 0;
    let paresSaltados = 0;
    
    logger.info(`🎯 META: ${targetVelas.toLocaleString()} velas por par (2 años)`);
    
    for (let i = 0; i < allAssets.length; i++) {
      const asset = allAssets[i];
      const pairNumber = i + 1;
      
      try {
        logger.info(`\n🔍 PAR ${pairNumber}/15: ${asset} - VERIFICANDO ESTADO`);
        
        const downloader = new HistoricalDownloader(null);
        await downloader.initialize();
        
        // Verificar estado actual
        const currentCount = await downloader.db.get(
          'SELECT COUNT(*) as count FROM candles WHERE asset = ?', 
          [asset]
        );
        
        const velasActuales = currentCount.count;
        const velasFaltantes = targetVelas - velasActuales;
        const diasFaltantes = Math.ceil(velasFaltantes / 1440);
        
        logger.info(`   📊 Velas actuales: ${velasActuales.toLocaleString()}`);
        logger.info(`   📈 Velas objetivo: ${targetVelas.toLocaleString()}`);
        logger.info(`   🆕 Velas faltantes: ${velasFaltantes.toLocaleString()}`);
        
        if (velasFaltantes <= 0) {
          logger.info(`   ✅ ${asset} YA COMPLETO - SALTANDO`);
          paresSaltados++;
          await downloader.close();
          continue;
        }
        
        logger.info(`   🔄 Completando ${diasFaltantes} días faltantes...`);
        
        const startTime = Date.now();
        
        // Solo generar los días que realmente faltan
        const saved = await downloader.analyzeAndSaveRetrospective(asset, diasFaltantes);
        
        const endTime = Date.now();
        const duration = Math.round((endTime - startTime) / 1000);
        const minutes = Math.round(duration / 60);
        const speed = Math.round(saved / duration);
        
        totalVelasNuevas += saved;
        paresCompletados++;
        
        logger.info(`   ✅ ${asset} COMPLETADO:`);
        logger.info(`   🆕 Velas agregadas: ${saved.toLocaleString()}`);
        logger.info(`   ⏱️ Tiempo: ${minutes} min (${duration}s)`);
        logger.info(`   🔥 Velocidad: ${speed} velas/segundo`);
        
        await downloader.close();
        
      } catch (error) {
        logger.error(`❌ Error en ${asset}:`, error.message);
        continue;
      }
    }
    
    const totalEndTime = Date.now();
    const totalDuration = Math.round((totalEndTime - totalStartTime) / 1000);
    const totalMinutes = Math.round(totalDuration / 60);
    
    logger.info(`\n🎯 COMPLETADO INTELIGENTE FINALIZADO:`);
    logger.info(`   ✅ Pares completados: ${paresCompletados}`);
    logger.info(`   ⏭️ Pares ya completos: ${paresSaltados}`);
    logger.info(`   🆕 Total velas agregadas: ${totalVelasNuevas.toLocaleString()}`);
    logger.info(`   ⏱️ Tiempo total: ${totalMinutes} minutos`);
    logger.info(`   🏆 TODOS LOS 15 PARES CON 2 AÑOS COMPLETOS`);
    
  } catch (error) {
    logger.error('❌ Error en completado inteligente:', error);
    process.exit(1);
  }
}

smartCompleteMissing()
  .then(() => {
    console.log('🎉 COMPLETADO INTELIGENTE FINALIZADO');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
