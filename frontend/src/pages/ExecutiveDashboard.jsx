import React, { useEffect, useState } from 'react';
import { getExecutiveAnalytics } from '../services/executive';
import { getProjects } from '../services/projects';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { 
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, 
  LineElement, Title, Tooltip, Legend, BarElement, ArcElement
} from 'chart.js';
import { 
  Activity, ShieldAlert, Users, Layers, AlertCircle, Sparkles, 
  RefreshCw, TrendingUp, Calendar, FileText, CheckCircle, 
  CloudRain, DollarSign, Filter, Search, UserCheck
} from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement, ArcElement);

const ExecutiveDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [data, setData] = useState(null);
  
  // Filter States
  const [selectedProject, setSelectedProject] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [managerId, setManagerId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const fetchFiltersAndData = async () => {
    try {
      setLoading(true);
      // Fetch all projects for selection list
      const response = await getProjects();
      setProjects(response.items || []);

      // Build query filters
      const params = {};
      if (selectedProject) params.project_id = selectedProject;
      if (selectedStatus) params.project_status = selectedStatus;
      if (managerId) params.manager_id = managerId;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      // Fetch analytics
      const analytics = await getExecutiveAnalytics(params);
      setData(analytics);
    } catch (err) {
      console.error("Failed to load executive analytics: ", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiltersAndData();
  }, [selectedProject, selectedStatus, managerId, startDate, endDate]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900 text-white">
        <div className="text-center">
          <Activity className="h-10 w-10 animate-spin text-indigo-500 mx-auto mb-4" />
          <p className="text-slate-400 font-medium">Assembling executive records...</p>
        </div>
      </div>
    );
  }

  const w = data?.widgets || {};
  const c = data?.charts || {};
  const recs = data?.recent_recommendations || [];

  // 1. Line: Risk History Chart Config
  const lineChartData = {
    labels: c.line_risk_history?.labels || [],
    datasets: [
      {
        label: 'Risk Score (0-100)',
        data: c.line_risk_history?.risk_scores || [],
        borderColor: '#f43f5e',
        backgroundColor: 'rgba(244, 63, 94, 0.1)',
        tension: 0.3,
        fill: true,
        yAxisID: 'y',
      },
      {
        label: 'Delay Probability (%)',
        data: c.line_risk_history?.delay_probs || [],
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.3,
        fill: true,
        yAxisID: 'y1',
      }
    ]
  };

  const lineChartOptions = {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#94a3b8' }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: { drawOnChartArea: false },
        ticks: { color: '#94a3b8' }
      },
      x: {
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#94a3b8' }
      }
    },
    plugins: {
      legend: { labels: { color: '#e2e8f0' } }
    }
  };

  // 2. Pie: Budget Distribution
  const pieChartData = {
    labels: c.pie_budget_distribution?.labels || [],
    datasets: [{
      data: c.pie_budget_distribution?.data || [],
      backgroundColor: [
        '#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'
      ],
      borderWidth: 1
    }]
  };

  // 3. Bar: Material Costs
  const materialBarData = {
    labels: c.bar_material_costs?.labels || [],
    datasets: [{
      label: 'Total Cost (INR)',
      data: c.bar_material_costs?.data || [],
      backgroundColor: '#3b82f6',
      borderRadius: 6
    }]
  };

  // 4. Bar: Worker Roles
  const workerBarData = {
    labels: c.bar_worker_roles?.labels || [],
    datasets: [{
      label: 'Workers Count',
      data: c.bar_worker_roles?.data || [],
      backgroundColor: '#10b981',
      borderRadius: 6
    }]
  };

  // 5. Forecast Line Curve
  const forecastChartData = {
    labels: c.forecast_progress?.labels || [],
    datasets: [
      {
        label: 'Actual Progress (%)',
        data: c.forecast_progress?.actual || [],
        borderColor: '#10b981',
        backgroundColor: '#10b981',
        spanGaps: true,
        tension: 0.2
      },
      {
        label: 'Predicted Forecast (%)',
        data: c.forecast_progress?.predicted || [],
        borderColor: '#8b5cf6',
        backgroundColor: '#8b5cf6',
        borderDash: [5, 5],
        tension: 0.2
      }
    ]
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 pb-5 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm tracking-wider uppercase">
            <Sparkles className="h-4 w-4 animate-pulse" />
            Executive Oversight Cockpit
          </div>
          <h1 className="text-3xl font-extrabold text-white mt-1">APEXBuild Live Portfolio Analytics</h1>
          <p className="text-slate-400 mt-1 text-sm">Real-time data feeds spanning finances, risk index, materials, safety violations, and AI planning summaries.</p>
        </div>
        <button 
          onClick={fetchFiltersAndData}
          className="mt-4 md:mt-0 flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg border border-slate-700 transition"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh Stats
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Project Selection</label>
          <div className="relative">
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full bg-slate-850 border border-slate-700 rounded-lg py-2 px-3 text-slate-200 focus:outline-none focus:border-indigo-500 appearance-none"
            >
              <option value="">All Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.project_name}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Project Status</label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full bg-slate-850 border border-slate-700 rounded-lg py-2 px-3 text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="On-Track">On-Track</option>
            <option value="Delayed">Delayed</option>
            <option value="Completed">Completed</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Manager ID</label>
          <input
            type="number"
            placeholder="Filter by ID"
            value={managerId}
            onChange={(e) => setManagerId(e.target.value)}
            className="w-full bg-slate-850 border border-slate-700 rounded-lg py-2 px-3 text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full bg-slate-850 border border-slate-700 rounded-lg py-2 px-3 text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full bg-slate-850 border border-slate-700 rounded-lg py-2 px-3 text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* KPI Widgets */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Widget 1: Projects count & completion */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 h-24 w-24 bg-indigo-500/10 rounded-full blur-xl group-hover:bg-indigo-500/20 transition-all duration-300" />
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 font-medium text-sm">Portfolio Scope</span>
            <div className="bg-indigo-500/10 p-2 rounded-lg text-indigo-400">
              <Layers className="h-5 w-5" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-white">{w.total_projects} Active</h3>
          <p className="text-slate-400 text-xs mt-2">Overall Progress: <span className="text-indigo-400 font-semibold">{w.overall_progress}%</span></p>
        </div>

        {/* Widget 2: Finances */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 h-24 w-24 bg-emerald-500/10 rounded-full blur-xl group-hover:bg-emerald-500/20 transition-all duration-300" />
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 font-medium text-sm">Finances (Estimated)</span>
            <div className="bg-emerald-500/10 p-2 rounded-lg text-emerald-400">
              <DollarSign className="h-5 w-5" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-white">₹{w.total_estimated_cost?.toLocaleString()}</h3>
          <p className="text-slate-400 text-xs mt-2">Optimized Target: <span className="text-emerald-400 font-semibold">₹{w.total_optimized_cost?.toLocaleString()}</span></p>
        </div>

        {/* Widget 3: Workforce Utilization */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 h-24 w-24 bg-amber-500/10 rounded-full blur-xl group-hover:bg-amber-500/20 transition-all duration-300" />
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 font-medium text-sm">Workforce Utilization</span>
            <div className="bg-amber-500/10 p-2 rounded-lg text-amber-400">
              <Users className="h-5 w-5" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-white">{w.active_workers} Workers</h3>
          <p className="text-slate-400 text-xs mt-2">Attendance Rate: <span className="text-amber-400 font-semibold">{w.attendance_rate}%</span></p>
        </div>

        {/* Widget 4: Risk Index */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 h-24 w-24 bg-rose-500/10 rounded-full blur-xl group-hover:bg-rose-500/20 transition-all duration-300" />
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 font-medium text-sm">Portfolio Threat Level</span>
            <div className="bg-rose-500/10 p-2 rounded-lg text-rose-400">
              <ShieldAlert className="h-5 w-5" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-white">{w.average_risk_score} / 100</h3>
          <p className="text-slate-400 text-xs mt-2">Safety Hazards Open: <span className="text-rose-400 font-semibold">{w.safety_violations_count} cases</span></p>
        </div>
      </div>

      {/* Chart Layout: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Risk Scores Line Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-400" />
            Chronological Risk Scores & Delay Forecasts (Line)
          </h2>
          <div className="h-72">
            <Line data={lineChartData} options={lineChartOptions} />
          </div>
        </div>

        {/* Budget Allocation Pie Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-emerald-400" />
            Portfolio Budget Distribution (Pie)
          </h2>
          <div className="h-72 flex items-center justify-center">
            {c.pie_budget_distribution?.data?.length > 0 ? (
              <div className="h-64 w-64">
                <Pie data={pieChartData} options={{ responsive: true, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } } }} />
              </div>
            ) : (
              <p className="text-slate-500 text-sm">No project budgets recorded.</p>
            )}
          </div>
        </div>

        {/* Material cost allocation Bar Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Layers className="h-5 w-5 text-blue-400" />
            Material Costs Allocation By Category (Bar)
          </h2>
          <div className="h-72">
            <Bar data={materialBarData} options={{ responsive: true, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8' } } } }} />
          </div>
        </div>

        {/* Progress Forecast Curve */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-400" />
            Project Completion Progress Forecast Curve (Forecast)
          </h2>
          <div className="h-72">
            <Line data={forecastChartData} options={lineChartOptions} />
          </div>
        </div>
      </div>

      {/* Bottom Grid: Heatmap + Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Heatmap: Weekly Shift Attendance */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 lg:col-span-1">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <UserCheck className="h-5 w-5 text-indigo-400" />
            Attendance Intensity (Heatmap)
          </h2>
          <div className="mt-4">
            <div className="grid grid-cols-8 gap-2 text-center text-xs font-semibold text-slate-400 mb-2">
              <div>Shift</div>
              {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => <div key={i}>{d}</div>)}
            </div>
            
            {/* Day Shift Row */}
            <div className="grid grid-cols-8 gap-2 items-center mb-2">
              <div className="text-xs font-medium text-slate-300">Day</div>
              {[...Array(7)].map((_, i) => {
                const val = c.heatmap_attendance?.find(h => h.day === i && h.shift === "Day")?.value || 0;
                let bg = 'bg-slate-800';
                if (val > 8) bg = 'bg-indigo-600 text-white';
                else if (val > 4) bg = 'bg-indigo-700/60 text-slate-200';
                else if (val > 0) bg = 'bg-indigo-900/30 text-slate-400';
                return (
                  <div key={i} className={`h-8 rounded flex items-center justify-center font-bold ${bg} text-xs transition duration-300 hover:scale-105`} title={`Active: ${val}`}>
                    {val}
                  </div>
                );
              })}
            </div>

            {/* Night Shift Row */}
            <div className="grid grid-cols-8 gap-2 items-center">
              <div className="text-xs font-medium text-slate-300">Night</div>
              {[...Array(7)].map((_, i) => {
                const val = c.heatmap_attendance?.find(h => h.day === i && h.shift === "Night")?.value || 0;
                let bg = 'bg-slate-800';
                if (val > 8) bg = 'bg-indigo-600 text-white';
                else if (val > 4) bg = 'bg-indigo-700/60 text-slate-200';
                else if (val > 0) bg = 'bg-indigo-900/30 text-slate-400';
                return (
                  <div key={i} className={`h-8 rounded flex items-center justify-center font-bold ${bg} text-xs transition duration-300 hover:scale-105`} title={`Active: ${val}`}>
                    {val}
                  </div>
                );
              })}
            </div>
          </div>
          <div className="flex items-center justify-between text-xxs text-slate-500 mt-6">
            <span>Low Roster</span>
            <div className="flex gap-1">
              <div className="h-3 w-3 bg-indigo-900/30 rounded" />
              <div className="h-3 w-3 bg-indigo-700/60 rounded" />
              <div className="h-3 w-3 bg-indigo-600 rounded" />
            </div>
            <span>High Intensity</span>
          </div>
        </div>

        {/* Timeline: Milestone calendar list */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 lg:col-span-2">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-amber-400" />
            Milestone Progress Timelines (Timeline)
          </h2>
          <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
            {c.timeline_milestones?.length > 0 ? (
              c.timeline_milestones.map((m, idx) => (
                <div key={idx} className="bg-slate-850 border border-slate-800 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="text-sm font-semibold text-white">{m.milestone_name}</h4>
                      <span className="text-slate-500 text-xs">{m.project_name}</span>
                    </div>
                    <span className="text-xs font-bold text-indigo-400">{m.completion}%</span>
                  </div>
                  <div className="w-full bg-slate-700 h-2 rounded-full overflow-hidden mb-2">
                    <div className="bg-indigo-500 h-2" style={{ width: `${m.completion}%` }} />
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Planned Target: <b className="text-slate-300">{m.planned_end || "N/A"}</b></span>
                    <span>Status: <b className={m.status === "Delayed" ? "text-rose-400" : "text-emerald-400"}>{m.status}</b></span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-slate-500 text-sm mt-4">No milestone pipelines scheduled.</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent AI Recs */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-lg font-bold text-indigo-400 mb-4 flex items-center gap-2 uppercase tracking-wide">
          <Sparkles className="h-5 w-5 animate-pulse" />
          Recent Real-time Portfolio AI Insights & Recs
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recs.length > 0 ? (
            recs.map((rec, idx) => (
              <div key={idx} className="bg-slate-850 border border-slate-700 rounded-xl p-4 hover:border-indigo-500/50 transition duration-300 relative group overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-400 uppercase">{rec.module}</span>
                  <span className="text-xxs text-slate-500">{rec.created_at}</span>
                </div>
                <h4 className="text-xs font-semibold text-slate-300 mb-2">{rec.project_name}</h4>
                <p className="text-slate-400 text-xs leading-relaxed">{rec.recommendation}</p>
              </div>
            ))
          ) : (
            <p className="text-slate-500 text-sm">No risk anomalies or visual inspections registered.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExecutiveDashboard;
