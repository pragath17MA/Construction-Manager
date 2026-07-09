import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  getProjectDocuments, uploadDocument, 
  queryDrawing, getDocument 
} from '../services/documents';
import { getProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { 
  ArrowLeft, Search, UploadCloud, FileText, Sparkles, 
  RefreshCw, Layers, ShieldCheck, AlertCircle, Bookmark, 
  ExternalLink, Loader, CornerDownRight, CheckCircle2 
} from 'lucide-react';

const DocumentDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  
  // States
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Upload and Query form state
  const [uploadFile, setUploadFile] = useState(null);
  const [queryText, setQueryText] = useState('');
  const [queryResponse, setQueryResponse] = useState(null);

  const loadData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);
      const docs = await getProjectDocuments(projectId);
      setDocuments(docs);
    } catch (err) {
      console.error(err);
      setError('Failed to load project drawings list.');
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

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploadLoading(true);
    setError('');
    try {
      await uploadDocument(projectId, uploadFile);
      setUploadFile(null);
      await loadData();
    } catch (err) {
      console.error(err);
      setError('Document specification upload failed.');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    setSearchLoading(true);
    setQueryResponse(null);
    try {
      const resp = await queryDrawing(projectId, queryText);
      setQueryResponse(resp);
    } catch (err) {
      console.error(err);
      setError('Semantic query execution failed.');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSelectDoc = async (docId) => {
    setError('');
    try {
      const detailed = await getDocument(docId);
      setSelectedDoc(detailed);
    } catch (err) {
      console.error(err);
      setError('Could not retrieve drawing segment chunks.');
    }
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <Loader className="w-10 h-10 animate-spin text-brand-500" />
      </div>
    );
  }

  const canModify = user?.role === 'Admin' || user?.role === 'Project Manager';

  return (
    <div className="space-y-6">
      {/* Header crumb */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div className="flex items-center space-x-3">
          <Link
            to={`/projects/${projectId}`}
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">AI Construction Drawing RAG Cockpit</h1>
            <p className="text-xs text-slate-400 mt-1">
              Semantic drawing lookup and Q&A engine: <span className="text-slate-205 font-semibold">{project?.project_name}</span>
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-250 text-xs">
          {error}
        </div>
      )}

      {/* RAG SEMANTIC SEARCH BAR */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-850 space-y-4 shadow-xl">
        <div className="flex items-center space-x-2 text-indigo-400">
          <Sparkles className="w-5 h-5 animate-pulse" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Semantic Query Drawing Library</h3>
        </div>
        
        <form onSubmit={handleQuerySubmit} className="flex gap-3">
          <input
            type="text"
            required
            placeholder="Ask anything: 'What is the concrete specification?' or 'Check plumber requirements...'"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            className="block flex-1 px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-all"
          />
          <button
            type="submit"
            disabled={searchLoading}
            className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl flex items-center transition-all disabled:opacity-50"
          >
            {searchLoading ? <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Search className="w-3.5 h-3.5 mr-1.5" />}
            Ask AI
          </button>
        </form>

        {/* Query output RAG card */}
        {queryResponse && (
          <div className="mt-4 p-4 bg-slate-900/60 border border-slate-850 rounded-xl space-y-4 animate-fade-in shadow-inner">
            
            {/* Answer */}
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-brand-400 uppercase tracking-wider block">AI Formulated Answer</span>
              <p className="text-xs text-slate-205 leading-relaxed">
                {queryResponse.answer}
              </p>
            </div>

            {/* Recommendations */}
            {queryResponse.recommendations?.length > 0 && (
              <div className="space-y-1.5 border-t border-slate-800/80 pt-3">
                <span className="text-[10px] font-bold text-emerald-450 uppercase tracking-wider block">AI Safety & Compliance Recommendations</span>
                <ul className="space-y-1 pl-1">
                  {queryResponse.recommendations.map((rec, rIdx) => (
                    <li key={rIdx} className="text-xs text-slate-350 flex items-start">
                      <CornerDownRight className="w-3.5 h-3.5 mr-2 text-slate-500 shrink-0 mt-0.5" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Sources referenced */}
            {queryResponse.sources?.length > 0 && (
              <div className="space-y-1.5 border-t border-slate-800/80 pt-3">
                <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider block">Sources Referenced</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1.5">
                  {queryResponse.sources.map((src, sIdx) => (
                    <div key={sIdx} className="p-2.5 bg-slate-950/60 border border-slate-900 rounded-lg flex items-center justify-between text-[10px]">
                      <div className="space-y-0.5">
                        <span className="font-semibold text-slate-300 block truncate max-w-[180px]">{src.document_name}</span>
                        <span className="text-slate-500">Page {src.page_number} • Match Score: {(src.similarity_score * 100).toFixed(0)}%</span>
                      </div>
                      <Bookmark className="w-3.5 h-3.5 text-brand-450 opacity-70" />
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}
      </div>

      {/* DRAWING LIBRARY AND VIEWER ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Drawing registry library */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-850 space-y-4 shadow-lg">
          <div className="flex justify-between items-center">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Drawing Library</h3>
            <span className="text-[10px] text-slate-500">{documents.length} docs registered</span>
          </div>

          {canModify && (
            <form onSubmit={handleUploadSubmit} className="p-4 bg-slate-905 border border-dashed border-slate-800 rounded-xl flex flex-col items-center space-y-3">
              <input
                type="file"
                accept=".pdf"
                required
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="hidden"
                id="rag-file-picker"
              />
              <label 
                htmlFor="rag-file-picker"
                className="cursor-pointer text-center flex flex-col items-center space-y-1.5 text-slate-400 hover:text-white transition-all"
              >
                <UploadCloud className="w-8 h-8 text-brand-400 animate-bounce" />
                <span className="text-xs font-semibold block">{uploadFile ? uploadFile.name : 'Select Drawing PDF'}</span>
                <span className="text-[9px] text-slate-550">Only PDF files up to 10MB</span>
              </label>
              {uploadFile && (
                <button
                  type="submit"
                  disabled={uploadLoading}
                  className="w-full py-1.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-[10px] rounded-lg transition-all disabled:opacity-50"
                >
                  {uploadLoading ? 'Indexing Chunks...' : 'Confirm Upload'}
                </button>
              )}
            </form>
          )}

          <div className="space-y-2 max-h-80 overflow-y-auto">
            {documents.length === 0 ? (
              <p className="text-xs text-slate-500 italic text-center py-4">No drawings uploaded.</p>
            ) : (
              documents.map((doc) => (
                <div 
                  key={doc.id}
                  onClick={() => handleSelectDoc(doc.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                    selectedDoc?.id === doc.id 
                      ? 'bg-brand-600/10 border-brand-500/30 text-white' 
                      : 'bg-slate-900/40 border-slate-850 hover:bg-slate-800 text-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                    <div className="min-w-0">
                      <span className="text-xs font-bold block truncate">{doc.file_name}</span>
                      <span className="text-[9px] text-slate-500">{doc.total_chunks} segments indexed</span>
                    </div>
                  </div>
                  
                  {/* Status Indicator */}
                  <span className={`px-2 py-0.5 text-[8px] font-bold rounded-full ${
                    doc.status === 'Completed' ? 'bg-emerald-500/10 text-emerald-400' :
                    doc.status === 'Processing' ? 'bg-indigo-500/10 text-indigo-400 animate-pulse' :
                    doc.status === 'Error' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {doc.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Extracted text chunk viewer */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col justify-between shadow-lg h-96">
          <div className="space-y-1 pb-3 border-b border-slate-800/80">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Drawing Segment Chunks</h3>
            <span className="text-[9px] text-slate-500 block">
              {selectedDoc ? `Document: ${selectedDoc.file_name} (${selectedDoc.total_chunks} total chunks)` : 'Select a drawing to view segment records'}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto mt-4 space-y-3 pr-2 scrollbar-thin">
            {!selectedDoc ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500 italic">
                Choose a drawing from library ledger to view chunk details.
              </div>
            ) : selectedDoc.chunks?.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500 italic">
                Drawing is still processing. Please refresh.
              </div>
            ) : (
              selectedDoc.chunks.map((chunk) => (
                <div key={chunk.id} className="p-3 bg-slate-900/60 border border-slate-900 rounded-xl space-y-1.5">
                  <div className="flex justify-between items-center text-[9px] text-slate-500 border-b border-slate-900 pb-1">
                    <span>Segment #{chunk.chunk_index + 1}</span>
                    <span>Page {chunk.page_number}</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap">
                    {chunk.chunk_text}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default DocumentDashboard;
