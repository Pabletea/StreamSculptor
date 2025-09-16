from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from app.tasks.process_vod import download_and_extract_audio
from app.services.minio_client import get_minio_client

app = FastAPI(title="StreamSculptor - Ingest API")

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