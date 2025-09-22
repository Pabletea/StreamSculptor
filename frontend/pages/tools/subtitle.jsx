import { useState } from "react";
import axios from "axios";
import Layout from "../../components/Layout";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function Subtitle(){
    const [sourceUrl, setSourceUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const generateSubtitles = async () => {
        if(!sourceUrl.trim()){
            setError('Please enter a valid URL');
        }

        setLoading(true);
        setError(null);
        setResult(null);
        
        try{
            const response = await axios.post(`${API_BASE}/subtitles`, { source_url : sourceUrl});
            setResult(response.data);
        }catch(error){
            setError(error.response?.data?.detail || 'Subtitle generation failer');
        }finally{
            setLoading(false);
        }
    };
  return (
    <Layout>
      <div className="min-h-screen bg-background font-sans">
        <div className="container mx-auto px-4 py-16">
          <div className="text-left mb-12">
            <h1 className="text-5xl font-extrabold text-text-main">Subtitle Video</h1>
            <p className="text-xl text-text-secondary mt-2">Create subtitles for your videos automatically.</p>
          </div>

          <div className="max-w-3xl mx-auto bg-surface rounded-2xl shadow-xl p-8 border border-secondary">
            <h2 className="text-2xl font-bold text-text-main mb-6">Enter Video URL</h2>

            <div className="space-y-4 mb-6">
              <input
                type="text"
                placeholder="Paste a YouTube or Twitch URL..."
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                className="w-full px-5 py-4 bg-background border border-secondary rounded-lg text-text-main placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={loading}
              />
              <button
                onClick={generateSubtitles}
                disabled={loading || !sourceUrl.trim()}
                className="w-full py-4 bg-primary hover:bg-primary-hover text-white font-semibold rounded-lg transition-all duration-300 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? 'Processing...' : '💬 Generate Subtitles'}
              </button>
            </div>

            {result && (
              <div className="mt-6 p-4 bg-background rounded-lg border border-secondary">
                <h3 className="text-md font-semibold text-text-main mb-2">Subtitles File:</h3>
                <a
                  href={result.file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary underline"
                >
                  Download .srt
                </a>
              </div>
            )}

            {error && (
              <div className="mt-6 p-4 bg-red-900/50 border border-red-500/50 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
