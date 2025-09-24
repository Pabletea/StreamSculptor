FROM node:18-alpine

WORKDIR /app

# Copiamos dependencias primero
COPY package.json package-lock.json* ./

# Instalamos dependencias
RUN npm ci --legacy-peer-deps

# Copiamos el resto del código
COPY . .

# Railway usa la variable $PORT dinámicamente
EXPOSE $PORT

# Para desarrollo en Railway
CMD ["sh", "-c", "npm run dev -- --port $PORT --host 0.0.0.0"]