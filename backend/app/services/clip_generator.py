import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Dict
from app.services.minio_client import get_minio_client
from app.services.audio_analyzer import AudioSegment
import logging
import json

LOG = logging.getLogger(__name__)

class ClipGenerator:
    """Generador de clips de video usando ffmpeg"""
    
    def __init__(self):
        self.bucket = "vods"
    
    def generate_clips_from_segments(
        self, 
        job_id: str, 
        segments: List[AudioSegment], 
        max_clips: int = 10
    ) -> List[Dict]:
        """Genera clips de video para los segmentos seleccionados"""
        
        client = get_minio_client()
        clips_metadata = []
        
        # Descargar video original
        video_object = f"{job_id}/input.mp4"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            try:
                LOG.info(f"Downloading video {video_object} for clipping...")
                data = client.get_object(self.bucket, video_object)
                for chunk in data.stream(8192):
                    temp_video.write(chunk)
                
                temp_video.flush()
                video_path = temp_video.name
                
                # Generar clips para cada segmento
                for i, segment in enumerate(segments[:max_clips]):
                    clip_metadata = self._create_clip(
                        job_id=job_id,
                        segment=segment,
                        video_path=video_path,
                        clip_index=i,
                        client=client
                    )
                    clips_metadata.append(clip_metadata)
                
                return clips_metadata
                
            finally:
                if os.path.exists(video_path):
                    os.unlink(video_path)
    
    def _create_clip(
        self, 
        job_id: str, 
        segment: AudioSegment, 
        video_path: str, 
        clip_index: int,
        client
    ) -> Dict:
        """Crea un clip individual usando ffmpeg"""
        
        clip_filename = f"clip_{clip_index:02d}.mp4"
        clip_object = f"{job_id}/clips/{clip_filename}"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_clip:
            try:

                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-ss", str(segment.start_time),
                    "-t", str(segment.duration),
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-preset", "fast",
                    "-crf", "23",
                    temp_clip.name
                ]
                
                LOG.info(f"Creating clip {clip_index}: {segment.start_time:.1f}s-{segment.end_time:.1f}s")
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                    LOG.error("FFmpeg failed for clip %s: returncode=%s stdout=%s stderr=%s", clip_index, proc.returncode, proc.stdout, proc.stderr)
                    raise RuntimeError(f"Failed to generate clip {clip_index}: returncode={proc.returncode}; stderr={proc.stderr}")

                # Subir clip a MinIO
                client.fput_object(self.bucket, clip_object, temp_clip.name)
                
                # Crear metadata del clip
                clip_metadata = {
                    "clip_index": clip_index,
                    "filename": clip_filename,
                    "object_name": clip_object,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "duration": segment.duration,
                    "rms_score": segment.rms_score,
                    "peak_amplitude": segment.peak_amplitude,
                    "composite_score": getattr(segment, 'composite_score', 0.0),
                    "file_size_mb": os.path.getsize(temp_clip.name) / (1024*1024)
                }
                
                LOG.info(f"Clip {clip_index} generated: {clip_metadata['file_size_mb']:.1f}MB")
                return clip_metadata
                
            except subprocess.CalledProcessError as e:
                LOG.error(f"FFmpeg failed for clip {clip_index}: {e.stderr.decode()}")
                raise Exception(f"Failed to generate clip {clip_index}")
            
            finally:
                if os.path.exists(temp_clip.name):
                    os.unlink(temp_clip.name)
    
    def save_clips_metadata(self, job_id: str, clips_metadata: List[Dict]):
        """Guarda metadata de clips en MinIO"""
        client = get_minio_client()
        metadata_object = f"{job_id}/clips_metadata.json"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump({
                "job_id": job_id,
                "clips_count": len(clips_metadata),
                "clips": clips_metadata,
                "generated_at": str(datetime.utcnow())
            }, temp_file, indent=2, default=str)
            temp_file_path = temp_file.name
        
        try:
            client.fput_object(self.bucket, metadata_object, temp_file_path)
            LOG.info(f"Clips metadata saved: {metadata_object}")
        finally:
            os.unlink(temp_file_path)

# Importar datetime al inicio del archivo
from datetime import datetime