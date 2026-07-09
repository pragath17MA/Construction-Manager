import React, { useEffect, useState, useRef } from 'react';
import { 
  createChatSession, listChatSessions, getChatSession, 
  deleteChatSession, sendChatMessage, sendAudioChatMessage, sendImageChatMessage 
} from '../services/chat';
import { getProjects } from '../services/projects';
import { 
  MessageSquare, Trash2, Send, Mic, MicOff, Image, Plus, 
  Activity, Sparkles, RefreshCw, FileText, AlertTriangle, 
  Clock, Paperclip, CheckCircle, Loader, User, Eye
} from 'lucide-react';

const AIChat = () => {
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  
  // Message inputs
  const [query, setQuery] = useState('');
  const [sending, setSending] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  // Audio Recording States
  const [recording, setRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  // Session creator form modal
  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [newChatProject, setNewChatProject] = useState('');
  const [newChatName, setNewChatName] = useState('');

  const chatEndRef = useRef(null);

  const initData = async () => {
    try {
      setLoading(true);
      const response = await getProjects();
      setProjects(response.items || []);

      const sessList = await listChatSessions();
      setSessions(sessList);
      
      if (sessList.length > 0) {
        handleSelectSession(sessList[0].id);
      }
    } catch (err) {
      console.error("AIChat initialization error: ", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initData();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSelectSession = async (sessionId) => {
    try {
      const details = await getChatSession(sessionId);
      setActiveSession(details);
      setMessages(details.messages || []);
    } catch (err) {
      console.error("Failed to load chat history: ", err);
    }
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    try {
      const data = {};
      if (newChatProject) data.project_id = parseInt(newChatProject);
      if (newChatName) data.session_name = newChatName;

      const newSess = await createChatSession(data);
      setSessions([newSess, ...sessions]);
      setActiveSession(newSess);
      setMessages([]);
      setShowNewChatModal(false);
      setNewChatName('');
      setNewChatProject('');
    } catch (err) {
      console.error("Failed to create chat session: ", err);
    }
  };

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation permanently?")) return;
    try {
      await deleteChatSession(sessionId);
      const updated = sessions.filter(s => s.id !== sessionId);
      setSessions(updated);
      if (activeSession?.id === sessionId) {
        if (updated.length > 0) {
          handleSelectSession(updated[0].id);
        } else {
          setActiveSession(null);
          setMessages([]);
        }
      }
    } catch (err) {
      console.error("Failed to delete chat session: ", err);
    }
  };

  // Submit Text Query
  const handleSendText = async (e) => {
    e.preventDefault();
    if (!query.trim() && !imageFile) return;
    if (!activeSession) return;

    try {
      setSending(true);
      const userText = query;
      setQuery('');

      // Add user message locally for responsive UX
      const tempUserMsg = {
        id: Date.now(),
        sender: 'user',
        message_text: userText || "Uploaded site photo",
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, tempUserMsg]);

      let reply;
      if (imageFile) {
        reply = await sendImageChatMessage(activeSession.id, userText || "Analyze this site image and identify hazards.", imageFile);
        // Clear image attachment preview
        setImageFile(null);
        setImagePreview(null);
      } else {
        reply = await sendChatMessage(activeSession.id, { message_text: userText });
      }

      setMessages(prev => [...prev, reply]);
    } catch (err) {
      console.error("Send text chat failed: ", err);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        message_text: "⚠️ I ran into an error processing your query. Please check Groq API configuration details.",
        created_at: new Date().toISOString()
      }]);
    } finally {
      setSending(false);
    }
  };

  // Image Selection Handler
  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // Mic Audio Recording
  const startRecording = async () => {
    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        if (audioChunksRef.current.length === 0) return;
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        
        // Process audio upload query
        try {
          setSending(true);
          const tempUserMsg = {
            id: Date.now(),
            sender: 'user',
            message_text: "🎤 [Voice Input Command]",
            created_at: new Date().toISOString()
          };
          setMessages(prev => [...prev, tempUserMsg]);

          const reply = await sendAudioChatMessage(activeSession.id, audioBlob);
          setMessages(prev => [...prev, reply]);
        } catch (err) {
          console.error("Failed to parse mic command: ", err);
          setMessages(prev => [...prev, {
            id: Date.now() + 1,
            sender: 'assistant',
            message_text: "⚠️ Failed to transcribe or execute your voice command.",
            created_at: new Date().toISOString()
          }]);
        } finally {
          setSending(false);
        }
      };

      mediaRecorder.start();
      setRecording(true);
      setRecordDuration(0);
      timerRef.current = setInterval(() => {
        setRecordDuration(prev => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Microphone device allocation failed: ", err);
      alert("Microphone device permissions rejected or unavailable.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
      setRecording(false);
      clearInterval(timerRef.current);
    }
  };

  // Clean helper to parse basic markdown bullet lines in response text
  const renderMessageContent = (text) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      if (line.startsWith('# ')) {
        return <h1 key={idx} className="text-xl font-extrabold text-white mt-4 mb-2">{line.replace('# ', '')}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={idx} className="text-lg font-bold text-white mt-3 mb-1.5">{line.replace('## ', '')}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={idx} className="text-sm font-bold text-indigo-300 mt-2 mb-1">{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return <li key={idx} className="list-disc ml-5 text-xs text-slate-300 mb-1">{line.substring(2)}</li>;
      }
      return <p key={idx} className="text-xs leading-relaxed text-slate-200 mb-1">{line}</p>;
    });
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* 1. Left Sidebar Conversations */}
      <div className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-400 animate-pulse" />
            <span className="font-bold text-white tracking-wide">RAG Chat Cockpit</span>
          </div>
          <button 
            onClick={() => setShowNewChatModal(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white p-2 rounded-lg transition"
            title="Start New Conversation"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {sessions.length > 0 ? (
            sessions.map((s) => {
              const active = activeSession?.id === s.id;
              return (
                <div
                  key={s.id}
                  onClick={() => handleSelectSession(s.id)}
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition ${
                    active 
                      ? 'bg-indigo-650 text-white font-semibold' 
                      : 'bg-slate-850 border border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2 overflow-hidden mr-2">
                    <MessageSquare className="h-4.5 w-4.5 flex-shrink-0" />
                    <span className="text-xs truncate">{s.session_name}</span>
                  </div>
                  <button 
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-700/50"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })
          ) : (
            <div className="text-center text-slate-500 text-xs py-8">
              No conversations started. Click the '+' button to begin.
            </div>
          )}
        </div>
      </div>

      {/* 2. Main Chat Thread */}
      <div className="flex-1 flex flex-col bg-slate-950">
        {activeSession ? (
          <>
            {/* Header info */}
            <div className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-white">{activeSession.session_name}</h2>
                <div className="flex items-center gap-1.5 text-slate-400 text-xxs mt-0.5">
                  <Clock className="h-3.5 w-3.5" />
                  Created: {new Date(activeSession.created_at).toLocaleString()}
                </div>
              </div>
            </div>

            {/* Message window */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.length > 0 ? (
                messages.map((m) => {
                  const isUser = m.sender === 'user';
                  return (
                    <div key={m.id} className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
                      {!isUser && (
                        <div className="h-8 w-8 rounded-full bg-indigo-650 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                          AI
                        </div>
                      )}
                      <div className={`max-w-xl rounded-xl p-4 text-slate-200 border ${
                        isUser 
                          ? 'bg-indigo-600/10 border-indigo-500/30' 
                          : 'bg-slate-900 border-slate-800 shadow-md shadow-slate-950/20'
                      }`}>
                        <div className="flex items-center justify-between text-xxs text-slate-500 mb-2 border-b border-slate-800/40 pb-1">
                          <span>{isUser ? 'You' : 'APEXBuild Assistant'}</span>
                          <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <div className="space-y-1">{renderMessageContent(m.message_text)}</div>
                      </div>
                      {isUser && (
                        <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 text-xs font-bold flex-shrink-0">
                          <User className="h-4.5 w-4.5" />
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
                  <Sparkles className="h-10 w-10 text-indigo-400 animate-pulse mb-4" />
                  <h3 className="text-sm font-bold text-white">Ask APEXBuild AI</h3>
                  <p className="text-slate-400 text-xs mt-1 leading-relaxed">
                    I am ready to query your database. You can ask about current budgets, material levels, active workers roster, safety warnings, and drawing blueprint specifications.
                  </p>
                </div>
              )}
              {sending && (
                <div className="flex gap-4 justify-start">
                  <div className="h-8 w-8 rounded-full bg-indigo-650 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                    AI
                  </div>
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3">
                    <Loader className="h-4 w-4 animate-spin text-indigo-400" />
                    <span className="text-xs text-slate-400">Assistant is synthesizing answer...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input box */}
            <div className="p-4 bg-slate-900 border-t border-slate-800">
              <form onSubmit={handleSendText} className="relative">
                {/* Image upload preview */}
                {imagePreview && (
                  <div className="mb-3 p-2 bg-slate-850 border border-slate-700 rounded-lg flex items-center justify-between max-w-sm">
                    <div className="flex items-center gap-2">
                      <img src={imagePreview} alt="upload preview" className="h-10 w-10 object-cover rounded" />
                      <span className="text-xxs text-slate-300 truncate max-w-xs">{imageFile.name}</span>
                    </div>
                    <button 
                      type="button"
                      onClick={() => { setImageFile(null); setImagePreview(null); }}
                      className="text-slate-400 hover:text-rose-400 text-xs font-bold"
                    >
                      Remove
                    </button>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  {/* Image Attachment Trigger */}
                  <label className="cursor-pointer bg-slate-800 hover:bg-slate-700 border border-slate-750 p-3 rounded-lg text-slate-400 hover:text-slate-200 transition" title="Attach Site Image">
                    <Image className="h-5 w-5" />
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleImageSelect} 
                      className="hidden" 
                    />
                  </label>

                  {/* Audio Microphone Trigger */}
                  <button
                    type="button"
                    onClick={recording ? stopRecording : startRecording}
                    className={`p-3 rounded-lg border transition ${
                      recording 
                        ? 'bg-rose-600 border-rose-500 text-white animate-pulse' 
                        : 'bg-slate-800 border-slate-750 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
                    }`}
                    title={recording ? `Stop Recording (${recordDuration}s)` : 'Record Voice Command'}
                  >
                    {recording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                  </button>

                  <input
                    type="text"
                    placeholder={recording ? `Recording in progress... (${recordDuration}s)` : "Type project command (e.g. 'What safety issues are active?' or 'Explain drawing reinforcement specs')"}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={recording || sending}
                    className="flex-1 bg-slate-850 border border-slate-750 rounded-lg py-3 px-4 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                  />

                  <button
                    type="submit"
                    disabled={(!query.trim() && !imageFile) || sending || recording}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white p-3 rounded-lg disabled:opacity-50 transition"
                  >
                    <Send className="h-5 w-5" />
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center max-w-md mx-auto">
            <MessageSquare className="h-12 w-12 text-slate-600 mb-4 animate-bounce" />
            <h3 className="text-base font-bold text-white">Select Chat session</h3>
            <p className="text-slate-500 text-xs mt-1">Select an active conversation on the left, or create a new conversation thread using project scoping context details.</p>
            <button 
              onClick={() => setShowNewChatModal(true)}
              className="mt-4 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-xs font-semibold shadow"
            >
              Start Conversation
            </button>
          </div>
        )}
      </div>

      {/* 3. New Chat Form Modal */}
      {showNewChatModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-sm w-full">
            <h3 className="text-sm font-bold text-white mb-4">New Conversational Thread</h3>
            <form onSubmit={handleCreateSession} className="space-y-4">
              <div>
                <label className="block text-xxs font-bold text-slate-400 uppercase mb-2">Scope Project context (Optional)</label>
                <select
                  value={newChatProject}
                  onChange={(e) => setNewChatProject(e.target.value)}
                  className="w-full bg-slate-850 border border-slate-700 rounded-lg py-2 px-3 text-slate-200 text-xs focus:outline-none"
                >
                  <option value="">No specific project context</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.project_name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xxs font-bold text-slate-400 uppercase mb-2">Conversation Topic Name</label>
                <input
                  type="text"
                  placeholder="e.g. Budget Audit"
                  value={newChatName}
                  onChange={(e) => setNewChatName(e.target.value)}
                  className="w-full bg-slate-850 border border-slate-700 rounded-lg py-2 px-3 text-slate-200 text-xs focus:outline-none"
                />
              </div>

              <div className="flex gap-2 justify-end mt-6">
                <button
                  type="button"
                  onClick={() => setShowNewChatModal(false)}
                  className="bg-slate-800 text-slate-400 px-4 py-2 rounded-lg text-xs hover:bg-slate-750 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-xs font-semibold transition"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIChat;
