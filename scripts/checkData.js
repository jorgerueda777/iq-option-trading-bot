const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function checkData() {
  const logger = new Logger('CheckData');
  
  try {
    logger.info('🔍 VERIFICANDO DATOS EN BASE DE DATOS');
    
    const downloader = new HistoricalDownloader(null);
    await downloader.initialize();
    
    // Mostrar estadísticas
    const stats = await downloader.getStats();
    
    if (stats.length === 0) {
      logger.info('❌ No hay datos en la base de datos');
    } else {
      logger.info(`📊 DATOS ENCONTRADOS:`);
      stats.forEach(stat => {
        logger.info(`📈 ${stat.asset}: ${stat.total_candles.toLocaleString()} velas`);
        logger.info(`   📅 Rango: ${stat.oldest_date} → ${stat.newest_date}`);
        logger.info(`   🗓️ Cobertura: ${stat.days_covered} días (${stat.months_covered} meses)`);
        logger.info('');
      });
    }
    
    await downloader.close();
    
  } catch (error) {
    logger.error('❌ Error verificando datos:', error);
  }
}

checkData()
  .then(() => {
    console.log('✅ Verificación completada');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
