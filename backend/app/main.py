from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import timedelta
import uuid
from app.tasks.process_vod import download_and_extract_audio
from app.services.minio_client import get_minio_client
from app.services.whisper_client import transcribe_audio  # <— tu función

app = FastAPI(title="StreamSculptor - Ingest API")

class TranscribeRequest(BaseModel):
    job_id: str  # opcional si quieres buscar la ruta desde el job_id
    audio_path: str  # ruta completa dentro del contenedor

class DownloadRequest(BaseModel):
    source_url: str
    user_id: int | None = None

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/ingest/download")
def ingest_download(req: DownloadRequest):
    job_id = str(uuid.uuid4())
    # enlocamos la tarea (async worker)
    task = download_and_extract_audio.delay(job_id, req.source_url, req.user_id)
    return {"job_id":job_id,"task_id":task.id, "status":"queued"}


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
def list_files(job_id: str):
    client = get_minio_client()
    bucket = "vods"
    objects = [obj.object_name for obj in client.list_objects(bucket, prefix=f"{job_id}/")]
    return {"objects": objects}

@app.get("/download/{job_id}/{file_type}")
def download_file(job_id: str, file_type: str):
    client = get_minio_client()
    bucket = "vods"
    object_name = f"{job_id}/{'input.mp4' if file_type=='video' else 'audio.wav'}"

    try:
        data = client.get_object(bucket, object_name)
        filename = f"{file_type}_{job_id}.{'mp4' if file_type=='video' else 'wav'}"
        return StreamingResponse(
            data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {e}")


@app.post("/transcribe")
def transcribe_endpoint(req: TranscribeRequest):
    try:
        # Llamas a tu función de servicios
        result = transcribe_audio(req.audio_path)
        return {"job_id": req.job_id, "transcription": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))