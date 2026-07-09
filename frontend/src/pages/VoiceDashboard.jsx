import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProject } from '../services/projects';
import { submitVoiceCommand, getVoiceHistory, getVoiceAudioUrl } from '../services/voice';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  ArrowLeft, Mic, MicOff, Send, Volume2, Play, Square, Loader, 
  CornerDownLeft, MessageSquare, History, VolumeX, AlertCircle
} from 'lucide-react';

const VoiceDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [history, setHistory] = useState([]);
  const [commandText, setCommandText] = useState('');
  
  // Audio Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const recordingTimer = useRef(null);

  // Response / Status State
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [playbackLoading, setPlaybackLoading] = useState(null); // logId being played
  const [error, setError] = useState('');
  
  // Audio playback ref
  const audioRef = useRef(null);
  const [nowPlayingUrl, setNowPlayingUrl] = useState('');

  const loadData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);
      const logs = await getVoiceHistory(projectId);
      setHistory(logs);
    } catch (err) {
      console.error(err);
      setError('Failed to load voice control center.');
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadData();
      setLoading(false);
    };
    init();
  }, [projectId]);

  // Recording Timer
  useEffect(() => {
    if (isRecording) {
      recordingTimer.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } else {
      clearInterval(recordingTimer.current);
      setRecordingDuration(0);
    }
    return () => clearInterval(recordingTimer.current);
  }, [isRecording]);

  const startRecording = async () => {
    setError('');
    setAudioChunks([]);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/wav' });
      
      const chunks = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };
      
      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        await handleSendVoice(null, audioBlob);
        // Stop all tracks in stream to release mic icon in browser
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err) {
      console.error(err);
      setError('Microphone access denied or audio device not found.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const handleSendText = async (e) => {
    e.preventDefault();
    if (!commandText.trim()) return;
    
    const txt = commandText;
    setCommandText('');
    await handleSendVoice(txt, null);
  };

  const handleSendVoice = async (text, audioBlob) => {
    setActionLoading(true);
    setError('');
    try {
      const resp = await submitVoiceCommand(projectId, text, audioBlob);
      
      // Reload logs
      const logs = await getVoiceHistory(projectId);
      setHistory(logs);
      
      // Auto-play synthesized voice response if URL is returned
      if (resp.audio_url) {
        await playSecureAudio(resp.audio_url, 'new');
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to process voice command.');
    } finally {
      setActionLoading(false);
    }
  };

  const playSecureAudio = async (relativeUrl, logId) => {
    setPlaybackLoading(logId);
    try {
      // Fetch audio blob securely via Axios to pass JWT bearer tokens
      const response = await api.get(relativeUrl, { responseType: 'blob' });
      const objectUrl = URL.createObjectURL(response.data);
      
      if (audioRef.current) {
        audioRef.current.pause();
      }
      
      const audio = new Audio(objectUrl);
      audioRef.current = audio;
      setNowPlayingUrl(objectUrl);
      
      audio.onended = () => {
        setPlaybackLoading(null);
        URL.revokeObjectURL(objectUrl);
        setNowPlayingUrl('');
      };
      
      await audio.play();
    } catch (err) {
      console.error('Failed to play voice response securely', err);
      setError('Secure voice playback failed.');
      setPlaybackLoading(null);
    }
  };

  const handleStopPlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setPlaybackLoading(null);
      if (nowPlayingUrl) {
        URL.revokeObjectURL(nowPlayingUrl);
        setNowPlayingUrl('');
      }
    }
  };

  const formatDuration = (sec) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <Loader className="w-10 h-10 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header breadcrumb */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div className="flex items-center space-x-3">
          <Link
            to={`/projects/${projectId}`}
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">AI Voice Command Cockpit</h1>
            <p className="text-xs text-slate-400 mt-1">
              Spoken operations assistant terminal for: <span className="text-slate-200 font-semibold">{project?.project_name}</span>
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-300 text-xs flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Voice Assistant Panel */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Main Control Panel */}
          <div className="glass-panel p-8 rounded-2xl border border-slate-850 flex flex-col items-center justify-center text-center space-y-6 min-h-[350px]">
            {isRecording ? (
              <div className="space-y-6">
                {/* Visual pulse wave */}
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-2.5 h-8 bg-brand-500 rounded-full animate-bounce delay-100"></div>
                  <div className="w-2.5 h-12 bg-brand-400 rounded-full animate-bounce delay-200"></div>
                  <div className="w-2.5 h-16 bg-brand-550 rounded-full animate-bounce delay-350"></div>
                  <div className="w-2.5 h-10 bg-indigo-500 rounded-full animate-bounce delay-150"></div>
                  <div className="w-2.5 h-6 bg-indigo-400 rounded-full animate-bounce delay-75"></div>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-slate-200 font-bold tracking-wide">Assistant is listening...</p>
                  <p className="text-xs text-rose-400 font-medium uppercase tracking-widest">{formatDuration(recordingDuration)}</p>
                </div>
                <button
                  onClick={stopRecording}
                  className="p-5 bg-rose-600 hover:bg-rose-500 border border-rose-700/40 rounded-full text-white shadow-xl shadow-rose-950/40 transition-all transform hover:scale-105 active:scale-95"
                >
                  <Square className="w-6 h-6 fill-current" />
                </button>
              </div>
            ) : actionLoading ? (
              <div className="space-y-4">
                <Loader className="w-12 h-12 animate-spin text-brand-500 mx-auto" />
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-slate-200">Processing Audio Stream...</p>
                  <p className="text-[10px] text-slate-450 uppercase tracking-widest">Whisper Transcription & RAG lookup</p>
                </div>
              </div>
            ) : playbackLoading === 'new' ? (
              <div className="space-y-4">
                <Volume2 className="w-12 h-12 text-brand-400 mx-auto animate-pulse" />
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-slate-200">Reading Response Aloud</p>
                  <button
                    onClick={handleStopPlayback}
                    className="mt-2 inline-flex items-center text-[10px] bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 px-3 py-1 rounded-lg"
                  >
                    <VolumeX className="w-3.5 h-3.5 mr-1" />
                    Stop Voice Playback
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="w-20 h-20 bg-brand-600/10 text-brand-400 rounded-full border border-brand-500/20 flex items-center justify-center mx-auto shadow-inner shadow-brand-900/10">
                  <Mic className="w-9 h-9" />
                </div>
                <div className="space-y-2 max-w-sm">
                  <p className="text-base font-bold text-white">Ask APEXBuild Assistant</p>
                  <p className="text-xs text-slate-450 leading-relaxed">
                    Press the microphone to record a spoken instruction or query. You can ask about budgets, milestones, worker allocations, safety, or risk indexes.
                  </p>
                </div>
                <button
                  onClick={startRecording}
                  className="px-6 py-3 bg-brand-600 hover:bg-brand-550 text-white rounded-xl text-xs font-semibold shadow-lg shadow-brand-950/20 flex items-center transition-all mx-auto"
                >
                  <Mic className="w-4 h-4 mr-2" />
                  Record Command
                </button>
              </div>
            )}
          </div>

          {/* Text Input Option */}
          <form onSubmit={handleSendText} className="glass-panel p-4 rounded-2xl border border-slate-850 flex items-center space-x-3 shadow-md">
            <div className="p-2 bg-slate-900 text-slate-400 rounded-xl border border-slate-800">
              <MessageSquare className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={commandText}
              onChange={(e) => setCommandText(e.target.value)}
              placeholder="Or type your project query here... (e.g. 'What is the budget?')"
              className="bg-transparent border-0 text-slate-205 focus:outline-none focus:ring-0 text-xs flex-1 placeholder:text-slate-500"
              disabled={actionLoading || isRecording}
            />
            <button
              type="submit"
              disabled={!commandText.trim() || actionLoading || isRecording}
              className="p-2.5 bg-brand-600 hover:bg-brand-550 text-white rounded-xl disabled:opacity-50 transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Right Side: Command History Log */}
        <div className="lg:col-span-1 glass-panel p-5 rounded-2xl border border-slate-850 space-y-4 flex flex-col">
          <h3 className="text-xs font-bold text-slate-350 uppercase tracking-wider flex items-center border-b border-slate-800/80 pb-3">
            <History className="w-4 h-4 mr-1.5 text-brand-400" />
            Command History
          </h3>
          <div className="space-y-4 overflow-y-auto max-h-[420px] flex-1 pr-1">
            {history.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-xs italic">
                No commands processed yet.
              </div>
            ) : (
              history.map((log) => {
                const isPlaying = playbackLoading === log.id;
                const url = log.audio_path ? `/api/voice/audio/${log.audio_path.split(/[\\/]/).pop()}` : null;
                
                return (
                  <div key={log.id} className="p-3.5 bg-slate-900/40 border border-slate-800/80 rounded-xl space-y-2 text-xs">
                    <div className="flex justify-between items-start">
                      <span className="text-[9px] text-slate-500 font-semibold">{new Date(log.created_at).toLocaleString()}</span>
                      {url && (
                        isPlaying ? (
                          <button
                            onClick={handleStopPlayback}
                            className="text-rose-400 hover:text-rose-300 font-semibold text-[10px] flex items-center space-x-1"
                          >
                            <Square className="w-3 h-3 fill-current" />
                            <span>Stop</span>
                          </button>
                        ) : (
                          <button
                            onClick={() => playSecureAudio(url, log.id)}
                            className="text-brand-400 hover:text-brand-300 font-semibold text-[10px] flex items-center space-x-1"
                          >
                            <Play className="w-2.5 h-2.5 fill-current" />
                            <span>Speak</span>
                          </button>
                        )
                      )}
                    </div>
                    <div className="space-y-1">
                      <p className="text-slate-400 font-medium"><span className="text-slate-500 font-semibold uppercase text-[9px] mr-1">Query:</span>"{log.command_text}"</p>
                      <p className="text-slate-200 mt-1 leading-relaxed"><span className="text-slate-500 font-semibold uppercase text-[9px] mr-1">Response:</span>{log.response_text}</p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceDashboard;
