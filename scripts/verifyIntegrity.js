const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function verifyIntegrity() {
  const logger = new Logger('Verify');
  
  try {
    logger.info('🔍 VERIFICANDO INTEGRIDAD DE DATOS');
    
    const downloader = new HistoricalDownloader(null);
    await downloader.initialize();
    
    const asset = 'EURUSD-OTC';
    
    // Obtener rango de fechas
    const rangeQuery = await downloader.db.get(`
      SELECT 
        MIN(DATE(timestamp/1000, 'unixepoch')) as min_date,
        MAX(DATE(timestamp/1000, 'unixepoch')) as max_date,
        COUNT(*) as total_candles
      FROM candles 
      WHERE asset = ?
    `, [asset]);
    
    logger.info(`📊 ${asset}:`);
    logger.info(`   📅 Rango: ${rangeQuery.min_date} → ${rangeQuery.max_date}`);
    logger.info(`   📈 Total velas: ${rangeQuery.total_candles.toLocaleString()}`);
    
    // Verificar días con velas faltantes
    const dailyCount = await downloader.db.all(`
      SELECT 
        DATE(timestamp/1000, 'unixepoch') as date,
        COUNT(*) as candles_count
      FROM candles 
      WHERE asset = ?
      GROUP BY DATE(timestamp/1000, 'unixepoch')
      HAVING candles_count < 1440
      ORDER BY date
      LIMIT 10
    `, [asset]);
    
    if (dailyCount.length > 0) {
      logger.warn(`⚠️ Días con velas faltantes:`);
      dailyCount.forEach(day => {
        const missing = 1440 - day.candles_count;
        logger.warn(`   ${day.date}: ${day.candles_count}/1440 velas (faltan ${missing})`);
      });
    } else {
      logger.info(`✅ Todos los días tienen 1440 velas completas`);
    }
    
    // Calcular días totales
    const startDate = new Date(rangeQuery.min_date);
    const endDate = new Date(rangeQuery.max_date);
    const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
    const expectedVelas = daysDiff * 1440;
    const missing = expectedVelas - rangeQuery.total_candles;
    
    logger.info(`\n📊 RESUMEN:`);
    logger.info(`   📅 Días cubiertos: ${daysDiff} días`);
    logger.info(`   🎯 Velas esperadas: ${expectedVelas.toLocaleString()}`);
    logger.info(`   📈 Velas reales: ${rangeQuery.total_candles.toLocaleString()}`);
    logger.info(`   ❌ Velas faltantes: ${missing.toLocaleString()}`);
    logger.info(`   📊 Completitud: ${((rangeQuery.total_candles/expectedVelas)*100).toFixed(2)}%`);
    
    await downloader.close();
    
  } catch (error) {
    logger.error('❌ Error verificando integridad:', error);
  }
}

verifyIntegrity()
  .then(() => {
    console.log('✅ Verificación completada');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
