import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

// Helper para el color de la puntuación
const getScoreColor = (score) => {
  if (score > 0.8) return 'from-green-400 to-teal-400';
  if (score > 0.5) return 'from-yellow-400 to-orange-400';
  return 'from-gray-400 to-gray-500';
};

const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export default function ClipsPage() {
  const router = useRouter();
  const { jobId } = router.query;
  
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedClip, setSelectedClip] = useState(null);

  useEffect(() => {
    if (jobId) {
      fetchClips();
    } else {
        setLoading(false);
    }
  }, [jobId]);

  const fetchClips = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/clips/${jobId}`);
      const fetchedClips = response.data.clips || [];
      setClips(fetchedClips);
      if (fetchedClips.length > 0) {
        setSelectedClip(fetchedClips[0]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load clips');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><p>Loading clips...</p></div>;
  if (error) return <div className="min-h-screen flex items-center justify-center"><p className="text-red-400">{error}</p></div>;

  return (
    <div className="min-h-screen bg-background font-sans">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-10">
            <button onClick={() => router.push('/dashboard')} className="text-sm text-primary hover:underline mb-4">
                ← Back to Dashboard
            </button>
            <h1 className="text-4xl font-extrabold text-text-main">Generated Clips</h1>
            <p className="text-text-secondary">
                Job ID: <span className="font-mono text-primary/80">{jobId}</span>
            </p>
        </div>

        {clips.length === 0 ? (
            <div className="text-center py-20 bg-surface rounded-lg border border-secondary">
                <h2 className="text-2xl font-bold text-text-main">No Clips Found</h2>
                <p className="text-text-secondary mt-2">Processing may still be in progress or no suitable clips were generated.</p>
            </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Clips Grid */}
            <div className="lg:col-span-2">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {clips.map((clip) => (
                  <div 
                    key={clip.clip_index}
                    onClick={() => setSelectedClip(clip)}
                    className={`bg-surface rounded-lg border transition-all duration-300 cursor-pointer ${selectedClip?.clip_index === clip.clip_index ? 'border-primary shadow-glow' : 'border-secondary hover:border-primary/50'}`}
                  >
                    <div className="relative h-40 bg-background rounded-t-lg flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-secondary" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                      </svg>
                      <span className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
                        {formatTime(clip.start_time)} - {formatTime(clip.end_time)}
                      </span>
                    </div>
                    <div className="p-4">
                      <div className="flex justify-between items-center">
                        <h3 className="font-bold text-text-main">Clip {clip.clip_index + 1}</h3>
                        <div className={`text-xs font-bold text-white px-2 py-1 rounded-full bg-gradient-to-r ${getScoreColor(clip.composite_score)}`}>
                            ⚡ {clip.composite_score.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Clip Details */}
            {selectedClip && (
              <div className="lg:col-span-1">
                <div className="sticky top-12 bg-surface p-6 rounded-2xl border border-secondary">
                  <h2 className="text-2xl font-bold text-text-main mb-4">Clip {selectedClip.clip_index + 1}</h2>
                  
                  {/* Mock Video Player */}
                  <div className="aspect-video bg-black rounded-lg mb-4 flex items-center justify-center">
                    <p className="text-text-secondary">Video Preview</p>
                  </div>

                  {/* Stats */}
                  <div className="space-y-3 text-sm mb-6">
                    <div className="flex justify-between"><span className="text-text-secondary">Duration:</span> <span className="font-medium text-text-main">{selectedClip.duration}s</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Size:</span> <span className="font-medium text-text-main">{selectedClip.file_size_mb.toFixed(1)} MB</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Score:</span> <span className="font-medium text-text-main">{selectedClip.composite_score.toFixed(3)}</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Subtitles:</span> <span className={`font-medium ${selectedClip.has_srt ? 'text-green-400' : 'text-red-400'}`}>{selectedClip.has_srt ? 'Available' : 'N/A'}</span></div>
                  </div>

                  {/* Actions */}
                  <div className="space-y-3">
                    <button onClick={() => window.open(`${API_BASE}/clips/${jobId}/download/${selectedClip.clip_index}`, '_blank')} className="w-full text-center py-3 bg-primary hover:bg-primary-hover text-white font-semibold rounded-lg transition-all duration-300">
                      Download Clip (MP4)
                    </button>
                    {selectedClip.has_srt && (
                      <button onClick={() => window.open(`${API_BASE}/clips/${jobId}/srt/${selectedClip.clip_index}`, '_blank')} className="w-full text-center py-3 bg-secondary hover:bg-primary/50 text-text-main font-semibold rounded-lg transition-colors">
                        Download Subtitles (SRT)
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            {/* Bulk Actions (Moved outside the main grid) */}
            <div className="lg:col-span-3 mt-12">
              <div className="bg-surface p-6 rounded-2xl border border-secondary">
                <h2 className="text-xl font-bold text-text-main mb-4">Bulk Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button onClick={() => window.open(`${API_BASE}/download/${jobId}/clips_metadata`, '_blank')} className="py-3 bg-secondary hover:bg-primary/50 text-text-main font-semibold rounded-lg transition-colors">
                    Download Metadata
                  </button>
                  <button onClick={() => window.open(`${API_BASE}/transcript/${jobId}`, '_blank')} className="py-3 bg-secondary hover:bg-primary/50 text-text-main font-semibold rounded-lg transition-colors">
                    View Full Transcript
                  </button>
                   <button onClick={() => clips.forEach(c => setTimeout(() => window.open(`${API_BASE}/clips/${jobId}/download/${c.clip_index}`, '_blank'), c.clip_index * 300))} className="py-3 bg-primary/80 hover:bg-primary text-white font-semibold rounded-lg transition-colors">
                    Download All Clips
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}