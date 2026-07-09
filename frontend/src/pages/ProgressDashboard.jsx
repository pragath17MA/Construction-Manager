import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  getProgressSummary, submitDailyProgress, 
  createOrUpdateMilestone, downloadProgressReport 
} from '../services/progress';
import { getProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { Line, Bar } from 'react-chartjs-2';
import { 
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, 
  LineElement, Title, Tooltip, Legend, BarElement 
} from 'chart.js';
import { 
  ArrowLeft, CheckCircle2, AlertTriangle, Sparkles, RefreshCw, 
  FileText, FileSpreadsheet, Plus, UploadCloud, User, Clock, 
  Layers, IndianRupee, Activity, Calendar, FileImage, Loader
} from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement);

const ProgressDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  // Daily Log Form State
  const [logForm, setLogForm] = useState({
    update_text: '',
    log_date: new Date().toISOString().split('T')[0]
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [logError, setLogError] = useState('');
  const [logSuccess, setLogSuccess] = useState('');

  // Milestone Form State
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);
  const [milestoneForm, setMilestoneForm] = useState({
    milestone_name: '',
    description: '',
    planned_end_date: new Date().toISOString().split('T')[0],
    completion_percentage: '0',
    status: 'Planning'
  });

  const loadData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);
      
      const sum = await getProgressSummary(projectId);
      setSummary(sum);
    } catch (err) {
      console.error(err);
      setError('Failed to retrieve project progress details.');
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

  const handleRecalculate = async () => {
    setActionLoading(true);
    setError('');
    try {
      await loadData();
    } catch (err) {
      console.error(err);
      setError('AI progress re-calculation failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleLogSubmit = async (e) => {
    e.preventDefault();
    setLogError('');
    setLogSuccess('');
    if (!logForm.update_text.trim()) {
      setLogError('Update logs message is required.');
      return;
    }

    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('log_date', logForm.log_date);
    formData.append('update_text', logForm.update_text);
    if (selectedFile) {
      formData.append('file', selectedFile);
    }

    setActionLoading(true);
    try {
      await submitDailyProgress(formData);
      setLogForm({ update_text: '', log_date: new Date().toISOString().split('T')[0] });
      setSelectedFile(null);
      setLogSuccess('Daily progress log registered successfully.');
      await loadData();
    } catch (err) {
      console.error(err);
      setLogError('Failed to file progress update log.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleMilestoneSubmit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await createOrUpdateMilestone({
        project_id: parseInt(projectId),
        milestone_name: milestoneForm.milestone_name,
        description: milestoneForm.description,
        planned_end_date: milestoneForm.planned_end_date,
        completion_percentage: parseFloat(milestoneForm.completion_percentage),
        status: milestoneForm.status
      });
      setShowMilestoneModal(false);
      setMilestoneForm({ milestone_name: '', description: '', planned_end_date: new Date().toISOString().split('T')[0], completion_percentage: '0', status: 'Planning' });
      await loadData();
    } catch (err) {
      console.error(err);
      alert('Failed to save milestone log.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownload = async (format) => {
    try {
      await downloadProgressReport(projectId, format, `progress_report_project_${projectId}`);
    } catch (err) {
      console.error(err);
      alert('Report download execution failed.');
    }
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <Loader className="w-10 h-10 animate-spin text-brand-500" />
      </div>
    );
  }

  const milestones = summary?.milestones || [];
  const latestLogs = summary?.latest_logs || [];
  const reports = summary?.reports || [];
  const activeReport = reports[0]; // Current daily cached snapshot

  const canModify = user?.role === 'Admin' || user?.role === 'Project Manager';

  // Chart configs: Budget Burn-down
  const budgetBurnData = {
    labels: ['Start', 'Current', 'Forecasted Target'],
    datasets: [
      {
        label: 'Cumulative Cost Burn (₹)',
        data: [0, parseFloat(summary?.budget_spent || 0), parseFloat(summary?.budget_spent || 0) * 1.1],
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.2,
        fill: true
      },
      {
        label: 'Budget Ceiling line',
        data: [parseFloat(summary?.budget_limit || 0), parseFloat(summary?.budget_limit || 0), parseFloat(summary?.budget_limit || 0)],
        borderColor: '#10b981',
        borderDash: [5, 5],
        fill: false
      }
    ]
  };

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
            <h1 className="text-xl font-bold tracking-tight text-white">AI Progress & Scheduling Center</h1>
            <p className="text-xs text-slate-400 mt-1">
              Live progression dashboards for: <span className="text-slate-200 font-semibold">{project?.project_name}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleDownload('pdf')}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-850 text-slate-200 font-semibold text-xs rounded-xl border border-slate-800 flex items-center transition-all"
          >
            <FileText className="w-3.5 h-3.5 mr-1.5" />
            Download PDF Report
          </button>
          <button
            onClick={() => handleDownload('excel')}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-850 text-slate-200 font-semibold text-xs rounded-xl border border-slate-800 flex items-center transition-all"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5" />
            Export Excel Sheet
          </button>
          {canModify && (
            <button
              onClick={() => setShowMilestoneModal(true)}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-850 text-slate-200 font-semibold text-xs rounded-xl border border-slate-800 flex items-center transition-all"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Add Milestone Task
            </button>
          )}
          <button
            onClick={handleRecalculate}
            disabled={actionLoading}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl flex items-center shadow-lg transition-all disabled:opacity-50"
          >
            {actionLoading ? <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 mr-1.5 animate-pulse" />}
            Refresh Roster Analytics
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-250 text-xs">
          {error}
        </div>
      )}

      {/* KPI SUMMARIES */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Overall Progress</span>
          <span className="text-lg font-extrabold text-white mt-1 flex items-center">
            <Activity className="w-4.5 h-4.5 mr-1.5 text-indigo-400" />
            {parseFloat(summary?.overall_completion || 0.0).toFixed(1)}% Completed
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Timeline Variance</span>
          <span className={`text-lg font-extrabold mt-1 flex items-center ${
            summary?.planned_vs_actual_variance > 10 ? 'text-amber-500' : 'text-emerald-400'
          }`}>
            <Clock className="w-4.5 h-4.5 mr-1.5" />
            {summary?.planned_vs_actual_variance || 0} Days Delay
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Budget utilization</span>
          <span className="text-lg font-extrabold text-white mt-1 flex items-center">
            <IndianRupee className="w-4.5 h-4.5 mr-1.5 text-slate-500" />
            {((parseFloat(summary?.budget_spent || 0) / parseFloat(summary?.budget_limit || 1)) * 100).toFixed(1)}% spent
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Resource Utilization</span>
          <span className="text-lg font-extrabold text-white mt-1 flex items-center">
            <Layers className="w-4.5 h-4.5 mr-1.5 text-slate-500" />
            {parseFloat(summary?.resource_utilization || 85.0).toFixed(1)}% Active
          </span>
        </div>
      </div>

      {/* TIMELINE BURNDOWN GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Progress Timeline view */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col justify-between shadow-lg">
          <div className="space-y-1 mb-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
              <Calendar className="w-4 h-4 mr-1 text-slate-500" />
              Gantt-style Milestone Timelines
            </h3>
            <span className="text-[9px] text-slate-500 italic block">Planned end-dates logs</span>
          </div>

          <div className="space-y-4">
            {milestones.length === 0 ? (
              <p className="text-xs text-slate-500 italic text-center py-8">No milestones declared yet.</p>
            ) : (
              milestones.map((ms, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-205">{ms.milestone_name}</span>
                    <span className="text-slate-405">{parseFloat(ms.completion_percentage)}% • <span className="text-white font-bold">{ms.status}</span></span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-slate-900/60">
                    <div 
                      className={`h-full rounded-full transition-all ${
                        ms.status === 'Completed' ? 'bg-emerald-500' :
                        ms.status === 'Delayed' ? 'bg-rose-500' :
                        ms.status === 'At-Risk' ? 'bg-amber-500' : 'bg-brand-500'
                      }`}
                      style={{ width: `${parseFloat(ms.completion_percentage)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[9px] text-slate-405">
                    <span>Deadline: {new Date(ms.planned_end_date).toLocaleDateString()}</span>
                    {ms.actual_end_date && <span>Completed: {new Date(ms.actual_end_date).toLocaleDateString()}</span>}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Budget burn-down line chart */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col justify-between shadow-lg">
          <div className="text-center space-y-1">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Budget Burn-down Index</h3>
            <span className="text-[9px] text-slate-500 italic block">Spent vs Ceiling limit</span>
          </div>
          
          <div className="w-full h-44 mt-3">
            <Line 
              data={budgetBurnData} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                  x: { ticks: { color: '#64748b', font: { size: 9 } } },
                  y: { ticks: { color: '#64748b', font: { size: 9 } }, grid: { color: '#1e293b' } }
                }
              }} 
            />
          </div>
        </div>

      </div>

      {/* COCKPIT ENGINE DAILY LOG FORM & LATEST UPDATES */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Daily update logger form */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-850 space-y-4 shadow-lg">
          <div className="flex items-center space-x-2 text-indigo-400">
            <UploadCloud className="w-5 h-5 animate-pulse" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Log Daily Progress Update</h3>
          </div>

          {logError && <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-250 rounded-xl text-xs">{logError}</div>}
          {logSuccess && <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-xl text-xs">{logSuccess}</div>}

          <form onSubmit={handleLogSubmit} className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Update Date</label>
              <input
                type="date"
                required
                value={logForm.log_date}
                onChange={(e) => setLogForm(prev => ({ ...prev, log_date: e.target.value }))}
                className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Update description</label>
              <textarea
                required
                placeholder="Log accomplishments, labor delays, material usage..."
                value={logForm.update_text}
                onChange={(e) => setLogForm(prev => ({ ...prev, update_text: e.target.value }))}
                className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white h-20 resize-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Site image upload</label>
              <div className="flex items-center space-x-2">
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                  className="hidden"
                  id="image-file-picker"
                />
                <label 
                  htmlFor="image-file-picker"
                  className="px-4 py-2 bg-slate-850 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold text-xs rounded-xl flex items-center cursor-pointer transition-all"
                >
                  <FileImage className="w-3.5 h-3.5 mr-1.5" />
                  {selectedFile ? selectedFile.name : 'Choose File'}
                </label>
              </div>
            </div>
            <button
              type="submit"
              disabled={actionLoading}
              className="w-full px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl shadow-md disabled:opacity-50"
            >
              Submit Daily Update
            </button>
          </form>
        </div>

        {/* AI progress summary & list of daily updates */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-850 space-y-5 shadow-lg">
          
          {/* AI Narrative */}
          {activeReport?.ai_summary && (
            <div className="space-y-2 pb-4 border-b border-slate-800/80">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center">
                <Sparkles className="w-4 h-4 mr-1 text-indigo-400 animate-pulse" />
                AI Progress & Scheduling Narrative
              </h4>
              <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed pl-3 border-l-2 border-brand-500">
                {activeReport.ai_summary}
              </p>
            </div>
          )}

          {/* Daily logs roster list */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Latest updates history</h4>
            {latestLogs.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-4">No progress logs recorded yet.</p>
            ) : (
              <div className="space-y-3">
                {latestLogs.map((log) => (
                  <div key={log.id} className="p-3 bg-slate-900/40 border border-slate-850 rounded-xl space-y-2 shadow-sm">
                    <div className="flex justify-between items-center text-[10px] text-slate-400">
                      <span className="font-semibold">{new Date(log.log_date).toLocaleDateString()}</span>
                      <span className="flex items-center">
                        <User className="w-3.5 h-3.5 mr-1" /> Logged
                      </span>
                    </div>
                    <p className="text-xs text-slate-205 leading-relaxed">
                      {log.update_text}
                    </p>
                    {log.image_path && (
                      <span className="text-[9px] text-brand-455 font-mono block">Image Attachment: {log.image_path}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>

      {/* CREATE MILESTONE MODAL */}
      {showMilestoneModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel max-w-md w-full p-6 rounded-2xl border border-slate-800 space-y-4 relative shadow-2xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Add Milestone Task</h3>
            <form onSubmit={handleMilestoneSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Milestone Item Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Foundation Pouring Completion"
                  value={milestoneForm.milestone_name}
                  onChange={(e) => setMilestoneForm(prev => ({ ...prev, milestone_name: e.target.value }))}
                  className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Task Description</label>
                <input
                  type="text"
                  placeholder="Details..."
                  value={milestoneForm.description}
                  onChange={(e) => setMilestoneForm(prev => ({ ...prev, description: e.target.value }))}
                  className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-455 uppercase tracking-wider mb-2">Planned End Date</label>
                  <input
                    type="date"
                    required
                    value={milestoneForm.planned_end_date}
                    onChange={(e) => setMilestoneForm(prev => ({ ...prev, planned_end_date: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-455 uppercase tracking-wider mb-2">Completion Ratio %</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    required
                    value={milestoneForm.completion_percentage}
                    onChange={(e) => setMilestoneForm(prev => ({ ...prev, completion_percentage: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowMilestoneModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl disabled:opacity-50"
                >
                  Save Milestone
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressDashboard;
