# IQ Option AI Scanner 🤖

Bot escáner avanzado con Inteligencia Artificial para análisis y predicción de velas en IQ Option OTC. Utiliza análisis técnico profesional y machine learning para predecir la dirección de la siguiente vela basándose en patrones históricos por horas.

## 🚀 Características Principales

### 🧠 Inteligencia Artificial Avanzada
- **Red Neuronal** con TensorFlow.js para predicciones
- **Análisis de patrones históricos** por horas específicas
- **Aprendizaje continuo** con cada resultado
- **Múltiples indicadores técnicos** integrados

### 📊 Análisis Técnico Profesional
- **RSI, MACD, Bollinger Bands**
- **Medias móviles** (EMA, SMA)
- **Osciladores** (Stochastic, Williams %R)
- **Patrones de velas** (Doji, Hammer, Engulfing)
- **Análisis de volumen** y soporte/resistencia

### 🎯 Sistema de Predicción Inteligente
- **Predicciones en tiempo real** cada minuto
- **Filtros de confianza** configurables
- **Análisis temporal** por sesiones de trading
- **Cooldown automático** entre predicciones
- **Verificación automática** de resultados

### 📱 Dashboard en Tiempo Real
- **Interfaz moderna** con TailwindCSS
- **WebSocket** para actualizaciones instantáneas
- **Estadísticas detalladas** por activo y hora
- **Gráficos de rendimiento** en tiempo real
- **Notificaciones** de nuevas predicciones

## 🛠️ Instalación

### Prerrequisitos
- **Node.js** v16 o superior
- **MongoDB** (opcional, usa archivos locales como fallback)
- **Cuenta de IQ Option** para datos en tiempo real

### Pasos de Instalación

1. **Clonar el proyecto**
```bash
cd D:\iq_quot
```

2. **Instalar dependencias**
```bash
npm install
```

3. **Configurar variables de entorno**
```bash
copy .env.example .env
```

4. **Editar archivo .env**
```env
# Configuración de IQ Option
IQ_EMAIL=tu_email@ejemplo.com
IQ_PASSWORD=tu_password
IQ_PRACTICE=true

# Configuración del servidor
PORT=3000
HOST=localhost

# Base de datos (opcional)
MONGODB_URI=mongodb://localhost:27017/iq_scanner

# Logging
LOG_LEVEL=info
```

## 🚀 Uso

### Iniciar el Bot
```bash
npm start
```

### Modo Desarrollo
```bash
npm run dev
```

### Entrenar IA
```bash
npm run train
```

### Acceder al Dashboard
Abrir navegador en: `http://localhost:3000`

## 📋 Configuración Avanzada

### Activos Monitoreados
Editar en `config/config.js`:
```javascript
assets: [
  'EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC',
  'USDCAD-OTC', 'EURJPY-OTC', 'GBPJPY-OTC', 'EURGBP-OTC'
]
```

### Parámetros de IA
```javascript
ai: {
  confidence_threshold: 0.7,    // Confianza mínima (70%)
  lookbackPeriod: 100,          // Velas históricas
  epochs: 100,                  // Épocas de entrenamiento
  batchSize: 32                 // Tamaño de lote
}
```

### Límites de Predicción
```javascript
prediction: {
  confidence_threshold: 0.7,           // Umbral de confianza
  max_predictions_per_hour: 10,        // Máximo por hora
  cooldown_period: 300000              // 5 minutos entre predicciones
}
```

## 🎯 Cómo Funciona la IA

### 1. Recolección de Datos
- **Velas históricas** de IQ Option en tiempo real
- **Indicadores técnicos** calculados automáticamente
- **Patrones de velas** identificados
- **Contexto temporal** (hora, sesión de trading)

### 2. Análisis de Patrones
- **Análisis por horas específicas** para detectar patrones recurrentes
- **Correlación** entre indicadores técnicos
- **Identificación** de condiciones de mercado similares
- **Peso histórico** de precisión por hora

### 3. Predicción
- **Red neuronal** procesa todas las características
- **Probabilidades** de CALL vs PUT
- **Filtros de confianza** para evitar predicciones débiles
- **Validación** con análisis técnico

### 4. Aprendizaje Continuo
- **Verificación automática** de resultados
- **Reentrenamiento** cada 24 horas
- **Ajuste de pesos** según precisión histórica
- **Optimización** de parámetros

## 📊 Indicadores Utilizados

### Tendencia
- **RSI (14)** - Sobrecompra/sobreventa
- **MACD (12,26,9)** - Momentum y señales
- **Bollinger Bands (20,2)** - Volatilidad

### Medias Móviles
- **EMA 12, 26, 50** - Tendencias cortas
- **SMA 20, 50, 100** - Tendencias medias/largas

### Osciladores
- **Stochastic (14,3)** - Momentum
- **Williams %R (14)** - Sobrecompra/sobreventa

### Patrones de Velas
- **Doji** - Indecisión del mercado
- **Hammer** - Reversión alcista
- **Shooting Star** - Reversión bajista
- **Engulfing** - Confirmación de tendencia

## 🔧 API Endpoints

### Estado del Scanner
```http
GET /api/status
```

### Obtener Predicciones
```http
GET /api/predictions
```

### Iniciar Scanner
```http
POST /api/start
```

### Detener Scanner
```http
POST /api/stop
```

## 📈 Estadísticas y Métricas

### Precisión General
- **Accuracy total** de todas las predicciones
- **Precisión por activo** individual
- **Precisión por hora** del día
- **Confianza promedio** de predicciones

### Rendimiento
- **Predicciones por día**
- **Tiempo de respuesta** promedio
- **Uptime** del sistema
- **Activos monitoreados** activamente

## 🚨 Consideraciones Importantes

### ⚠️ Aspectos Legales
- **Revisar términos de servicio** de IQ Option
- **Uso responsable** de la API
- **No garantía** de ganancias
- **Riesgo financiero** inherente al trading

### 🔒 Seguridad
- **No hardcodear** credenciales
- **Usar variables de entorno**
- **Conexiones seguras** (HTTPS/WSS)
- **Validación** de datos de entrada

### 📊 Limitaciones
- **Mercado impredecible** por naturaleza
- **Factores externos** no considerados
- **Latencia** de red puede afectar
- **Datos históricos** limitados

## 🐛 Solución de Problemas

### Error de Conexión
```bash
# Verificar credenciales en .env
# Comprobar conexión a internet
# Revisar logs en ./logs/app.log
```

### IA No Entrena
```bash
# Verificar datos suficientes (>100 muestras)
# Comprobar espacio en disco
# Revisar logs de TensorFlow
```

### Dashboard No Carga
```bash
# Verificar puerto 3000 disponible
# Comprobar archivos en ./public/
# Revisar consola del navegador
```

## 📁 Estructura del Proyecto

```
D:\iq_quot/
├── src/
│   ├── main.js                 # Aplicación principal
│   ├── connectors/
│   │   └── iqOptionConnector.js # Conexión IQ Option
│   ├── ai/
│   │   └── predictor.js        # IA y predicciones
│   ├── analysis/
│   │   └── technicalAnalyzer.js # Análisis técnico
│   ├── engine/
│   │   └── predictionEngine.js # Motor de predicción
│   ├── data/
│   │   └── dataManager.js      # Gestión de datos
│   └── utils/
│       └── logger.js           # Sistema de logging
├── config/
│   └── config.js               # Configuración
├── public/
│   ├── index.html              # Dashboard web
│   ├── css/
│   │   └── dashboard.css       # Estilos
│   └── js/
│       └── dashboard.js        # JavaScript frontend
├── data/                       # Datos locales
├── logs/                       # Archivos de log
├── models/                     # Modelos de IA
├── package.json                # Dependencias
└── README.md                   # Documentación
```

## 🤝 Contribuir

1. **Fork** el proyecto
2. **Crear rama** para nueva característica
3. **Commit** cambios
4. **Push** a la rama
5. **Abrir Pull Request**

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## ⚡ Próximas Características

- [ ] **Telegram Bot** para notificaciones
- [ ] **Backtesting** automático
- [ ] **Múltiples timeframes** simultáneos
- [ ] **Análisis de sentimiento** de noticias
- [ ] **API REST** completa
- [ ] **Docker** containerización
- [ ] **Estrategias** personalizables
- [ ] **Paper trading** integrado

## 📞 Soporte

Para soporte técnico o preguntas:
- **Issues**: GitHub Issues
- **Documentación**: Este README
- **Logs**: `./logs/app.log`

---

⚠️ **DISCLAIMER**: Este software es solo para fines educativos. El trading conlleva riesgos financieros. Use bajo su propia responsabilidad.
