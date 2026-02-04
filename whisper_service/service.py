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

# Carga lazy del modelo para evitar bloquear el arranque del servicio
model = None
model_name = os.environ.get("WHISPER_MODEL", "base")
model_loading = False
model_error = None

class TranscribeFromMinIORequest(BaseModel):
    bucket: str = "vods"
    object_name: str  # ej: "job_id/audio.wav"


def get_model():
    """Carga el modelo la primera vez que se necesita y devuelve la instancia.
    Levanta HTTPException(503) si ya se está cargando, o 500 si falló la carga.
    """
    global model, model_loading, model_error
    if model is not None:
        return model
    if model_loading:
        raise HTTPException(status_code=503, detail="Model is currently loading")
    try:
        model_loading = True
        LOG.info("Loading Whisper model '%s'...", model_name)
        model = whisper.load_model(model_name)
        LOG.info("Whisper model '%s' loaded successfully", model_name)
        model_error = None
        return model
    except Exception as e:
        model_error = str(e)
        LOG.exception("Failed to load Whisper model: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")
    finally:
        model_loading = False
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

    # Cargar modelo si es necesario
    mdl = get_model()

    result = mdl.transcribe(str(temp_path))
    
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
                
                # Cargar modelo si es necesario
                mdl = get_model()
                # Transcribir usando Whisper
                result = mdl.transcribe(temp_file_path)
                
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
    """Estado del servicio y del modelo (not_loaded / loading / ready / error)"""
    model_status = "ready" if model is not None else ("loading" if model_loading else ("error" if model_error else "not_loaded"))
    return {"status": "ok", "model": model_name, "model_status": model_status, "model_error": model_error}
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)