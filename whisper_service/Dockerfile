FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Copiar el código del servicio
COPY . /app

# Instalar whisper.cpp o faster-whisper
RUN pip install git+https://github.com/openai/whisper.git
RUN pip install torch  # si tienes CPU, funciona bien. Para GPU instalar la versión CUDA

# Exponer puerto para la API
EXPOSE 5000

CMD ["python", "service.py"]
