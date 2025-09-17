from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import timedelta
import uuid
from app.tasks.process_vod import download_and_extract_audio, transcribe_vod_audio, process_vod_complete
from app.services.minio_client import get_minio_client
from app.services.whisper_client import transcribe_audio, transcribe_audio_from_minio
import json

app = FastAPI(title="StreamSculptor - Ingest API")

class TranscribeRequest(BaseModel):
    job_id: str  # opcional si quieres buscar la ruta desde el job_id
    audio_path: str  # ruta completa dentro del contenedor

class TranscribeMinIORequest(BaseModel):
    job_id: str
    bucket: str = "vods"  # bucket por defecto

class DownloadRequest(BaseModel):
    source_url: str
    user_id: int | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest/download")
def ingest_download(req: DownloadRequest):
    job_id = str(uuid.uuid4())
    # encolamos la tarea (async worker)
    task = download_and_extract_audio.delay(job_id, req.source_url, req.user_id)
    return {"job_id": job_id, "task_id": task.id, "status": "queued"}

@app.post("/ingest/download-and-transcribe")
def ingest_download_and_transcribe(req: DownloadRequest):
    """Endpoint para el pipeline completo: descargar + transcribir"""
    job_id = str(uuid.uuid4())
    # encolamos la tarea completa
    task = process_vod_complete.delay(job_id, req.source_url, req.user_id)
    return {"job_id": job_id, "task_id": task.id, "status": "processing"}

@app.post("/transcribe/from-minio")
def transcribe_from_minio_endpoint(req: TranscribeMinIORequest):
    """Transcribir audio que ya está en MinIO"""
    try:
        audio_object = f"{req.job_id}/audio.wav"
        result = transcribe_audio_from_minio(req.bucket, audio_object)
        return {"job_id": req.job_id, "transcription": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe/task/{job_id}")
def start_transcription_task(job_id: str):
    """Iniciar tarea de transcripción para un job_id específico"""
    task = transcribe_vod_audio.delay(job_id)
    return {"job_id": job_id, "task_id": task.id, "status": "transcribing"}

@app.post("/transcribe")
def transcribe_endpoint(req: TranscribeRequest):
    """Endpoint original para transcripción desde archivo local"""
    try:
        # Llamas a tu función de servicios
        result = transcribe_audio(req.audio_path)
        return {"job_id": req.job_id, "transcription": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-minio")
def test_minio():
    client = get_minio_client()
    buckets = [b.name for b in client.list_buckets()]
    return {"buckets": buckets}

@app.get("/test-minio-files")
def list_files():
    client = get_minio_client()
    bucket = "vods"
    objects = [obj.object_name for obj in client.list_objects(bucket)]
    return {"objects": objects}

@app.get("/test-minio-files/{job_id}")
def list_job_files(job_id: str):
    client = get_minio_client()
    bucket = "vods"
    objects = [obj.object_name for obj in client.list_objects(bucket, prefix=f"{job_id}/")]
    return {"objects": objects}

@app.get("/download/{job_id}/{file_type}")
def download_file(job_id: str, file_type: str):
    client = get_minio_client()
    bucket = "vods"
    
    file_mapping = {
        "video": "input.mp4",
        "audio": "audio.wav", 
        "transcript": "transcript.json"
    }
    
    if file_type not in file_mapping:
        raise HTTPException(status_code=400, detail="Invalid file type. Use: video, audio, transcript")
    
    object_name = f"{job_id}/{file_mapping[file_type]}"

    try:
        data = client.get_object(bucket, object_name)
        filename = f"{file_type}_{job_id}.{file_mapping[file_type].split('.')[-1]}"
        
        media_types = {
            "video": "video/mp4",
            "audio": "audio/wav",
            "transcript": "application/json"
        }
        
        return StreamingResponse(
            data,
            media_type=media_types.get(file_type, "application/octet-stream"),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {e}")

@app.get("/transcript/{job_id}")
def get_transcript(job_id: str):
    """Obtener la transcripción de un job específico"""
    client = get_minio_client()
    bucket = "vods"
    object_name = f"{job_id}/transcript.json"
    
    try:
        data = client.get_object(bucket, object_name)
        transcript_data = json.loads(data.read().decode('utf-8'))
        return transcript_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Transcript not found for job {job_id}: {e}")