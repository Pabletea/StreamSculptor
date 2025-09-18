from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import timedelta
import uuid
import json
from app.tasks.process_vod import download_and_extract_audio, transcribe_vod_audio, process_vod_complete
from app.tasks.analyze_audio import analyze_audio_segments, generate_clips_task, process_vod_with_clips
from app.services.minio_client import get_minio_client
from app.services.whisper_client import transcribe_audio, transcribe_audio_from_minio
from app.models.clip_models import GenerateClipsRequest, ClipsResponse, AudioAnalysisResponse

app = FastAPI(title="StreamSculptor - Ingest & Clips API")

# Configurar CORS para el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscribeRequest(BaseModel):
    job_id: str
    audio_path: str

class TranscribeMinIORequest(BaseModel):
    job_id: str
    bucket: str = "vods"

class DownloadRequest(BaseModel):
    source_url: str
    user_id: int | None = None

class ProcessVODWithClipsRequest(BaseModel):
    source_url: str
    user_id: int | None = None
    max_clips: int = 10

@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# ENDPOINTS ORIGINALES
# ===============================

@app.post("/ingest/download")
def ingest_download(req: DownloadRequest):
    job_id = str(uuid.uuid4())
    task = download_and_extract_audio.delay(job_id, req.source_url, req.user_id)
    return {"job_id": job_id, "task_id": task.id, "status": "queued"}

@app.post("/ingest/download-and-transcribe")
def ingest_download_and_transcribe(req: DownloadRequest):
    job_id = str(uuid.uuid4())
    task = process_vod_complete.delay(job_id, req.source_url, req.user_id)
    return {"job_id": job_id, "task_id": task.id, "status": "processing"}

@app.post("/transcribe/from-minio")
def transcribe_from_minio_endpoint(req: TranscribeMinIORequest):
    try:
        audio_object = f"{req.job_id}/audio.wav"
        result = transcribe_audio_from_minio(req.bucket, audio_object)
        return {"job_id": req.job_id, "transcription": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# NUEVOS ENDPOINTS - CLIPS
# ===============================

@app.post("/ingest/process-with-clips")
def process_vod_with_clips_endpoint(req: ProcessVODWithClipsRequest):
    """Pipeline completo: descarga + transcribe + análisis + clips"""
    job_id = str(uuid.uuid4())
    task = process_vod_with_clips.delay(
        job_id, 
        req.source_url, 
        req.user_id, 
        req.max_clips
    )
    return {
        "job_id": job_id, 
        "task_id": task.id, 
        "status": "processing",
        "message": "Full pipeline started: download → transcribe → analyze → generate clips"
    }

@app.post("/audio/analyze/{job_id}")
def analyze_audio_endpoint(job_id: str, window_size: float = 30.0, step_size: float = 10.0):
    """Analizar audio y encontrar segmentos con alta energía"""
    task = analyze_audio_segments.delay(job_id, window_size, step_size)
    return {"job_id": job_id, "task_id": task.id, "status": "analyzing"}

@app.get("/audio/analysis/{job_id}")
def get_audio_analysis(job_id: str):
    """Obtener resultado del análisis de audio"""
    client = get_minio_client()
    bucket = "vods"
    analysis_object = f"{job_id}/audio_analysis.json"
    
    try:
        data = client.get_object(bucket, analysis_object)
        analysis = json.loads(data.read().decode('utf-8'))
        return analysis
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Analysis not found for job {job_id}: {e}")

@app.post("/clips/generate")
def generate_clips_endpoint(req: GenerateClipsRequest):
    """Generar clips basados en análisis de audio"""
    task = generate_clips_task.delay(req.job_id, req.max_clips)
    return {
        "job_id": req.job_id, 
        "task_id": task.id, 
        "status": "generating_clips",
        "max_clips": req.max_clips
    }

@app.get("/clips/{job_id}")
def get_clips(job_id: str):
    """Listar todos los clips generados para un job"""
    client = get_minio_client()
    bucket = "vods"
    metadata_object = f"{job_id}/clips_metadata.json"
    
    try:
        data = client.get_object(bucket, metadata_object)
        clips_data = json.loads(data.read().decode('utf-8'))
        return clips_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Clips not found for job {job_id}: {e}")

@app.get("/clips/{job_id}/download/{clip_index}")
def download_clip(job_id: str, clip_index: int):
    """Descargar un clip específico"""
    client = get_minio_client()
    bucket = "vods"
    clip_object = f"{job_id}/clips/clip_{clip_index:02d}.mp4"
    
    try:
        data = client.get_object(bucket, clip_object)
        filename = f"clip_{clip_index}_{job_id}.mp4"
        
        return StreamingResponse(
            data,
            media_type="video/mp4",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Clip not found: {e}")

@app.get("/clips/{job_id}/srt/{clip_index}")
def download_srt(job_id: str, clip_index: int):
    """Descargar subtítulos SRT de un clip"""
    client = get_minio_client()
    bucket = "vods"
    srt_object = f"{job_id}/clips/clip_{clip_index:02d}.srt"
    
    try:
        data = client.get_object(bucket, srt_object)
        filename = f"clip_{clip_index}_{job_id}.srt"
        
        return StreamingResponse(
            data,
            media_type="application/x-subrip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"SRT not found: {e}")

@app.get("/clips/{job_id}/preview")
def get_clips_preview(job_id: str):
    """Vista previa de clips con metadata básica"""
    try:
        clips_data = get_clips(job_id)
        
        preview = {
            "job_id": job_id,
            "total_clips": len(clips_data.get("clips", [])),
            "clips": [
                {
                    "clip_index": clip["clip_index"],
                    "duration": clip["duration"],
                    "start_time": clip["start_time"],
                    "composite_score": clip["composite_score"],
                    "file_size_mb": clip["file_size_mb"],
                    "has_srt": clip.get("has_srt", False)
                }
                for clip in clips_data.get("clips", [])
            ]
        }
        
        return preview
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ===============================
# ENDPOINTS UTILITARIOS
# ===============================

@app.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Obtener estado de una tarea Celery"""
    from app.celery_app import celery
    task = celery.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to be processed'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),
            'error': str(task.info)
        }
    return response

@app.get("/test-minio")
def test_minio():
    client = get_minio_client()
    buckets = [b.name for b in client.list_buckets()]
    return {"buckets": buckets}

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
        "transcript": "transcript.json",
        "analysis": "audio_analysis.json",
        "clips_metadata": "clips_metadata.json"
    }
    
    if file_type not in file_mapping:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    object_name = f"{job_id}/{file_mapping[file_type]}"

    try:
        data = client.get_object(bucket, object_name)
        filename = f"{file_type}_{job_id}.{file_mapping[file_type].split('.')[-1]}"
        
        media_types = {
            "video": "video/mp4",
            "audio": "audio/wav",
            "transcript": "application/json",
            "analysis": "application/json",
            "clips_metadata": "application/json"
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