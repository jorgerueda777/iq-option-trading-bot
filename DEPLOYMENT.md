# 🚀 Deployment en Render.com

## Bot de Trading IQ Option - Sistema Híbrido Mejorado

### 📊 Características del Bot:
- **Sistema Híbrido:** Combina 5.4 millones de datos históricos + análisis técnico
- **Predicciones Inteligentes:** Patrones por hora/día específicos
- **Trading Automático:** Solo minutos PARES, ejecución directa (sin inversión)
- **Multi-Asset:** 6 pares OTC simultáneos
- **Filtros Mejorados:** Aprovecha datos históricos masivos

### 🔧 Pasos para Deploy en Render:

#### 1. **Preparar Repositorio Git:**
```bash
git init
git add .
git commit -m "Bot híbrido mejorado con 5.4M datos históricos"
git branch -M main
git remote add origin https://github.com/tu-usuario/iq-option-bot.git
git push -u origin main
```

#### 2. **Configurar en Render.com:**
1. Crear cuenta en [render.com](https://render.com)
2. Conectar repositorio GitHub
3. Seleccionar "Web Service"
4. Configurar variables de entorno:

**Variables Requeridas:**
```
IQ_EMAIL=tu_email@iqoption.com
IQ_PASSWORD=tu_password_seguro
TRADING_AMOUNT=1
MIN_CONFIDENCE=50
```

**Variables Opcionales:**
```
MAX_SIMULTANEOUS_OPERATIONS=5
ENABLED_ASSETS=EURUSD-OTC,GBPUSD-OTC,EURJPY-OTC,EURGBP-OTC,USDCHF-OTC,AUDCAD-OTC
LOG_LEVEL=info
```

#### 3. **Configuración de Recursos:**
- **Plan:** Starter ($7/mes) o superior
- **Región:** Oregon (US West) para menor latencia
- **Disco:** 1GB para base de datos histórica
- **Auto-Deploy:** Activado desde main branch

#### 4. **Monitoreo:**
- **Dashboard:** `https://tu-app.onrender.com`
- **Logs:** Panel de Render en tiempo real
- **Salud:** Health check automático cada 30s

### 📊 Datos Incluidos:
- **EURUSD-OTC:** 1,053,977 velas (~2.0 años)
- **GBPUSD-OTC:** 993,600 velas (~1.9 años)  
- **EURJPY-OTC:** 792,000 velas (~1.5 años)
- **EURGBP-OTC:** 792,000 velas (~1.5 años)
- **USDCHF-OTC:** 792,000 velas (~1.5 años)
- **AUDCAD-OTC:** 1,051,200 velas (~2.0 años)

**Total:** 5,474,777 velas históricas para predicciones inteligentes

### ⚠️ Importante:
- **Credenciales seguras:** Nunca commitear passwords al repositorio
- **Monitoreo activo:** Revisar logs regularmente
- **Backup de datos:** La base de datos se mantiene en disco persistente
- **Actualizaciones:** Auto-deploy desde main branch

### 🎯 Configuración de Trading:
- **Solo minutos PARES:** 0, 2, 4, 6, 8...
- **Ejecución directa:** Como manda el bot (sin inversión)
- **Máximo 5 operaciones:** Simultáneas por ciclo
- **Duración:** 1 minuto por operación
- **Monto:** $1 por operación (configurable)

### 📈 Logs Esperados:
```
🔍 ANÁLISIS COMPLETO EURUSD-OTC: Usando TODOS los datos históricos
📊 PATRONES HISTÓRICOS: 2,847 ocurrencias horarias, 15,234 diarias
🎯 PREDICCIÓN HISTÓRICA: UP (68.4% confianza)
✅ Señal APROBADA - Ejecutando EURUSD CALL $1
```
