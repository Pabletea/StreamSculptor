import os 
import subprocess
from pathlib import Path
from app.celery_app import celery
from app.services.minio_client import get_minio_client
import logging

LOG = logging.getLogger(__name__)

@celery.task(bind=True)
def download_and_extract_audio(self, job_id:str, source_url: str, user_id: int | None = None):
    workdir = Path("/tmp/streamsculptor") / job_id
    workdir.mkdir(parents=True, exist_ok=True)

    video_path = workdir / "input.mp4"
    audio_path = workdir / "audio.wav"

    # 1) Donwload with yt-dlp
    try:
        cmd_dl = ["yt-dlp", "-f", "best","-o", str(video_path),source_url]
        LOG.info("Running: %s", " ".join(cmd_dl))
        subprocess.run(cmd_dl, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        LOG.exception("yt-dlp failed : %s",e)
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

    # 4) return metadata
    return {"job_id": job_id, "video_obj": video_obj, "audio_obj": audio_obj}
