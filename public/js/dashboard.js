class Dashboard {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.predictions = [];
        this.results = [];
        this.stats = {
            predictionsToday: 0,
            accuracy: 0,
            activeAssets: 0,
            uptime: 0
        };
        this.marketData = new Map();
        this.startTime = Date.now();
        
        this.init();
    }

    init() {
        this.connectSocket();
        this.setupEventListeners();
        this.startUpdateTimer();
        this.updateConnectionStatus(false);
    }

    connectSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                this.isConnected = true;
                this.updateConnectionStatus(true);
                this.showNotification('Conectado al servidor', 'success');
            });

            this.socket.on('disconnect', () => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.showNotification('Desconectado del servidor', 'error');
            });

            this.socket.on('scanner_started', () => {
                this.updateScannerStatus(true);
                this.showNotification('Scanner iniciado', 'success');
            });

            this.socket.on('scanner_stopped', () => {
                this.updateScannerStatus(false);
                this.showNotification('Scanner detenido', 'warning');
            });

            this.socket.on('new_prediction', (prediction) => {
                this.handleNewPrediction(prediction);
            });

            this.socket.on('new_candle', (candleData) => {
                this.handleNewCandle(candleData);
            });

            this.socket.on('new_quote', (quoteData) => {
                this.handleNewQuote(quoteData);
            });

            this.socket.on('prediction_result', (result) => {
                this.handlePredictionResult(result);
            });

            this.socket.on('stats_update', (stats) => {
                this.updateStats(stats);
            });

        } catch (error) {
            console.error('Error conectando socket:', error);
            this.showNotification('Error de conexión', 'error');
        }
    }

    setupEventListeners() {
        // Start Scanner Button
        document.getElementById('start-scanner').addEventListener('click', () => {
            this.startScanner();
        });

        // Stop Scanner Button
        document.getElementById('stop-scanner').addEventListener('click', () => {
            this.stopScanner();
        });

        // Refresh Page on Connection Lost
        window.addEventListener('beforeunload', () => {
            if (this.socket) {
                this.socket.disconnect();
            }
        });
    }

    async startScanner() {
        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Scanner iniciado exitosamente', 'success');
            } else {
                this.showNotification('Error iniciando scanner: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Error starting scanner:', error);
            this.showNotification('Error de comunicación', 'error');
        }
    }

    async stopScanner() {
        try {
            const response = await fetch('/api/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Scanner detenido', 'warning');
            } else {
                this.showNotification('Error deteniendo scanner', 'error');
            }
        } catch (error) {
            console.error('Error stopping scanner:', error);
            this.showNotification('Error de comunicación', 'error');
        }
    }

    handleNewPrediction(prediction) {
        // NUEVA LÓGICA: Solo una predicción por minuto por asset
        const now = new Date();
        const currentMinute = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
        const predictionKey = `${prediction.asset}_${currentMinute}`;
        
        // Verificar si ya tenemos una predicción para este asset en este minuto
        const existingIndex = this.predictions.findIndex(p => 
            p.asset === prediction.asset && 
            p.currentTime === currentMinute
        );
        
        if (existingIndex !== -1) {
            // Ya existe una predicción para este asset en este minuto - NO agregar
            console.log(`🚫 Predicción duplicada filtrada: ${prediction.asset} ${currentMinute}`);
            return;
        }
        
        // Agregar nueva predicción
        console.log(`✅ Nueva predicción agregada: ${prediction.asset} ${prediction.direction} ${currentMinute}`);
        this.predictions.unshift(prediction);
        
        // Keep only last 20 predictions (reducido para menos spam)
        if (this.predictions.length > 20) {
            this.predictions = this.predictions.slice(0, 20);
        }

        // Update UI
        this.renderPredictions();
        
        // Show notification with color
        const notificationColor = prediction.color === 'VERDE' ? 'success' : 'danger';
        this.showNotification(
            `🎯 PREDICCIÓN: ${prediction.asset} - ${prediction.signal} ${prediction.color} para ${prediction.nextCandleTime} (${(prediction.confidence * 100).toFixed(1)}%)`, 
            notificationColor
        );
        
        // Play sound notification
        this.playPredictionSound(prediction.signal);
    }

    handleNewCandle(candleData) {
        // Update market data
        this.marketData.set(candleData.asset, candleData);
        this.renderMarketData();
    }

    handleNewQuote(quoteData) {
        // Update real-time quotes - these move faster than candles
        const currentData = this.marketData.get(quoteData.asset) || {};
        
        // Update with real-time price
        const updatedData = {
            ...currentData,
            asset: quoteData.asset,
            close: quoteData.bid,
            timestamp: quoteData.timestamp,
            realTimePrice: true
        };
        
        this.marketData.set(quoteData.asset, updatedData);
        this.renderMarketData();
        
        // Show real-time price updates
        console.log(` PRECIO TIEMPO REAL: ${quoteData.asset} = ${quoteData.bid}`);
    }

    handlePredictionResult(result) {
        // Add to results array
        this.results.unshift(result);
        
        // Keep only last 100 results
        if (this.results.length > 100) {
            this.results = this.results.slice(0, 100);
        }

        // Update prediction in array
        const predictionIndex = this.predictions.findIndex(p => p.id === result.predictionId);
        if (predictionIndex !== -1) {
            this.predictions[predictionIndex].result = result;
        }

        // Update UI
        this.renderResults();
        this.renderPredictions();
        this.updateStats();

        // Show notification
        const resultText = result.correct ? 'CORRECTA' : 'INCORRECTA';
        const notificationType = result.correct ? 'success' : 'error';
        
        this.showNotification(
            `Resultado ${result.asset}: ${resultText}`,
            notificationType
        );
    }

    renderPredictions() {
        const container = document.getElementById('predictions-container');
        
        if (this.predictions.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                    <i class="fas fa-search text-4xl mb-4"></i>
                    <p>Esperando predicciones...</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.predictions.map(prediction => {
            const confidenceClass = prediction.confidence > 0.8 ? 'confidence-high' : 
                                   prediction.confidence > 0.6 ? 'confidence-medium' : 'confidence-low';
            
            // Determinar clase de color basada en señal
            const signalClass = prediction.signal === 'COMPRA' ? 'signal-buy' : 'signal-sell';
            const colorClass = prediction.color === 'VERDE' ? 'bg-green-600' : 'bg-red-600';
            const iconClass = prediction.signal === 'COMPRA' ? 'fa-arrow-up' : 'fa-arrow-down';
            const assetClass = this.getAssetClass(prediction.asset);

            return `
                <div class="prediction-item bg-gray-800 border-l-4 ${prediction.color === 'VERDE' ? 'border-green-500' : 'border-red-500'} p-4 rounded-lg mb-3">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <div class="text-white text-xl font-bold">${prediction.asset}</div>
                            <div class="prediction-signal px-4 py-2 rounded-lg font-bold text-lg ${prediction.color === 'VERDE' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}">
                                <i class="fas ${iconClass} mr-2"></i>
                                ${prediction.signal}
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="confidence-badge ${confidenceClass} text-lg font-bold">
                                ${(prediction.confidence * 100).toFixed(1)}%
                            </div>
                            <div class="text-xs text-gray-400">${prediction.analysisTime || this.formatTime(prediction.timestamp)}</div>
                        </div>
                    </div>
                    <div class="mt-2 text-xs text-gray-300 flex justify-between">
                        <span>Próxima vela: <strong>${prediction.nextCandleTime}</strong></span>
                        <span>Timeframe: ${prediction.timeframe || '1m'}</span>
                        ${prediction.technicalScore ? `<span>Score: ${prediction.technicalScore.toFixed(2)}</span>` : ''}
                    </div>
                    ${prediction.trends ? `
                        <div class="mt-1 text-xs text-blue-400">
                            Tendencia: ${prediction.trends.direction} (${(prediction.trends.strength * 100).toFixed(0)}%)
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    renderMarketData() {
        const container = document.getElementById('market-data');
        
        if (this.marketData.size === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-400 py-4">
                    <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                    <p class="text-sm">Cargando datos...</p>
                </div>
            `;
            return;
        }

        container.innerHTML = Array.from(this.marketData.entries()).map(([asset, data]) => {
            const change = data.open ? ((data.close - data.open) / data.open * 100) : 0;
            const changeClass = change > 0 ? 'price-up' : change < 0 ? 'price-down' : 'price-neutral';
            const changeIcon = change > 0 ? 'fa-arrow-up' : change < 0 ? 'fa-arrow-down' : 'fa-minus';
            const assetClass = this.getAssetClass(asset);
            const isRealTime = data.realTimePrice;

            return `
                <div class="market-item ${isRealTime ? 'glow-blue' : ''}">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="asset-badge ${assetClass}">${asset}</div>
                            <div class="text-lg font-bold ${isRealTime ? 'text-blue-400' : ''}">${data.close.toFixed(5)}</div>
                            ${isRealTime ? '<div class="text-xs text-blue-400">⚡ TIEMPO REAL</div>' : ''}
                        </div>
                        <div class="text-right">
                            <div class="flex items-center ${changeClass}">
                                <i class="fas ${changeIcon} mr-1"></i>
                                <span class="font-semibold">${change.toFixed(2)}%</span>
                            </div>
                            <div class="text-xs text-gray-400">${this.formatTime(data.timestamp)}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderResults() {
        const tbody = document.getElementById('results-table');
        
        if (this.results.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-gray-400 py-8">
                        <i class="fas fa-inbox text-3xl mb-2"></i>
                        <p>No hay resultados aún</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.results.slice(0, 20).map(result => {
            const resultClass = result.correct ? 'result-correct' : 'result-incorrect';
            const resultIcon = result.correct ? 'fa-check-circle' : 'fa-times-circle';
            const assetClass = this.getAssetClass(result.asset);
            
            return `
                <tr class="result-row border-b border-gray-700">
                    <td class="py-3 px-4">
                        <span class="time-badge">${this.formatTime(Date.now())}</span>
                    </td>
                    <td class="py-3 px-4">
                        <span class="asset-badge ${assetClass}">${result.asset}</span>
                    </td>
                    <td class="py-3 px-4">
                        <span class="font-semibold ${result.predicted === 'CALL' ? 'text-green-400' : 'text-red-400'}">
                            ${result.predicted}
                        </span>
                    </td>
                    <td class="py-3 px-4">
                        <span class="font-semibold ${result.actual === 'CALL' ? 'text-green-400' : 'text-red-400'}">
                            ${result.actual}
                        </span>
                    </td>
                    <td class="py-3 px-4">
                        <span class="text-yellow-400">${(result.confidence * 100).toFixed(1)}%</span>
                    </td>
                    <td class="py-3 px-4">
                        <div class="flex items-center ${resultClass}">
                            <i class="fas ${resultIcon} mr-2"></i>
                            <span class="font-semibold">${result.correct ? 'CORRECTO' : 'INCORRECTO'}</span>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    renderHourlyPerformance() {
        const container = document.getElementById('hourly-performance');
        
        if (!this.stats.aiStats || !this.stats.aiStats.byHour) {
            container.innerHTML = '<div class="text-gray-400 text-sm">No hay datos disponibles</div>';
            return;
        }

        const hourlyData = this.stats.aiStats.byHour;
        const hours = Object.keys(hourlyData).sort((a, b) => parseInt(a) - parseInt(b));
        
        container.innerHTML = hours.map(hour => {
            const accuracy = hourlyData[hour];
            const accuracyLevel = accuracy >= 70 ? 'high' : accuracy >= 50 ? 'medium' : 'low';
            
            return `
                <div class="flex items-center justify-between py-2">
                    <span class="text-sm text-gray-400">${hour}:00</span>
                    <div class="flex items-center space-x-2">
                        <div class="performance-bar w-16">
                            <div class="performance-fill confidence-${accuracyLevel}" 
                                 style="width: ${accuracy}%"></div>
                        </div>
                        <span class="text-sm font-semibold w-12">${accuracy.toFixed(0)}%</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateStats(newStats = null) {
        if (newStats) {
            this.stats = { ...this.stats, ...newStats };
        }

        // Update stats cards
        document.getElementById('predictions-today').textContent = this.stats.predictionsToday || 0;
        document.getElementById('overall-accuracy').textContent = `${(this.stats.accuracy || 0).toFixed(1)}%`;
        document.getElementById('active-assets').textContent = this.stats.activeAssets?.length || 0;
        
        // Update AI status
        if (this.stats.aiStats) {
            document.getElementById('avg-confidence').textContent = `${(this.stats.aiStats.overall || 0).toFixed(1)}%`;
        }

        // Update hourly performance
        this.renderHourlyPerformance();
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        const dot = statusElement.querySelector('div');
        const text = statusElement.querySelector('span');
        
        if (connected) {
            dot.className = 'w-3 h-3 rounded-full bg-green-500 mr-2';
            text.textContent = 'Conectado';
        } else {
            dot.className = 'w-3 h-3 rounded-full bg-red-500 mr-2';
            text.textContent = 'Desconectado';
        }
    }

    updateScannerStatus(running) {
        const startBtn = document.getElementById('start-scanner');
        const stopBtn = document.getElementById('stop-scanner');
        
        if (running) {
            startBtn.disabled = true;
            startBtn.classList.add('opacity-50', 'cursor-not-allowed');
            stopBtn.disabled = false;
            stopBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            startBtn.disabled = false;
            startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            stopBtn.disabled = true;
            stopBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }

    startUpdateTimer() {
        setInterval(() => {
            this.updateUptime();
        }, 1000);
    }

    updateUptime() {
        const uptime = Date.now() - this.startTime;
        const hours = Math.floor(uptime / (1000 * 60 * 60));
        const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((uptime % (1000 * 60)) / 1000);
        
        document.getElementById('uptime').textContent = 
            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        const text = document.getElementById('notification-text');
        
        // Remove existing classes
        notification.className = notification.className.replace(/notification-\w+/g, '');
        
        // Add new type class
        notification.classList.add(`notification-${type}`);
        
        text.textContent = message;
        
        // Show notification
        notification.classList.remove('translate-x-full');
        
        // Hide after 3 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
        }, 3000);
    }

    playNotificationSound() {
        // Create audio context for notification sound
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (error) {
            // Audio not supported or blocked
        }
    }

    // Utility functions
    getTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / (1000 * 60));
        const seconds = Math.floor(diff / 1000);
        
        if (minutes > 0) {
            return `hace ${minutes}m`;
        } else {
            return `hace ${seconds}s`;
        }
    }

    getConfidenceLevel(confidence) {
        if (confidence >= 0.7) return 'high';
        if (confidence >= 0.5) return 'medium';
        return 'low';
    }

    getAssetClass(asset) {
        if (asset.includes('EUR')) return 'asset-eur';
        if (asset.includes('GBP')) return 'asset-gbp';
        if (asset.includes('USD')) return 'asset-usd';
        if (asset.includes('JPY')) return 'asset-jpy';
        if (asset.includes('AUD')) return 'asset-aud';
        if (asset.includes('CAD')) return 'asset-cad';
        return 'asset-eur';
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
