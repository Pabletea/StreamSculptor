import os 
import subprocess
from pathlib import Path
from app.celery_app import celery
from app.services.minio_client import get_minio_client
from app.services.whisper_client import transcribe_audio_from_minio
import logging

LOG = logging.getLogger(__name__)

@celery.task(bind=True)
def download_and_extract_audio(self, job_id: str, source_url: str, user_id: int | None = None):
    workdir = Path("/tmp/streamsculptor") / job_id
    workdir.mkdir(parents=True, exist_ok=True)

    video_path = workdir / "input.mp4"
    audio_path = workdir / "audio.wav"

    # 1) Download with yt-dlp
    try:
        cmd_dl = ["yt-dlp", "-f", "best", "-o", str(video_path), source_url]
        LOG.info("Running: %s", " ".join(cmd_dl))
        subprocess.run(cmd_dl, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        LOG.exception("yt-dlp failed: %s", e)
        raise

    # 2) Extract audio with ffmpeg (WAV)
    try:
        cmd_ff = ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", str(audio_path)]
        LOG.info("Running: %s", " ".join(cmd_ff))
        subprocess.run(cmd_ff, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        LOG.exception("ffmpeg failed: %s", e)
        raise

    # 3) Upload to MinIO
    client = get_minio_client()
    bucket = "vods"
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    video_obj = f"{job_id}/input.mp4"
    audio_obj = f"{job_id}/audio.wav"

    client.fput_object(bucket, video_obj, str(video_path))
    client.fput_object(bucket, audio_obj, str(audio_path))

    # 4) Cleanup local files
    video_path.unlink(missing_ok=True)
    audio_path.unlink(missing_ok=True)
    workdir.rmdir()

    # 5) Return metadata
    return {"job_id": job_id, "video_obj": video_obj, "audio_obj": audio_obj}

@celery.task(bind=True)
def transcribe_vod_audio(self, job_id: str):
    """Tarea para transcribir el audio de un VOD desde MinIO"""
    try:
        bucket = "vods"
        audio_obj = f"{job_id}/audio.wav"
        
        LOG.info(f"Starting transcription for job {job_id}")
        
        # Llamar al servicio Whisper
        transcription = transcribe_audio_from_minio(bucket, audio_obj)
        
        # Guardar la transcripción en MinIO como JSON
        client = get_minio_client()
        transcript_obj = f"{job_id}/transcript.json"
        
        import json
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(transcription, temp_file, indent=2)
            temp_file_path = temp_file.name
        
        try:
            client.fput_object(bucket, transcript_obj, temp_file_path)
            LOG.info(f"Transcription saved to MinIO: {transcript_obj}")
        finally:
            os.unlink(temp_file_path)
        
        return {
            "job_id": job_id,
            "transcript_obj": transcript_obj,
            "text": transcription["text"],
            "segments_count": len(transcription["segments"])
        }
        
    except Exception as e:
        LOG.exception(f"Transcription failed for job {job_id}: {e}")
        raise

@celery.task(bind=True)
def process_vod_complete(self, job_id: str, source_url: str, user_id: int | None = None):
    """Tarea completa: descarga, extrae audio y transcribe"""
    try:
        # 1. Descargar y extraer audio
        LOG.info(f"Starting complete VOD processing for job {job_id}")
        
        download_result = download_and_extract_audio.apply(args=[job_id, source_url, user_id])
        if download_result.failed():
            raise Exception("Download and audio extraction failed")
        
        # 2. Transcribir audio
        transcript_result = transcribe_vod_audio.apply(args=[job_id])
        if transcript_result.failed():
            raise Exception("Transcription failed")
        
        # 3. Retornar resultado completo
        return {
            "job_id": job_id,
            "status": "completed",
            "download": download_result.result,
            "transcription": transcript_result.result
        }
        
    except Exception as e:
        LOG.exception(f"Complete VOD processing failed for job {job_id}: {e}")
        raise