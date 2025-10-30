const { spawn } = require('child_process');
const path = require('path');
const Logger = require('../utils/logger');

class IQOptionPythonBridge {
  constructor() {
    this.logger = new Logger('IQOptionPythonBridge');
    this.pythonScript = path.join(__dirname, '../../iq_option_stable_api.py');
    this.connected = false;
  }

  async connect() {
    try {
      this.logger.info('🐍 Conectando a IQ Option via Python API...');
      
      const result = await this.runPythonCommand(['connect']);
      
      if (result.success) {
        this.connected = true;
        this.logger.info('✅ Conectado a IQ Option via Python API');
        this.logger.info(`💰 Balance: $${result.balance}`);
        return true;
      } else {
        this.logger.error(`❌ Error conectando: ${result.message}`);
        return false;
      }
    } catch (error) {
      this.logger.error('❌ Error en conexión Python:', error.message);
      return false;
    }
  }

  async buyOption(asset, amount, direction, duration) {
    try {
      if (!this.connected) {
        this.logger.error('❌ No conectado a IQ Option');
        return { success: false, message: 'No conectado' };
      }

      this.logger.info(`🚀 EJECUTANDO OPERACIÓN REAL VIA PYTHON: ${asset} ${direction} $${amount}`);
      
      const result = await this.runPythonCommand([
        'buy',
        asset,
        amount.toString(),
        direction,
        duration.toString()
      ]);

      if (result.success) {
        this.logger.info(`✅ OPERACIÓN CONFIRMADA: ID ${result.operation_id}`);
        return {
          success: true,
          operationId: result.operation_id,
          message: result.message
        };
      } else {
        this.logger.error(`❌ Error ejecutando operación: ${result.message}`);
        return { success: false, message: result.message };
      }
    } catch (error) {
      this.logger.error('❌ Error en buyOption Python:', error.message);
      return { success: false, message: error.message };
    }
  }

  async executeTrade(tradeData) {
    try {
      this.logger.info(`Ejecutando trade: ${tradeData.asset} ${tradeData.direction} $${tradeData.amount}`);
      
      const result = await this.runPythonCommand([
        'buy',
        tradeData.asset,
        tradeData.amount.toString(),
        tradeData.direction,
        tradeData.duration.toString()
      ]);
      
      if (result.success) {
        this.logger.info(`OPERACION EJECUTADA: ID ${result.id || result.trade_id}`);
        return result;
      } else {
        this.logger.error(`Error ejecutando trade: ${result.message}`);
        return result;
      }
    } catch (error) {
      this.logger.error('Error en executeTrade Python:', error.message);
      return { success: false, message: error.message };
    }
  }

  async executeSimultaneousTrades() {
    try {
      this.logger.info(`🚀 EJECUTANDO 7 OPERACIONES SIMULTÁNEAS...`);
      
      // Ejecutar el script de operaciones simultáneas
      const simultaneousScript = path.join(__dirname, '../../simultaneous_7_trades.py');
      
      const result = await this.runPythonScript(simultaneousScript, []);
      
      if (result.success) {
        this.logger.info(`✅ OPERACIONES SIMULTÁNEAS EJECUTADAS`);
        return result;
      } else {
        this.logger.error(`❌ Error ejecutando operaciones simultáneas: ${result.message}`);
        return result;
      }
    } catch (error) {
      this.logger.error('❌ Error en executeSimultaneousTrades:', error.message);
      return { success: false, message: error.message };
    }
  }

  async checkResult(operationId) {
    try {
      this.logger.info(`🔍 Verificando resultado de operación ${operationId}...`);
      
      const result = await this.runPythonCommand(['check_result', operationId]);
      
      if (result.success) {
        this.logger.info(`✅ Resultado obtenido: ${result.result}`);
        return result;
      } else {
        this.logger.error(`❌ Error verificando resultado: ${result.message}`);
        return result;
      }
    } catch (error) {
      this.logger.error('❌ Error en checkResult Python:', error.message);
      return { success: false, message: error.message };
    }
  }

  runPythonCommand(args) {
    return new Promise((resolve, reject) => {
      const python = spawn('python', [this.pythonScript, ...args]);
      
      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      python.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout.trim());
            resolve(result);
          } catch (error) {
            this.logger.error(`❌ Error parsing JSON: ${stdout}`);
            reject(new Error(`Error parsing response: ${error.message}`));
          }
        } else {
          this.logger.error(`❌ Python script error: ${stderr}`);
          reject(new Error(`Python script failed with code ${code}: ${stderr}`));
        }
      });

      python.on('error', (error) => {
        this.logger.error(`❌ Error ejecutando Python: ${error.message}`);
        reject(error);
      });
    });
  }

  runPythonScript(scriptPath, args) {
    return new Promise((resolve, reject) => {
      const python = spawn('python', [scriptPath, ...args]);
      
      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
        this.logger.info(`🐍 ${data.toString().trim()}`);
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      python.on('close', (code) => {
        if (code === 0) {
          resolve({ success: true, message: 'Operaciones simultáneas completadas', output: stdout });
        } else {
          this.logger.error(`❌ Python script error: ${stderr}`);
          reject(new Error(`Python script failed with code ${code}: ${stderr}`));
        }
      });

      python.on('error', (error) => {
        this.logger.error(`❌ Error ejecutando Python: ${error.message}`);
        reject(error);
      });
    });
  }

  runPythonScriptWithJSON(scriptPath, args) {
    return new Promise((resolve, reject) => {
      const python = spawn('python', [scriptPath, ...args]);
      
      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
        this.logger.info(`🐍 ${data.toString().trim()}`);
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      python.on('close', (code) => {
        if (code === 0) {
          // INTENTAR PARSEAR JSON DEL OUTPUT
          try {
            const lines = stdout.trim().split('\n');
            const lastLine = lines[lines.length - 1];
            
            // Buscar línea que contenga JSON
            if (lastLine && (lastLine.includes('{') || lastLine.includes('success'))) {
              const result = JSON.parse(lastLine);
              resolve(result);
            } else {
              // Si no hay JSON, devolver éxito básico
              resolve({ success: true, message: 'Operaciones completadas', output: stdout });
            }
          } catch (parseError) {
            this.logger.warn(`⚠️ No se pudo parsear JSON, devolviendo éxito básico: ${parseError.message}`);
            resolve({ success: true, message: 'Operaciones completadas', output: stdout });
          }
        } else {
          this.logger.error(`❌ Python script error: ${stderr}`);
          reject(new Error(`Python script failed with code ${code}: ${stderr}`));
        }
      });

      python.on('error', (error) => {
        this.logger.error(`❌ Error ejecutando Python: ${error.message}`);
        reject(error);
      });
    });
  }

  // EJECUTAR OPERACIONES DINÁMICAS BASADAS EN SEÑALES
  async executeDynamicTrades(signals) {
    try {
      this.logger.info(`🚀 Ejecutando ${signals.length} operaciones dinámicas INVERTIDAS...`);
      this.logger.info(`📊 Señales a invertir: ${JSON.stringify(signals, null, 2)}`);
      
      const scriptPath = path.join(__dirname, '../../dynamic_trades.py');
      const signalsJson = JSON.stringify(signals);
      
      this.logger.info(`🐍 Llamando script: ${scriptPath}`);
      this.logger.info(`📋 Parámetros: ${signalsJson}`);
      
      const result = await this.runPythonScriptWithJSON(scriptPath, [signalsJson]);
      
      this.logger.info(`✅ ${signals.length} operaciones dinámicas INVERTIDAS completadas`);
      this.logger.info(`📊 Resultado: ${JSON.stringify(result)}`);
      return result;
      
    } catch (error) {
      this.logger.error('❌ Error en executeDynamicTrades:', error.message);
      return { success: false, message: error.message };
    }
  }

  isConnectionActive() {
    return this.connected;
  }
}

module.exports = IQOptionPythonBridge;
