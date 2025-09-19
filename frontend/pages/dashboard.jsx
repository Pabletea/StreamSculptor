import { useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function Dashboard() {
  const router = useRouter();
  const [jobId, setJobId] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(null);

  const processVideo = async () => {
    if (!sourceUrl.trim()) {
      setError('Please enter a valid URL');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress({ state: 'PENDING', status: 'Initializing...' });
    
    try {
      const response = await axios.post(`${API_BASE}/ingest/process-with-clips`, {
        source_url: sourceUrl, user_id: 1, max_clips: 10
      });
      setResult(response.data);
      setJobId(response.data.job_id);
      setTaskId(response.data.task_id);
      startProgressPolling(response.data.task_id, response.data.job_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Processing failed to start');
      setLoading(false);
      setProgress(null);
    }
  };

  const startProgressPolling = (currentTaskId, currentJobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE}/task/${currentTaskId}`);
        const taskData = response.data;
        setProgress(taskData);
        
        if (taskData.state === 'SUCCESS') {
          clearInterval(pollInterval);
          setLoading(false);
          setProgress({ ...taskData, status: 'Completed! Redirecting...' });
          setTimeout(() => router.push(`/clips/${currentJobId}`), 2000);
        } else if (taskData.state === 'FAILURE') {
          clearInterval(pollInterval);
          setLoading(false);
          setError(taskData.error || 'Processing failed');
        }
      } catch (err) {
        console.error('Progress polling error:', err);
        clearInterval(pollInterval);
        setLoading(false);
        setError('Failed to get task status.');
      }
    }, 2000);
  };

  const viewClips = () => {
    if (jobId.trim()) router.push(`/clips/${jobId}`);
  };



  return (
    <Layout>
      <div className="min-h-screen bg-background font-sans">
        <div className="container mx-auto px-4 py-16">
          {/* Header */}
          <div className="text-left mb-12">
            <h1 className="text-5xl font-extrabold text-text-main">
              Stream<span className="text-primary">Sculptor</span>
            </h1>
            <p className="text-xl text-text-secondary mt-2">
              AI-powered video clipping. Effortless highlights.
            </p>
          </div>

          {/* Main Card */}
          <div className="max-w-3xl mx-auto bg-surface rounded-2xl shadow-xl p-8 border border-secondary">
            <h2 className="text-2xl font-bold text-text-main mb-6">
              Generate Clips from URL
            </h2>
            
            <div className="space-y-4 mb-6">
              <input
                type="text"
                placeholder="Paste a YouTube or Twitch URL here..."
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                className="w-full px-5 py-4 bg-background border border-secondary rounded-lg text-text-main placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-300 shadow-sm focus:shadow-glow"
                disabled={loading}
              />
              <button
                onClick={processVideo}
                disabled={loading || !sourceUrl.trim()}
                className="w-full py-4 bg-primary hover:bg-primary-hover text-white font-semibold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Processing...</span>
                  </>
                ) : (
                  '🚀 Generate Clips'
                )}
              </button>
            </div>

            {/* Progress / Status Display */}
            {progress && (
              <div className="mt-6 p-4 bg-background rounded-lg border border-secondary">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-md font-semibold text-text-main">
                    Status: <span className="text-primary">{progress.state}</span>
                  </h3>
                  {progress.state === 'SUCCESS' && <span className="text-green-400">✅</span>}
                  {progress.state === 'FAILURE' && <span className="text-red-400">❌</span>}
                </div>
                <p className="text-sm text-text-secondary mb-3">{progress.status}</p>
                <div className="w-full bg-secondary rounded-full h-2.5">
                  <div className={`h-2.5 rounded-full ${progress.state === 'SUCCESS' ? 'bg-green-500' : 'bg-primary'} transition-all duration-500`} style={{ width: progress.state === 'SUCCESS' ? '100%' : '50%' }}></div>
                </div>
              </div>
            )}

            {error && (
              <div className="mt-6 p-4 bg-red-900/50 border border-red-500/50 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Quick Access & Features */}
          <div className="max-w-3xl mx-auto mt-8 grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Quick Access */}
              <div className="bg-surface rounded-2xl shadow-xl p-6 border border-secondary">
                  <h3 className="font-bold text-text-main mb-4">View Existing Job</h3>
                  <div className="flex gap-2">
                      <input
                          type="text"
                          placeholder="Enter Job ID"
                          value={jobId}
                          onChange={(e) => setJobId(e.target.value)}
                          className="w-full px-4 py-2 bg-background border border-secondary rounded-lg text-text-main placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                      <button
                          onClick={viewClips}
                          disabled={!jobId.trim()}
                          className="px-6 py-2 bg-secondary hover:bg-primary/50 text-text-main font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                          View
                      </button>
                  </div>
              </div>

              {/* Features */}
              <div className="bg-surface rounded-2xl shadow-xl p-6 border border-secondary">
                  <h3 className="font-bold text-text-main mb-4">How It Works</h3>
                  <div className="space-y-3">
                      {[
                          { icon: '📥', title: 'Download & Transcribe' },
                          { icon: '✨', title: 'AI-Powered Analysis' },
                          { icon: '✂️', title: 'Clip Generation' },
                      ].map(feature => (
                          <div key={feature.title} className="flex items-center gap-4">
                              <div className="text-xl">{feature.icon}</div>
                              <span className="text-text-secondary">{feature.title}</span>
                          </div>
                      ))}
                  </div>
              </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}