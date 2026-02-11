import os
import requests
import logging

LOG = logging.getLogger(__name__)

WHISPER_URL = os.environ.get("WHISPER_URL", "http://whisper:5000")  # Base URL del servicio Whisper

def transcribe_audio(file_path: str):
    """Envía el archivo de audio al servicio Whisper y devuelve la transcripción."""
    with open(file_path, "rb") as f:
        response = requests.post(f"{WHISPER_URL}/transcribe", files={"file": f})
    response.raise_for_status()
    return response.json()

def transcribe_audio_from_minio(bucket: str, object_name: str):
    """Transcribe audio directamente desde MinIO sin descarga local."""
    try:
        LOG.info(f"Requesting transcription for {bucket}/{object_name}")
        
        payload = {
            "bucket": bucket,
            "object_name": object_name
        }
        
        response = requests.post(
            f"{WHISPER_URL}/transcribe-from-minio", 
            json=payload,
            timeout=1200  # 5 minutos timeout para transcripciones largas
        )
        
        response.raise_for_status()
        result = response.json()
        
        LOG.info(f"Transcription completed for {object_name}")
        return result
        
    except requests.exceptions.Timeout:
        LOG.error(f"Transcription timeout for {object_name}")
        raise Exception("Transcription timeout - audio file may be too long")
    except requests.exceptions.RequestException as e:
        LOG.error(f"Request failed for transcription: {e}")
        raise Exception(f"Failed to connect to Whisper service: {str(e)}")
    except Exception as e:
        LOG.error(f"Unexpected error during transcription: {e}")
        raise