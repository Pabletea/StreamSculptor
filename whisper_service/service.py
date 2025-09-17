from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import whisper
import uvicorn
from pathlib import Path
import tempfile
import os
from minio import Minio
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

app = FastAPI(title="Whisper Service")

# Cargar modelo (CPU, base para no consumir demasiado)
model = whisper.load_model("base")

class TranscribeFromMinIORequest(BaseModel):
    bucket: str = "vods"
    object_name: str  # ej: "job_id/audio.wav"

def get_minio_client():
    """Crear cliente MinIO con las mismas configuraciones del backend"""
    endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
    access_key = os.environ.get("MINIO_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET", "minioadmin")
    
    # Limpiar el endpoint si tiene esquema
    if "://" in endpoint:
        endpoint = endpoint.split("://")[1]
    
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False
    )
    return client

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Endpoint original para archivos subidos directamente"""
    temp_path = Path("/tmp") / file.filename
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    result = model.transcribe(str(temp_path))
    
    # Limpiar archivo temporal
    temp_path.unlink(missing_ok=True)
    
    return {"segments": result["segments"], "text": result["text"]}

@app.post("/transcribe-from-minio")
def transcribe_from_minio(req: TranscribeFromMinIORequest):
    """Transcribir audio directamente desde MinIO sin descarga local"""
    try:
        client = get_minio_client()
        
        # Verificar que el objeto existe
        try:
            client.stat_object(req.bucket, req.object_name)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Object not found: {req.object_name}")
        
        # Usar un archivo temporal para el streaming
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            try:
                LOG.info(f"Downloading {req.object_name} from MinIO...")
                
                # Stream el objeto desde MinIO al archivo temporal
                data = client.get_object(req.bucket, req.object_name)
                for chunk in data.stream(8192):  # Lee en chunks de 8KB
                    temp_file.write(chunk)
                
                temp_file.flush()
                temp_file_path = temp_file.name
                
                LOG.info(f"Starting transcription of {temp_file_path}...")
                
                # Transcribir usando Whisper
                result = model.transcribe(temp_file_path)
                
                LOG.info("Transcription completed successfully")
                
                return {
                    "object_name": req.object_name,
                    "segments": result["segments"], 
                    "text": result["text"]
                }
                
            finally:
                # Limpiar el archivo temporal
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    LOG.info(f"Temporary file {temp_file_path} cleaned up")
                    
    except Exception as e:
        LOG.exception(f"Error transcribing from MinIO: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok", "model": "whisper-base"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)