// Cargar variables de entorno
require('dotenv').config();

const IQOptionAPI = require('../src/iqoption/iqOptionAPI');
const Logger = require('../src/utils/logger');

async function testConnection() {
  const logger = new Logger('TestIQ');
  
  try {
    logger.info('🧪 PROBANDO CONEXIÓN CON IQ OPTION');
    
    const api = new IQOptionAPI();
    
    // Inicializar conexión
    await api.initialize();
    
    // Obtener información de la cuenta
    const balance = await api.getBalance();
    const assets = await api.getAvailableAssets();
    
    logger.info('✅ CONEXIÓN EXITOSA:');
    logger.info(`   💰 Balance: $${balance}`);
    logger.info(`   🎯 Tipo de cuenta: ${process.env.IQ_ACCOUNT_TYPE || 'PRACTICE'}`);
    logger.info(`   📈 Assets disponibles: ${assets.length}`);
    
    // Probar obtener precio actual
    logger.info('\n🔍 Probando obtención de precios...');
    const testAssets = ['EURUSD-OTC', 'GBPUSD-OTC'];
    
    for (const asset of testAssets) {
      try {
        const price = await api.getCurrentPrice(asset);
        const isOpen = await api.isAssetOpen(asset);
        logger.info(`   📊 ${asset}: $${price} (${isOpen ? 'ABIERTO' : 'CERRADO'})`);
      } catch (error) {
        logger.warn(`   ⚠️ ${asset}: Error obteniendo precio`);
      }
    }
    
    logger.info('\n🎉 PRUEBA COMPLETADA - IQ Option listo para el bot');
    
    await api.close();
    
  } catch (error) {
    logger.error('❌ Error de conexión:', error.message);
    logger.info('💡 Posibles soluciones:');
    logger.info('   1. Verifica tus credenciales en el archivo .env');
    logger.info('   2. Asegúrate de que tu cuenta IQ Option esté activa');
    logger.info('   3. Verifica tu conexión a internet');
  }
}

testConnection()
  .then(() => {
    console.log('✅ Prueba completada');
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
