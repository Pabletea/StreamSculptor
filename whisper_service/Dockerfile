FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway usa la variable $PORT dinámicamente
EXPOSE $PORT

# Usar la variable $PORT de Railway
CMD ["sh", "-c", "uvicorn service:app --host 0.0.0.0 --port $PORT"]
