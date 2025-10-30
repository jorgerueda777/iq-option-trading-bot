const readline = require('readline');
const fs = require('fs');
const Logger = require('../src/utils/logger');

async function setupIQOption() {
  const logger = new Logger('Setup');
  
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const question = (prompt) => {
    return new Promise((resolve) => {
      rl.question(prompt, resolve);
    });
  };

  try {
    logger.info('🔧 CONFIGURACIÓN DE IQ OPTION');
    logger.info('Este asistente te ayudará a configurar las credenciales de IQ Option');
    
    console.log('\n📧 Ingresa tus credenciales de IQ Option:');
    
    const email = await question('Email: ');
    const password = await question('Password: ');
    
    console.log('\n⚙️ Configuración de cuenta:');
    console.log('1. PRACTICE (Cuenta demo - Recomendado para pruebas)');
    console.log('2. REAL (Cuenta real - Solo para trading real)');
    
    const accountChoice = await question('Selecciona tipo de cuenta (1 o 2): ');
    const accountType = accountChoice === '2' ? 'REAL' : 'PRACTICE';
    
    // Crear archivo .env
    const envContent = `# Configuración de IQ Option
IQ_EMAIL=${email}
IQ_PASSWORD=${password}
IQ_ACCOUNT_TYPE=${accountType}

# Configuración de seguridad
IQ_MAX_DAILY_LOSS=50
IQ_MAX_OPERATIONS_PER_DAY=20
`;

    fs.writeFileSync('.env', envContent);
    
    logger.info('✅ Configuración guardada en .env');
    logger.info(`📊 Tipo de cuenta: ${accountType}`);
    
    // Probar conexión
    console.log('\n🧪 ¿Quieres probar la conexión ahora? (y/n): ');
    const testConnection = await question('');
    
    if (testConnection.toLowerCase() === 'y') {
      logger.info('🔌 Probando conexión...');
      
      // Cargar variables de entorno
      require('dotenv').config();
      
      const IQOptionAPI = require('../src/iqoption/iqOptionAPI');
      const api = new IQOptionAPI();
      
      try {
        await api.initialize();
        const balance = await api.getBalance();
        
        logger.info('✅ ¡Conexión exitosa!');
        logger.info(`💰 Balance: $${balance}`);
        logger.info(`🎯 Cuenta: ${accountType}`);
        
        await api.close();
      } catch (error) {
        logger.error('❌ Error de conexión:', error.message);
        logger.info('💡 Verifica tus credenciales y vuelve a intentar');
      }
    }
    
    logger.info('\n🎉 Configuración completada');
    logger.info('💡 Ahora puedes ejecutar el bot con: node scripts/runAutoBot.js');
    
  } catch (error) {
    logger.error('❌ Error en configuración:', error);
  } finally {
    rl.close();
  }
}

setupIQOption();
