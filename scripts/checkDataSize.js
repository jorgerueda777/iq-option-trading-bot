const sqlite3 = require('sqlite3').verbose();
const { open } = require('sqlite');
const Logger = require('../src/utils/logger');

async function checkDataSize() {
  const logger = new Logger('CheckSize');
  
  try {
    logger.info('📊 VERIFICANDO TAMAÑO DE DATOS POR PAR');
    
    const db = await open({
      filename: './data/historical.db',
      driver: sqlite3.Database
    });
    
    const allAssets = [
      'EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'USDCAD-OTC',
      'EURJPY-OTC', 'GBPJPY-OTC', 'EURGBP-OTC', 'AUDJPY-OTC', 'NZDUSD-OTC',
      'USDCHF-OTC', 'EURCHF-OTC', 'GBPCHF-OTC', 'AUDCHF-OTC', 'CADCHF-OTC'
    ];
    
    let totalVelas = 0;
    
    for (const asset of allAssets) {
      const result = await db.get(`
        SELECT 
          COUNT(*) as total_velas,
          MIN(DATE(timestamp/1000, 'unixepoch')) as fecha_inicio,
          MAX(DATE(timestamp/1000, 'unixepoch')) as fecha_fin
        FROM candles 
        WHERE asset = ?
      `, [asset]);
      
      const velas = result.total_velas;
      const dias = Math.round(velas / 1440);
      const meses = Math.round(dias / 30);
      
      totalVelas += velas;
      
      logger.info(`📈 ${asset}:`);
      logger.info(`   🔢 Velas: ${velas.toLocaleString()}`);
      logger.info(`   📅 Período: ${result.fecha_inicio} → ${result.fecha_fin}`);
      logger.info(`   📊 Cobertura: ${dias} días (${meses} meses)`);
      logger.info('');
    }
    
    logger.info(`🎯 TOTAL GENERAL:`);
    logger.info(`   📊 Total velas: ${totalVelas.toLocaleString()}`);
    logger.info(`   📈 Promedio por par: ${Math.round(totalVelas/allAssets.length).toLocaleString()}`);
    logger.info(`   💾 Base de datos: ${(totalVelas * 15 * 8 / 1024 / 1024).toFixed(1)} MB estimados`);
    
    await db.close();
    
  } catch (error) {
    logger.error('❌ Error:', error);
  }
}

checkDataSize()
  .then(() => {
    console.log('✅ Verificación completada');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
