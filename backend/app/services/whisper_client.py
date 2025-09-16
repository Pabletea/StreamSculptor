import requests

WHISPER_URL = "http://whisper:5000/transcribe"  # nombre del servicio en docker-compose

def transcribe_audio(file_path: str):
    """Envía el archivo de audio al servicio Whisper y devuelve la transcripción."""
    with open(file_path, "rb") as f:
        response = requests.post(WHISPER_URL, files={"file": f})
    response.raise_for_status()
    return response.json()