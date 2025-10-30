const HistoricalDownloader = require('./src/utils/historicalDownloader');
const IQOptionOTCConnector = require('./src/connectors/iqOptionOTC');
const Logger = require('./src/utils/logger');

async function checkData() {
  const logger = new Logger('DataChecker');
  const iqConnector = new IQOptionOTCConnector();
  const downloader = new HistoricalDownloader(iqConnector);
  
  const assets = [
    'EURUSD-OTC',
    'GBPUSD-OTC', 
    'EURJPY-OTC',
    'EURGBP-OTC',
    'USDCHF-OTC',
    'AUDCAD-OTC'
  ];
  
  try {
    await downloader.initialize();
    logger.info('📊 ESTADO ACTUAL DE DATOS HISTÓRICOS:');
    
    let totalCandles = 0;
    
    for (const asset of assets) {
      try {
        const result = await downloader.db.get(
          'SELECT COUNT(*) as count FROM candles WHERE asset = ?',
          [asset]
        );
        const count = result ? result.count : 0;
        totalCandles += count;
        
        const years = (count / (365 * 1440)).toFixed(1);
        logger.info(`📈 ${asset}: ${count.toLocaleString()} velas (~${years} años)`);
      } catch (error) {
        logger.info(`📈 ${asset}: 0 velas (error)`);
      }
    }
    
    logger.info(`\n🎯 TOTAL: ${totalCandles.toLocaleString()} velas históricas`);
    logger.info(`📅 Equivalente a ~${(totalCandles / (365 * 1440)).toFixed(1)} años de datos por asset`);
    
  } catch (error) {
    logger.error('❌ Error verificando datos:', error);
  } finally {
    process.exit(0);
  }
}

checkData();
