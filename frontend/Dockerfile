FROM node:18-alpine

WORKDIR /app

# Copiamos dependencias primero
COPY package.json package-lock.json ./

# Instalamos dependencias de forma limpia (respeta el lockfile)
RUN npm ci --legacy-peer-deps

# Copiamos el resto del código (excluyendo node_modules)
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]