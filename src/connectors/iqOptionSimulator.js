const Logger = require('../utils/logger');

class IQOptionSimulator {
  constructor() {
    this.logger = new Logger('IQOptionSimulator');
    this.connected = true;
    this.balance = 10000; // $10,000 demo
    this.operations = new Map();
    this.operationCounter = 1;
  }

  async connect() {
    this.logger.info('🎮 MODO SIMULACIÓN: Conectado a IQ Option Demo');
    this.logger.info(`💰 Balance inicial: $${this.balance}`);
    return true;
  }

  async buyOption(asset, amount, direction, duration) {
    try {
      const operationId = `SIM_${this.operationCounter++}_${Date.now()}`;
      
      // Simular tiempo de respuesta real
      await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200));
      
      // Verificar balance
      if (this.balance < amount) {
        this.logger.error(`❌ Balance insuficiente: $${this.balance} < $${amount}`);
        return { success: false, message: 'Balance insuficiente' };
      }

      // Descontar del balance
      this.balance -= amount;

      // Crear operación
      const operation = {
        id: operationId,
        asset: asset,
        amount: amount,
        direction: direction,
        duration: duration,
        startTime: Date.now(),
        endTime: Date.now() + (duration * 1000),
        status: 'active',
        payout: 0.85 // 85% payout
      };

      this.operations.set(operationId, operation);

      this.logger.info(`✅ OPERACIÓN SIMULADA EJECUTADA: ${asset} ${direction} $${amount}`);
      this.logger.info(`📊 ID: ${operationId} | Balance restante: $${this.balance.toFixed(2)}`);

      // Programar resultado automático
      setTimeout(() => {
        this.resolveOperation(operationId);
      }, duration * 1000);

      return {
        success: true,
        operationId: operationId,
        id: operationId,
        message: `Operación simulada ejecutada: ${asset} ${direction} $${amount}`
      };

    } catch (error) {
      this.logger.error('❌ Error en simulación:', error.message);
      return { success: false, message: error.message };
    }
  }

  resolveOperation(operationId) {
    const operation = this.operations.get(operationId);
    if (!operation) return;

    // Simular resultado (60% probabilidad de ganar)
    const won = Math.random() > 0.4;
    
    operation.status = won ? 'won' : 'lost';
    operation.result = won ? 'win' : 'loss';

    if (won) {
      const profit = operation.amount * operation.payout;
      const total = operation.amount + profit;
      this.balance += total;
      
      this.logger.info(`🎉 OPERACIÓN GANADA: ${operation.asset} | +$${profit.toFixed(2)} | Balance: $${this.balance.toFixed(2)}`);
    } else {
      this.logger.info(`❌ OPERACIÓN PERDIDA: ${operation.asset} | -$${operation.amount} | Balance: $${this.balance.toFixed(2)}`);
    }

    this.operations.set(operationId, operation);
  }

  async checkResult(operationId) {
    const operation = this.operations.get(operationId);
    if (!operation) {
      return { success: false, message: 'Operación no encontrada' };
    }

    return {
      success: true,
      result: operation.result || 'pending',
      operation: operation
    };
  }

  isConnectionActive() {
    return this.connected;
  }

  getBalance() {
    return this.balance;
  }

  getActiveOperations() {
    const active = [];
    for (const [id, op] of this.operations) {
      if (op.status === 'active') {
        active.push(op);
      }
    }
    return active;
  }

  getOperationHistory() {
    return Array.from(this.operations.values());
  }
}

module.exports = IQOptionSimulator;
