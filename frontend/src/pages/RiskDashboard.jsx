import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProjectRisk, analyzeProjectRisks, getRiskHistory, downloadRiskReport } from '../services/risk';
import { getProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { Line, Bar } from 'react-chartjs-2';
import { 
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, 
  LineElement, Title, Tooltip, Legend, BarElement 
} from 'chart.js';
import { 
  ArrowLeft, ShieldAlert, Sparkles, RefreshCw, FileText, 
  FileSpreadsheet, CloudRain, ShieldCheck, Thermometer, Wind, 
  Clock, AlertTriangle, Lightbulb, TrendingUp, Loader, IndianRupee
} from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement);

const RiskDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [currentRisk, setCurrentRisk] = useState(null);
  const [history, setHistory] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);
      
      const risk = await getProjectRisk(projectId);
      setCurrentRisk(risk);
      
      const hist = await getRiskHistory(projectId);
      setHistory(hist.reverse()); // Chronological ordering
    } catch (err) {
      console.error(err);
      setError('Failed to retrieve project risk registers.');
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
      const resp = await analyzeProjectRisks(projectId);
      setCurrentRisk(resp);
      await loadData();
    } catch (err) {
      console.error(err);
      setError('AI risk scoring re-calculation failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownload = async (format) => {
    try {
      await downloadRiskReport(projectId, format, `risk_report_project_${projectId}`);
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

  const riskObj = currentRisk?.risk;
  const delayObj = currentRisk?.delay_prediction;
  const weatherObj = currentRisk?.weather;
  const canModify = user?.role === 'Admin' || user?.role === 'Project Manager';

  // Severity colors helper
  const getSeverityStyles = (sev) => {
    switch (sev) {
      case 'Critical':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/25';
      case 'High':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/25';
      case 'Medium':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/25';
      default:
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25';
    }
  };

  // Chart configs
  const lineChartData = {
    labels: history.map(h => new Date(h.created_at).toLocaleDateString()),
    datasets: [
      {
        label: 'Risk Score Index',
        data: history.map(h => h.risk_score),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        tension: 0.3,
        fill: true
      },
      {
        label: 'Delay Probability %',
        data: history.map(h => parseFloat(h.delay_probability)),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.3,
        fill: true
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
            <h1 className="text-xl font-bold tracking-tight text-white">AI Risk Prediction Center</h1>
            <p className="text-xs text-slate-400 mt-1">
              Live predictive threat indicators for: <span className="text-slate-200 font-semibold">{project?.project_name}</span>
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
            Export History CSV
          </button>
          {canModify && (
            <button
              onClick={handleRecalculate}
              disabled={actionLoading}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl flex items-center shadow-lg transition-all disabled:opacity-50"
            >
              {actionLoading ? <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 mr-1.5 animate-pulse" />}
              Re-Calculate Risks
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-250 text-xs">
          {error}
        </div>
      )}

      {/* METRICS ROW */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Composite Risk Score Gauge */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col justify-between shadow-xl">
          <div className="space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Composite Risk Score</span>
            <div className="flex items-baseline space-x-2">
              <span className={`text-4xl font-extrabold ${
                riskObj?.risk_score > 60 ? 'text-rose-450' : riskObj?.risk_score > 30 ? 'text-amber-500' : 'text-emerald-400'
              }`}>
                {riskObj?.risk_score || 0}
              </span>
              <span className="text-xs text-slate-500">/ 100 max index</span>
            </div>
            <p className="text-[10px] text-slate-405 leading-relaxed">
              Analyzes composite metrics across workforce deficits, sequence delays, and material shortages.
            </p>
          </div>
          <div className="mt-4 border-t border-slate-800/60 pt-3">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Threat Level Status:</span>
            <span className={`text-xs font-bold ${
              riskObj?.risk_score > 60 ? 'text-rose-400' : riskObj?.risk_score > 30 ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {riskObj?.risk_score > 60 ? 'Critical Threat Warning' : riskObj?.risk_score > 30 ? 'Moderate Alert Level' : 'Operational Status Healthy'}
            </span>
          </div>
        </div>

        {/* Delay Probability Card */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col justify-between shadow-xl">
          <div className="space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Project Delay Probability</span>
            <div className="flex items-baseline space-x-2">
              <span className="text-4xl font-extrabold text-white">
                {parseFloat(riskObj?.delay_probability || 0.0)}%
              </span>
            </div>
            <p className="text-[10px] text-slate-405 leading-relaxed">
              Calculates target deadline overrun probability based on milestone deadline variance days.
            </p>
          </div>
          <div className="mt-4 border-t border-slate-800/60 pt-3">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Forecasted Completion Variance:</span>
            <span className="text-xs font-bold text-slate-205 flex items-baseline">
              <Clock className="w-3.5 h-3.5 mr-1 text-slate-500" />
              {delayObj?.predicted_delay_days || 0} Days Behind Schedule
            </span>
          </div>
        </div>

        {/* Weather Alerts strip */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col justify-between shadow-xl">
          <div className="space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Live Weather Conditions</span>
            {weatherObj ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <CloudRain className="w-8 h-8 text-brand-400" />
                    <div>
                      <span className="text-sm font-bold text-white block capitalize">{weatherObj.weather_description}</span>
                      <span className="text-[9px] text-slate-405">{weatherObj.location}</span>
                    </div>
                  </div>
                  <span className="text-lg font-bold text-white">{parseFloat(weatherObj.temperature)}°C</span>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 border-t border-slate-800/60 pt-2">
                  <span className="flex items-center">
                    <Wind className="w-3 h-3 mr-1 text-slate-500" />
                    Wind: {parseFloat(weatherObj.wind_speed)} km/h
                  </span>
                  <span className="flex items-center">
                    <Thermometer className="w-3 h-3 mr-1 text-slate-500" />
                    Rain: {parseFloat(weatherObj.precipitation)} mm
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No weather updates cached.</p>
            )}
          </div>
          
          <div className="mt-2 text-[10px] text-amber-500 font-bold">
            {weatherObj?.alerts ? `Alert: ${weatherObj.alerts}` : '✓ No hazardous weather alerts flagged'}
          </div>
        </div>

      </div>

      {/* CATEGORY MATRIX */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Risk Categories breakdown</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Weather Delays', field: 'weather_risk_severity' },
            { label: 'Material Deficit', field: 'material_risk_severity' },
            { label: 'Budget Overrun', field: 'budget_risk_severity' },
            { label: 'Labor Deficit', field: 'worker_risk_severity' },
            { label: 'Equipment Failure', field: 'equipment_risk_severity' },
            { label: 'Supplier Delay', field: 'supplier_risk_severity' },
            { label: 'Safety Incidents', field: 'safety_risk_severity' },
            { label: 'Timeline Delay', field: 'timeline_risk_severity' }
          ].map((cat, idx) => {
            const sev = riskObj ? riskObj[cat.field] : 'Low';
            return (
              <div key={idx} className={`p-4 rounded-xl border flex flex-col justify-between space-y-3 shadow ${getSeverityStyles(sev)}`}>
                <span className="text-[10px] font-bold uppercase tracking-wider block opacity-80">{cat.label}</span>
                <span className="text-sm font-extrabold block">{sev}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI RECOMMENDATIONS CARD */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Executive summary & suggestions */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-850 space-y-4 shadow-lg">
          <div className="flex items-center space-x-2 text-indigo-400">
            <Lightbulb className="w-5 h-5 animate-pulse" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Mitigation Strategy Plan</h3>
          </div>
          
          <div className="space-y-3 pl-3 border-l-2 border-brand-500">
            <h4 className="text-xs font-bold text-slate-200">Executive Summary Context</h4>
            <p className="text-xs text-slate-350 leading-relaxed whitespace-pre-line">
              {riskObj?.executive_summary || 'No risk narrative recorded.'}
            </p>
          </div>

          <div className="space-y-2 border-t border-slate-800/80 pt-4">
            <h4 className="text-xs font-bold text-slate-200">AI-Suggested Recommendations</h4>
            <p className="text-xs text-slate-350 leading-relaxed whitespace-pre-line pl-3">
              {riskObj?.ai_mitigation_suggestions || 'Assess shift registers periodically.'}
            </p>
          </div>
        </div>

        {/* History trend chart */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col items-center justify-between shadow-lg">
          <div className="w-full text-center space-y-1">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-center">
              <TrendingUp className="w-4 h-4 mr-1 text-slate-500" />
              Risk Index Timeline Trend
            </h3>
            <span className="text-[9px] text-slate-500 italic block">Audit logs trail</span>
          </div>
          
          <div className="w-full h-48 mt-4">
            {history.length > 0 ? (
              <Line 
                data={lineChartData} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { ticks: { color: '#64748b', font: { size: 9 } }, grid: { display: false } },
                    y: { ticks: { color: '#64748b', font: { size: 9 } }, grid: { color: '#1e293b' } }
                  }
                }} 
              />
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500 italic">
                Insufficient history logs data.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default RiskDashboard;
