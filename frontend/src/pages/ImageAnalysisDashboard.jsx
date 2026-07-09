import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProject } from '../services/projects';
import { triggerVisualAudit, getProjectVisualAudits, getAnnotatedImageUrl } from '../services/image_analysis';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  ArrowLeft, ImageIcon, ShieldAlert, Sparkles, RefreshCw, 
  FileText, Loader, CheckCircle2, AlertTriangle, AlertCircle, Play, Info
} from 'lucide-react';

const ImageAnalysisDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [images, setImages] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  
  const [annotatedImgSrc, setAnnotatedImgSrc] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [annotatedLoading, setAnnotatedLoading] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);
      // Sort images by date/uploaded_at descending
      const imgs = proj.images || [];
      setImages(imgs);
      
      const audits = await getProjectVisualAudits(projectId);
      setAnalyses(audits);
      
      // Auto-select the first image if any
      if (imgs.length > 0 && !selectedImage) {
        setSelectedImage(imgs[0]);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to retrieve project site photos.');
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

  // Handle selected image change
  useEffect(() => {
    if (selectedImage) {
      // Find matching analysis
      const analysis = analyses.find(a => a.site_image_id === selectedImage.id);
      setSelectedAnalysis(analysis || null);
      setAnnotatedImgSrc('');
    } else {
      setSelectedAnalysis(null);
      setAnnotatedImgSrc('');
    }
  }, [selectedImage, analyses]);

  // Load annotated image blob securely
  useEffect(() => {
    const loadAnnotatedImage = async () => {
      if (selectedAnalysis) {
        setAnnotatedLoading(true);
        try {
          const url = getAnnotatedImageUrl(selectedAnalysis.id);
          const response = await api.get(url, { responseType: 'blob' });
          const objectUrl = URL.createObjectURL(response.data);
          setAnnotatedImgSrc(objectUrl);
        } catch (err) {
          console.error('Failed to load annotated image securely', err);
          setAnnotatedImgSrc('');
        } finally {
          setAnnotatedLoading(false);
        }
      }
    };
    loadAnnotatedImage();
    
    // Clean up object URL
    return () => {
      if (annotatedImgSrc) {
        URL.revokeObjectURL(annotatedImgSrc);
      }
    };
  }, [selectedAnalysis]);

  const handleRunAudit = async () => {
    if (!selectedImage) return;
    setActionLoading(true);
    setError('');
    try {
      const newAnalysis = await triggerVisualAudit(projectId, selectedImage.id);
      // Reload analyses
      const audits = await getProjectVisualAudits(projectId);
      setAnalyses(audits);
      // Update selected
      setSelectedAnalysis(newAnalysis);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Visual threat detection audit workflow failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const getSafetyIssuesList = (analysis) => {
    if (!analysis || !analysis.safety_issues) return [];
    if (Array.isArray(analysis.safety_issues)) return analysis.safety_issues;
    try {
      const parsed = JSON.parse(analysis.safety_issues);
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch (e) {
      return [analysis.safety_issues];
    }
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <Loader className="w-10 h-10 animate-spin text-brand-500" />
      </div>
    );
  }

  const issues = selectedAnalysis ? getSafetyIssuesList(selectedAnalysis) : [];

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
            <h1 className="text-xl font-bold tracking-tight text-white">AI Site Image Visual Audit</h1>
            <p className="text-xs text-slate-400 mt-1">
              Visual risk recognition and safety gear detection on site photos for: <span className="text-slate-200 font-semibold">{project?.project_name}</span>
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

      {images.length === 0 ? (
        <div className="glass-panel p-12 text-center text-slate-450 border border-slate-850 rounded-2xl space-y-4">
          <ImageIcon className="w-12 h-12 mx-auto text-slate-600" />
          <p className="text-sm">No site images have been uploaded yet for this project.</p>
          <p className="text-xs text-slate-500">Go to the main project page, click on the "Site Images" tab, and upload site photos to analyze.</p>
          <Link
            to={`/projects/${projectId}`}
            className="inline-flex px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold mt-2"
          >
            Go to Project Uploads
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Thumbnails Sidebar */}
          <div className="lg:col-span-1 glass-panel p-4 rounded-2xl border border-slate-850 space-y-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Site Photos</h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {images.map((img) => {
                const isSelected = selectedImage?.id === img.id;
                const hasAnalysis = analyses.some(a => a.site_image_id === img.id);
                return (
                  <button
                    key={img.id}
                    onClick={() => setSelectedImage(img)}
                    className={`w-full text-left p-2.5 rounded-xl border flex items-center space-x-3 transition-all ${
                      isSelected 
                        ? 'bg-slate-850 border-brand-500 shadow-md' 
                        : 'bg-slate-900/40 border-slate-800 hover:bg-slate-850/60'
                    }`}
                  >
                    <div className="w-12 h-12 rounded-lg bg-slate-950 border border-slate-800 overflow-hidden flex-shrink-0 flex items-center justify-center">
                      <ImageIcon className="w-5 h-5 text-slate-500" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-slate-200 truncate">Image ID: {img.id}</p>
                      <p className="text-[10px] text-slate-450 mt-0.5">{new Date(img.capture_date).toLocaleDateString()}</p>
                    </div>
                    {hasAnalysis && (
                      <div className="p-1 bg-brand-500/10 text-brand-400 rounded-full border border-brand-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Main Visual Display */}
          <div className="lg:col-span-3 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Photo Display Panel */}
              <div className="glass-panel p-5 rounded-2xl border border-slate-850 space-y-4">
                <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
                  <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider">Original Site Photo</h4>
                  <span className="text-[10px] text-slate-500">Captured: {selectedImage ? new Date(selectedImage.capture_date).toLocaleDateString() : ''}</span>
                </div>
                <div className="aspect-[4/3] rounded-xl bg-slate-950 border border-slate-850 overflow-hidden relative flex items-center justify-center">
                  {selectedImage ? (
                    <img 
                      src={`${import.meta.env.VITE_API_URL || '/api'}/projects/${projectId}/images/${selectedImage.id}`}
                      alt="Original Site"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = '';
                      }}
                    />
                  ) : (
                    <Loader className="w-8 h-8 animate-spin text-slate-700" />
                  )}
                </div>
              </div>

              {/* Annotated Display Panel */}
              <div className="glass-panel p-5 rounded-2xl border border-slate-850 space-y-4">
                <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
                  <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider">AI Visual Detection</h4>
                  <span className="text-[10px] text-brand-450 font-semibold uppercase">YOLOv8 + CV2 layer</span>
                </div>
                <div className="aspect-[4/3] rounded-xl bg-slate-950 border border-slate-850 overflow-hidden relative flex items-center justify-center">
                  {annotatedLoading ? (
                    <div className="text-center space-y-2">
                      <Loader className="w-8 h-8 animate-spin text-brand-500 mx-auto" />
                      <p className="text-[10px] text-slate-400">Loading audit markup...</p>
                    </div>
                  ) : annotatedImgSrc ? (
                    <img 
                      src={annotatedImgSrc} 
                      alt="AI Detections"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-center p-6 space-y-3">
                      <Sparkles className="w-10 h-10 text-slate-650 mx-auto" />
                      <p className="text-xs text-slate-450 leading-relaxed max-w-xs">
                        {selectedAnalysis 
                          ? "Annotated file rendering failed or permission boundary expired." 
                          : "No visual analysis available for this photo yet."}
                      </p>
                      {!selectedAnalysis && (
                        <button
                          onClick={handleRunAudit}
                          disabled={actionLoading}
                          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl flex items-center shadow-lg transition-all mx-auto disabled:opacity-50"
                        >
                          {actionLoading ? <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Play className="w-3 h-3 mr-1.5 fill-current" />}
                          Run AI Threat Audit
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Analysis Audit Ledger */}
            {selectedAnalysis && (
              <div className="glass-panel p-6 rounded-2xl border border-slate-850 space-y-6">
                
                {/* Metric Summary Widgets */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Construction Stage and progress */}
                  <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3">
                    <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider block">Estimated Stage Completion</span>
                    <div className="flex justify-between items-baseline">
                      <span className="text-lg font-bold text-white">{selectedAnalysis.construction_stage}</span>
                      <span className="text-xs font-bold text-brand-400">{parseFloat(selectedAnalysis.progress_percentage)}%</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-850">
                      <div 
                        className="bg-brand-500 h-full rounded-full transition-all duration-300"
                        style={{ width: `${selectedAnalysis.progress_percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Hazard Severity Summary */}
                  <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 flex flex-col justify-between">
                    <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider block">Safety Threats Detected</span>
                    <div className="flex items-center space-x-2">
                      <span className={`text-2xl font-bold ${issues.length > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {issues.length} Hazards
                      </span>
                      <span className="text-xs text-slate-500">spotted in audit</span>
                    </div>
                    <p className="text-[10px] text-slate-450">
                      Auto-flagged via YOLO visual safety harness and PPE detection ruleset.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Threats/Hazards List */}
                  <div className="space-y-3">
                    <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
                      <ShieldAlert className="w-4 h-4 mr-1.5 text-rose-450" />
                      Visual Alert log
                    </h5>
                    {issues.length === 0 ? (
                      <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl text-xs text-emerald-450 flex items-center">
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        No active safety hazards detected on site. Excellent!
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {issues.map((iss, i) => (
                          <div key={i} className="p-3 bg-rose-500/5 border border-rose-500/10 rounded-xl text-xs text-rose-300 flex items-start">
                            <AlertTriangle className="w-3.5 h-3.5 mr-2 text-rose-400 mt-0.5 flex-shrink-0" />
                            <span>{iss}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Recommendations */}
                  <div className="space-y-3">
                    <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
                      <Info className="w-4 h-4 mr-1.5 text-brand-400" />
                      AI Inspection Insights
                    </h5>
                    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {selectedAnalysis.recommendations || "No recommendations generated."}
                    </div>
                  </div>
                </div>

                {/* Recalculate Trigger */}
                <div className="flex justify-end pt-2 border-t border-slate-800/60">
                  <button
                    onClick={handleRunAudit}
                    disabled={actionLoading}
                    className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-850 text-slate-300 text-xs font-semibold rounded-lg border border-slate-800 flex items-center transition-all disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3 h-3 mr-1.5 ${actionLoading ? 'animate-spin' : ''}`} />
                    Refresh Analysis
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageAnalysisDashboard;
