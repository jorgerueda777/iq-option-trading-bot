const IQOptionOTC = require('../src/connectors/iqOptionOTC');
const HistoricalDownloader = require('../src/utils/historicalDownloader');
const Logger = require('../src/utils/logger');

async function downloadAllHistory() {
  const logger = new Logger('DownloadScript');
  
  try {
    logger.info('🚀 INICIANDO DESCARGA MASIVA DE DATOS HISTÓRICOS');
    
    // Conectar a IQ Option
    const iqConnector = new IQOptionOTC();
    await iqConnector.connect();
    
    // Inicializar descargador
    const downloader = new HistoricalDownloader(iqConnector);
    await downloader.initialize();
    
    // Assets a descargar
    const assets = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC'];
    const monthsToDownload = 12; // 1 año completo
    
    logger.info(`📊 Descargando ${monthsToDownload} meses de datos para ${assets.length} activos`);
    
    // Descargar cada activo
    for (const asset of assets) {
      logger.info(`\n🎯 === DESCARGANDO ${asset} ===`);
      
      try {
        const downloaded = await downloader.downloadHistoricalData(asset, monthsToDownload);
        logger.info(`✅ ${asset} completado: ${downloaded.toLocaleString()} velas`);
        
      } catch (error) {
        logger.error(`❌ Error descargando ${asset}:`, error.message);
      }
      
      // Pausa entre activos
      logger.info('⏸️ Pausa de 5 segundos antes del siguiente activo...');
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
    
    // Mostrar estadísticas finales
    logger.info('\n📊 === ESTADÍSTICAS FINALES ===');
    const stats = await downloader.getStats();
    
    stats.forEach(stat => {
      logger.info(`📈 ${stat.asset}:`);
      logger.info(`   📊 Velas: ${stat.total_candles.toLocaleString()}`);
      logger.info(`   📅 Período: ${stat.oldest_date} → ${stat.newest_date}`);
      logger.info(`   🗓️ Meses cubiertos: ${stat.months_covered}`);
    });
    
    // Cerrar conexiones
    await downloader.close();
    await iqConnector.disconnect();
    
    logger.info('\n🎉 ¡DESCARGA MASIVA COMPLETADA EXITOSAMENTE!');
    logger.info('💡 Ahora el bot puede usar consultas instantáneas a la base de datos local');
    
  } catch (error) {
    logger.error('❌ Error en descarga masiva:', error);
    process.exit(1);
  }
}

// Ejecutar si es llamado directamente
if (require.main === module) {
  downloadAllHistory()
    .then(() => {
      console.log('\n✅ Script completado');
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ Script falló:', error);
      process.exit(1);
    });
}

module.exports = downloadAllHistory;
