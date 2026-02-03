import numpy as np
import librosa
import tempfile
import os
from typing import List, Dict, Tuple
from dataclasses import dataclass
from app.services.minio_client import get_minio_client
import logging

LOG = logging.getLogger(__name__)

@dataclass
class AudioSegment:
    start_time: float
    end_time: float
    duration: float
    rms_score: float
    peak_amplitude: float
    spectral_centroid: float
    zero_crossing_rate: float
    
class AudioAnalyzer:
    """Analizador de audio para detectar segmentos con alta energía"""
    
    def __init__(self, window_size: float = 30.0, step_size: float = 10.0):
        self.window_size = window_size
        self.step_size = step_size
        
    def analyze_audio_from_minio(self, bucket: str, audio_object: str) -> List[AudioSegment]:
        """Analiza audio desde MinIO y devuelve segmentos con scores"""
        client = get_minio_client()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            try:
                # Descargar audio a archivo temporal
                LOG.info(f"Downloading {audio_object} for analysis...")
                data = client.get_object(bucket, audio_object)
                for chunk in data.stream(8192):
                    temp_file.write(chunk)
                
                temp_file.flush()
                temp_file_path = temp_file.name
                

                LOG.info("Loading audio with librosa...")
                y, sr = librosa.load(temp_file_path, sr=None)
                

                segments = self._create_sliding_windows(y, sr)
                
                LOG.info(f"Generated {len(segments)} audio segments")
                return segments
                
            finally:

                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
    
    def _create_sliding_windows(self, y: np.ndarray, sr: int) -> List[AudioSegment]:
        """Crea ventanas deslizantes y calcula métricas"""
        segments = []
        

        window_samples = int(self.window_size * sr)
        step_samples = int(self.step_size * sr)
        

        for start_sample in range(0, len(y) - window_samples + 1, step_samples):
            end_sample = start_sample + window_samples
            

            segment_audio = y[start_sample:end_sample]

            start_time = start_sample / sr
            end_time = end_sample / sr
            duration = self.window_size
            

            rms_score = self._calculate_rms(segment_audio)
            peak_amplitude = np.max(np.abs(segment_audio))
            spectral_centroid = self._calculate_spectral_centroid(segment_audio, sr)
            zero_crossing_rate = self._calculate_zcr(segment_audio)
            
            segment = AudioSegment(
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                rms_score=rms_score,
                peak_amplitude=peak_amplitude,
                spectral_centroid=spectral_centroid,
                zero_crossing_rate=zero_crossing_rate
            )
            
            segments.append(segment)
            
        return segments
    
    def _calculate_rms(self, audio: np.ndarray) -> float:
        """Calcula RMS (Root Mean Square) - indicador de energía"""
        return float(np.sqrt(np.mean(audio**2)))
    
    def _calculate_spectral_centroid(self, audio: np.ndarray, sr: int) -> float:
        """Calcula centroide espectral - indicador de brillo/tono"""
        try:
            centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            return float(np.mean(centroid))
        except:
            return 0.0
    
    def _calculate_zcr(self, audio: np.ndarray) -> float:
        """Calcula Zero Crossing Rate - indicador de contenido tonal"""
        try:
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            return float(np.mean(zcr))
        except:
            return 0.0
    
    def rank_segments_by_energy(self, segments: List[AudioSegment], top_n: int = 10) -> List[AudioSegment]:
        """Rankea segmentos por energía y devuelve los top N"""

        for segment in segments:
            segment.composite_score = (
                0.7 * segment.rms_score + 
                0.2 * segment.peak_amplitude + 
                0.1 * (segment.spectral_centroid / 5000) 
            )
        
        ranked = sorted(segments, key=lambda x: x.composite_score, reverse=True)
        return ranked[:top_n]