from app.celery_app import celery
from app.services.audio_analyzer import AudioAnalyzer
from app.services.clip_generator import ClipGenerator
from app.services.srt_generator import SRTGenerator
from app.services.minio_client import get_minio_client
import logging
import json
import tempfile
import time

LOG = logging.getLogger(__name__)

@celery.task(bind=True)
def analyze_audio_segments(
    self, 
    job_id: str, 
    window_size: float = 30.0, 
    step_size: float = 10.0,
    energy_threshold: float = 0.01
):
    """Analiza audio y encuentra segmentos con alta energía"""
    try:
        start_time = time.time()
        
        LOG.info(f"Starting audio analysis for job {job_id}")
        
        # Inicializar analizador
        analyzer = AudioAnalyzer(window_size=window_size, step_size=step_size)
        
        # Analizar audio desde MinIO
        bucket = "vods"
        audio_object = f"{job_id}/audio.wav"
        segments = analyzer.analyze_audio_from_minio(bucket, audio_object)
        
        # Filtrar por umbral de energía
        filtered_segments = [s for s in segments if s.rms_score >= energy_threshold]
        
        # Rankear por energía
        top_segments = analyzer.rank_segments_by_energy(filtered_segments, top_n=20)
        
        # Guardar análisis en MinIO
        analysis_result = {
            "job_id": job_id,
            "total_segments": len(segments),
            "filtered_segments": len(filtered_segments),
            "top_segments": len(top_segments),
            "segments": [
                {
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "duration": s.duration,
                    "rms_score": s.rms_score,
                    "peak_amplitude": s.peak_amplitude,
                    "spectral_centroid": s.spectral_centroid,
                    "zero_crossing_rate": s.zero_crossing_rate,
                    "composite_score": getattr(s, 'composite_score', 0.0)
                }
                for s in top_segments
            ],
            "analysis_duration": time.time() - start_time,
            "parameters": {
                "window_size": window_size,
                "step_size": step_size,
                "energy_threshold": energy_threshold
            }
        }
        
        # Guardar en MinIO
        client = get_minio_client()
        analysis_object = f"{job_id}/audio_analysis.json"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(analysis_result, temp_file, indent=2, default=str)
            temp_file_path = temp_file.name
        
        try:
            client.fput_object(bucket, analysis_object, temp_file_path)
        finally:
            import os
            os.unlink(temp_file_path)
        
        LOG.info(f"Audio analysis completed for {job_id}: {len(top_segments)} segments")
        return analysis_result
        
    except Exception as e:
        LOG.exception(f"Audio analysis failed for job {job_id}: {e}")
        raise

@celery.task(bind=True)
def generate_clips_task(self, job_id: str, max_clips: int = 10):
    """Genera clips de video basados en el análisis de audio"""
    try:
        start_time = time.time()
        
        LOG.info(f"Starting clip generation for job {job_id}")
        
        # Obtener análisis de audio
        client = get_minio_client()
        bucket = "vods"
        analysis_object = f"{job_id}/audio_analysis.json"
        
        try:
            data = client.get_object(bucket, analysis_object)
            analysis_result = json.loads(data.read().decode('utf-8'))
        except Exception as e:
            raise Exception(f"Audio analysis not found for job {job_id}. Run analysis first.")
        
        # Convertir datos a objetos AudioSegment
        from app.services.audio_analyzer import AudioSegment
        segments = []
        for seg_data in analysis_result["segments"][:max_clips]:
            segment = AudioSegment(
                start_time=seg_data["start_time"],
                end_time=seg_data["end_time"],
                duration=seg_data["duration"],
                rms_score=seg_data["rms_score"],
                peak_amplitude=seg_data["peak_amplitude"],
                spectral_centroid=seg_data["spectral_centroid"],
                zero_crossing_rate=seg_data["zero_crossing_rate"]
            )
            segment.composite_score = seg_data["composite_score"]
            segments.append(segment)
        
        # Generar clips
        clip_generator = ClipGenerator()
        clips_metadata = clip_generator.generate_clips_from_segments(job_id, segments, max_clips)
        
        # Guardar metadata de clips
        clip_generator.save_clips_metadata(job_id, clips_metadata)
        
        # Generar subtítulos SRT
        srt_generator = SRTGenerator()
        srt_files = srt_generator.generate_srt_for_all_clips(job_id)
        
        # Actualizar metadata con info SRT
        for clip in clips_metadata:
            clip_idx = clip["clip_index"]
            if clip_idx in srt_files:
                clip["has_srt"] = True
                clip["srt_object"] = srt_files[clip_idx]
        
        # Resultado final
        result = {
            "job_id": job_id,
            "clips_generated": len(clips_metadata),
            "clips": clips_metadata,
            "srt_files": srt_files,
            "total_size_mb": sum(clip["file_size_mb"] for clip in clips_metadata),
            "generation_time": time.time() - start_time
        }
        
        LOG.info(f"Clip generation completed for {job_id}: {len(clips_metadata)} clips")
        return result
        
    except Exception as e:
        LOG.exception(f"Clip generation failed for job {job_id}: {e}")
        raise

