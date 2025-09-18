from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GenerateClipsRequest(BaseModel):
    job_id: str
    max_clips: int = 10
    window_size: float = 30.0
    step_size: float = 10.0
    energy_threshold: float = 0.01  # Umbral mínimo de energía

class AudioSegmentModel(BaseModel):
    start_time: float
    end_time: float
    duration: float
    rms_score: float
    peak_amplitude: float
    spectral_centroid: float
    zero_crossing_rate: float
    composite_score: Optional[float] = None

class ClipMetadata(BaseModel):
    clip_index: int
    filename: str
    object_name: str
    start_time: float
    end_time: float
    duration: float
    rms_score: float
    peak_amplitude: float
    composite_score: float
    file_size_mb: float
    has_srt: bool = False
    srt_object: Optional[str] = None

class ClipsResponse(BaseModel):
    job_id: str
    clips_count: int
    clips: List[ClipMetadata]
    generated_at: datetime
    status: str = "completed"

class AudioAnalysisResponse(BaseModel):
    job_id: str
    total_segments: int
    selected_segments: int
    segments: List[AudioSegmentModel]
    analysis_duration: float

class ClipGenerationResponse(BaseModel):
    job_id: str
    clips_generated: int
    clips: List[ClipMetadata]
    srt_files: dict  # {clip_index: srt_object_name}
    total_size_mb: float
    generation_time: float