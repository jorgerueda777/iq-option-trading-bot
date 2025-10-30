# Bot de Trading IQ Option - Sistema Híbrido Mejorado
FROM node:18-alpine

# Instalar Python y dependencias del sistema
RUN apk add --no-cache python3 py3-pip sqlite

# Crear directorio de trabajo
WORKDIR /app

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias de Node.js
RUN npm ci --only=production

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir iqoptionapi requests pandas numpy

# Copiar código fuente
COPY . .

# Crear directorio para base de datos
RUN mkdir -p /app/data

# Dar permisos de ejecución
RUN chmod +x /app/start.bat 2>/dev/null || true

# Exponer puerto para dashboard (opcional)
EXPOSE 3000

# Variables de entorno por defecto
ENV NODE_ENV=production
ENV TZ=America/New_York

# Comando de inicio
CMD ["node", "src/main.js"]
