import tempfile
import os
from typing import List, Dict
from app.services.minio_client import get_minio_client
import json
import logging

LOG = logging.getLogger(__name__)

class SRTGenerator:
    """Generador de subtítulos SRT para clips"""
    
    def __init__(self):
        self.bucket = "vods"
    
    def generate_srt_for_clip(
        self, 
        job_id: str, 
        clip_start_time: float, 
        clip_end_time: float, 
        clip_index: int
    ) -> str:
        """Genera archivo SRT para un clip específico"""
        
        # Obtener transcripción completa
        transcript = self._get_transcript(job_id)
        if not transcript:
            raise Exception(f"No transcript found for job {job_id}")
        
        # Filtrar segmentos que caen dentro del clip
        clip_segments = self._filter_segments_for_clip(
            transcript["segments"], 
            clip_start_time, 
            clip_end_time
        )
        
        # Generar contenido SRT
        srt_content = self._create_srt_content(clip_segments, clip_start_time)
        
        # Guardar SRT en MinIO
        srt_object = f"{job_id}/clips/clip_{clip_index:02d}.srt"
        self._save_srt_to_minio(srt_object, srt_content)
        
        return srt_object
    
    def generate_srt_for_all_clips(self, job_id: str) -> Dict[int, str]:
        """Genera SRT para todos los clips de un job"""
        
        # Obtener metadata de clips
        clips_metadata = self._get_clips_metadata(job_id)
        srt_files = {}
        
        for clip in clips_metadata["clips"]:
            try:
                srt_object = self.generate_srt_for_clip(
                    job_id=job_id,
                    clip_start_time=clip["start_time"],
                    clip_end_time=clip["end_time"],
                    clip_index=clip["clip_index"]
                )
                srt_files[clip["clip_index"]] = srt_object
                LOG.info(f"SRT generated for clip {clip['clip_index']}: {srt_object}")
                
            except Exception as e:
                LOG.error(f"Failed to generate SRT for clip {clip['clip_index']}: {e}")
                
        return srt_files
    
    def _get_transcript(self, job_id: str) -> Dict:
        """Obtiene la transcripción completa desde MinIO"""
        client = get_minio_client()
        transcript_object = f"{job_id}/transcript.json"
        
        try:
            data = client.get_object(self.bucket, transcript_object)
            return json.loads(data.read().decode('utf-8'))
        except Exception as e:
            LOG.error(f"Failed to get transcript for {job_id}: {e}")
            return None
    
    def _get_clips_metadata(self, job_id: str) -> Dict:
        """Obtiene metadata de clips desde MinIO"""
        client = get_minio_client()
        metadata_object = f"{job_id}/clips_metadata.json"
        
        try:
            data = client.get_object(self.bucket, metadata_object)
            return json.loads(data.read().decode('utf-8'))
        except Exception as e:
            LOG.error(f"Failed to get clips metadata for {job_id}: {e}")
            return {"clips": []}
    
    def _filter_segments_for_clip(
        self, 
        segments: List[Dict], 
        clip_start: float, 
        clip_end: float
    ) -> List[Dict]:
        """Filtra segmentos de transcripción que caen dentro del tiempo del clip"""
        
        clip_segments = []
        
        for segment in segments:
            seg_start = segment.get("start", 0)
            seg_end = segment.get("end", seg_start + 1)
            
            # Verificar si el segmento se solapa con el clip
            if seg_end >= clip_start and seg_start <= clip_end:
                # Ajustar tiempos relativos al clip
                adjusted_segment = segment.copy()
                adjusted_segment["start"] = max(0, seg_start - clip_start)
                adjusted_segment["end"] = min(clip_end - clip_start, seg_end - clip_start)
                
                # Solo incluir si tiene duración positiva
                if adjusted_segment["end"] > adjusted_segment["start"]:
                    clip_segments.append(adjusted_segment)
        
        return clip_segments
    
    def _create_srt_content(self, segments: List[Dict], clip_start_time: float) -> str:
        """Crea contenido SRT formateado"""
        
        srt_lines = []
        
        for i, segment in enumerate(segments, 1):
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment.get("text", "").strip()
            
            if not text:
                continue
            
            # Formatear tiempos en formato SRT (HH:MM:SS,mmm)
            start_formatted = self._format_srt_time(start_time)
            end_formatted = self._format_srt_time(end_time)
            
            # Agregar línea SRT
            srt_lines.extend([
                str(i),
                f"{start_formatted} --> {end_formatted}",
                text,
                ""  # Línea vacía entre subtítulos
            ])
        
        return "\n".join(srt_lines)
    
    def _format_srt_time(self, seconds: float) -> str:
        """Formatea tiempo en formato SRT: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _save_srt_to_minio(self, srt_object: str, srt_content: str):
        """Guarda contenido SRT en MinIO"""
        client = get_minio_client()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(srt_content)
            temp_file_path = temp_file.name
        
        try:
            client.fput_object(self.bucket, srt_object, temp_file_path)
            LOG.info(f"SRT saved to MinIO: {srt_object}")
        finally:
            os.unlink(temp_file_path)