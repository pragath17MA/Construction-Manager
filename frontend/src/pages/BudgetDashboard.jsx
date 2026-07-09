import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getBudgetDetail, getBudgetHistory, downloadBudgetReport, deleteBudget } from '../services/budget';
import { getProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { Pie, Bar, Line } from 'react-chartjs-2';
import { 
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, 
  PointElement, LineElement, ArcElement, Title, Tooltip, Legend 
} from 'chart.js';
import { 
  ArrowLeft, Calculator, Download, Calendar, Trash2, ArrowUpRight, 
  HelpCircle, AlertCircle, TrendingDown, IndianRupee, Sparkles, 
  ListFilter, History, RefreshCw, BarChart3, Loader
} from 'lucide-react';

// Register ChartJS
ChartJS.register(
  CategoryScale, LinearScale, BarElement, PointElement, 
  LineElement, ArcElement, Title, Tooltip, Legend
);

const BudgetDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [budgetDetail, setBudgetDetail] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyCount, setHistoryCount] = useState(0);
  const [historyPage, setHistoryPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('overview'); // overview, details, history, comparison
  const [error, setError] = useState('');
  const [downloadingReport, setDownloadingReport] = useState(false);

  const loadData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);
      
      try {
        const detail = await getBudgetDetail(projectId);
        setBudgetDetail(detail);
      } catch (err) {
        if (err.response?.status === 404) {
          setBudgetDetail(null);
        } else {
          throw err;
        }
      }
      
      try {
        const histData = await getBudgetHistory(projectId, historyPage, 5);
        setHistory(histData.items);
        setHistoryCount(histData.total);
      } catch (err) {
        console.error(err);
      }

    } catch (err) {
      console.error(err);
      setError('Failed to load project budget details.');
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadData();
      setLoading(false);
    };
    init();
  }, [projectId, historyPage]);

  const handleDownload = async () => {
    if (!budgetDetail?.budget?.id) return;
    setDownloadingReport(true);
    try {
      const name = `budget_report_${project.project_name.toLowerCase().replace(/\s+/g, '_')}.pdf`;
      await downloadBudgetReport(budgetDetail.budget.id, name);
    } catch (err) {
      console.error(err);
      alert('Failed to generate and download PDF report.');
    } finally {
      setDownloadingReport(false);
    }
  };

  const handleDelete = async (budgetId) => {
    if (window.confirm('Delete this budget estimate permanently? This cannot be undone.')) {
      try {
        await deleteBudget(budgetId);
        await loadData();
      } catch (err) {
        console.error(err);
        alert('Failed to delete budget estimate.');
      }
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

  // Render Placeholder if no estimates exist yet
  if (!budgetDetail) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <div className="flex items-center space-x-3">
          <Link
            to={`/projects/${projectId}`}
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-xl font-bold tracking-tight text-white">AI Cost Estimation Center</h1>
        </div>

        <div className="glass-panel p-10 rounded-2xl border border-slate-850 text-center space-y-6 shadow-xl">
          <div className="mx-auto w-14 h-14 bg-brand-500/10 border border-brand-500/25 rounded-2xl flex items-center justify-center text-brand-400">
            <Calculator className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h2 className="text-lg font-bold text-white">No active budget estimations</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Analyze project material bills, labor shifts, and machinery rentals using our AI optimization models to generate accurate budgets.
            </p>
          </div>
          {canModify ? (
            <Link
              to={`/projects/${projectId}/budget/new`}
              className="inline-flex px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl shadow-lg transition-all"
            >
              Configure Cost inputs & Run AI Estimate
            </Link>
          ) : (
            <p className="text-[10px] text-slate-500 italic">Estimations must be initialized by a Project Manager or Admin.</p>
          )}
        </div>
      </div>
    );
  }

  const { budget, labor_costs, equipment_costs } = budgetDetail;

  // Calculate totals by categories
  const getCategoryTotal = (catName) => {
    return budget.items
      .filter(item => item.category.toLowerCase() === catName.toLowerCase())
      .reduce((sum, item) => sum + parseFloat(item.total_price), 0);
  };

  const matTotal = getCategoryTotal('Material');
  const labTotal = getCategoryTotal('Labor');
  const eqTotal = getCategoryTotal('Equipment');
  const indTotal = getCategoryTotal('Indirect');
  const contTotal = getCategoryTotal('Contingency');

  const savings = Math.max(0, parseFloat(budget.estimated_cost) - parseFloat(budget.optimized_cost));

  // Chart data definitions
  const pieData = {
    labels: ['Materials', 'Labor', 'Equipment', 'Indirects', 'Contingency'],
    datasets: [
      {
        data: [matTotal, labTotal, eqTotal, indTotal, contTotal],
        backgroundColor: [
          '#6366f1', // Indigo
          '#10b981', // Emerald
          '#3b82f6', // Blue
          '#f59e0b', // Amber
          '#ef4444'  // Rose
        ],
        borderWidth: 1,
        borderColor: '#0f172a'
      }
    ]
  };

  const barData = {
    labels: ['Original Estimate', 'AI Optimized Target'],
    datasets: [
      {
        label: 'Budget Total',
        data: [parseFloat(budget.estimated_cost), parseFloat(budget.optimized_cost)],
        backgroundColor: ['rgba(99, 102, 241, 0.4)', 'rgba(16, 185, 129, 0.6)'],
        borderColor: ['#6366f1', '#10b981'],
        borderWidth: 1.5,
        borderRadius: 8
      }
    ]
  };

  // Compile history chart (last 5 estimates over time)
  const historySorted = [...history].reverse();
  const lineData = {
    labels: historySorted.map(h => new Date(h.created_at).toLocaleDateString()),
    datasets: [
      {
        label: 'Historical Cost Trends',
        data: historySorted.map(h => parseFloat(h.estimated_cost)),
        fill: false,
        borderColor: '#6366f1',
        tension: 0.1,
        pointBackgroundColor: '#818cf8'
      }
    ]
  };

  return (
    <div className="space-y-6">
      {/* Header cock pit */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div className="flex items-center space-x-3">
          <Link
            to={`/projects/${projectId}`}
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">AI Cost Estimation Center</h1>
            <p className="text-xs text-slate-400 mt-1">
              Active Control cockpit for project: <span className="text-slate-200 font-semibold">{project?.project_name}</span>
            </p>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleDownload}
            disabled={downloadingReport}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-100 font-semibold text-xs rounded-xl border border-slate-750 flex items-center transition-all disabled:opacity-50"
          >
            {downloadingReport ? (
              <Loader className="w-3.5 h-3.5 mr-1.5 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5 mr-1.5" />
            )}
            Download PDF Report
          </button>
          {canModify && (
            <Link
              to={`/projects/${projectId}/budget/new`}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl flex items-center shadow-lg transition-all"
            >
              <Calculator className="w-3.5 h-3.5 mr-1.5" />
              Recalculate Estimate
            </Link>
          )}
        </div>
      </div>

      {/* KPI stats section */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Estimated Cost</span>
          <span className="text-lg font-extrabold text-white mt-1 flex items-center">
            <IndianRupee className="w-4 h-4 mr-0.5 text-slate-500" />
            {parseFloat(budget.estimated_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block">AI Optimized Target</span>
          <span className="text-lg font-extrabold text-emerald-400 mt-1 flex items-center">
            <IndianRupee className="w-4 h-4 mr-0.5 text-emerald-500" />
            {parseFloat(budget.optimized_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">AI Computed Savings</span>
          <span className="text-lg font-extrabold text-indigo-400 mt-1 flex items-center">
            <IndianRupee className="w-4 h-4 mr-0.5 text-indigo-500" />
            {savings.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Building Area</span>
          <span className="text-lg font-extrabold text-slate-200 mt-1">
            {project?.budget ? 'Active Scope' : 'N/A'}
          </span>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-850 space-x-6 text-xs font-bold uppercase tracking-wider">
        <button
          onClick={() => setActiveSubTab('overview')}
          className={`pb-3 border-b-2 transition-all ${
            activeSubTab === 'overview' ? 'border-brand-500 text-white' : 'border-transparent text-slate-450 hover:text-slate-200'
          }`}
        >
          Overview & AI Recommendations
        </button>
        <button
          onClick={() => setActiveSubTab('details')}
          className={`pb-3 border-b-2 transition-all ${
            activeSubTab === 'details' ? 'border-brand-500 text-white' : 'border-transparent text-slate-450 hover:text-slate-200'
          }`}
        >
          Itemized Breakdown
        </button>
        <button
          onClick={() => setActiveSubTab('comparison')}
          className={`pb-3 border-b-2 transition-all ${
            activeSubTab === 'comparison' ? 'border-brand-500 text-white' : 'border-transparent text-slate-450 hover:text-slate-200'
          }`}
        >
          Savings comparison
        </button>
        <button
          onClick={() => setActiveSubTab('history')}
          className={`pb-3 border-b-2 transition-all ${
            activeSubTab === 'history' ? 'border-brand-500 text-white' : 'border-transparent text-slate-450 hover:text-slate-200'
          }`}
        >
          Estimation History
        </button>
      </div>

      {/* TAB CONTENT: OVERVIEW */}
      {activeSubTab === 'overview' && (
        <div className="space-y-6">
          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="glass-panel p-5 rounded-2xl border border-slate-850 flex flex-col items-center">
              <h3 className="text-xs font-semibold text-slate-350 mb-4 text-center">Cost Category Distribution</h3>
              <div className="w-56 h-56">
                <Pie data={pieData} options={{ plugins: { legend: { display: false } } }} />
              </div>
            </div>
            <div className="glass-panel p-5 rounded-2xl border border-slate-850 flex flex-col">
              <h3 className="text-xs font-semibold text-slate-350 mb-4 text-center">Original vs Optimized Cost</h3>
              <div className="flex-1 min-h-[220px]">
                <Bar data={barData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
            <div className="glass-panel p-5 rounded-2xl border border-slate-850 flex flex-col">
              <h3 className="text-xs font-semibold text-slate-350 mb-4 text-center">Historical Estimations trend</h3>
              <div className="flex-1 min-h-[220px]">
                <Line data={lineData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>

          {/* AI Optimizer recommendation boxes */}
          {budget.ai_summary && (
            <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 bg-indigo-950/10 space-y-4 shadow-lg">
              <div className="flex items-center space-x-2 text-indigo-400">
                <Sparkles className="w-5 h-5 animate-pulse" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Executive Budget Analysis</h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-medium">
                {budget.ai_summary}
              </p>
              
              {budget.ai_recommendations && (
                <div className="border-t border-slate-800/80 pt-4 space-y-2">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wide">Optimization Directives:</h4>
                  <div className="text-xs text-slate-400 whitespace-pre-line leading-relaxed pl-3 border-l-2 border-brand-500">
                    {budget.ai_recommendations}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: DETAILS */}
      {activeSubTab === 'details' && (
        <div className="space-y-6">
          <div className="glass-panel rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
            <table className="min-w-full divide-y divide-slate-850">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Quantity</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Unit Price</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Total Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850/60 bg-transparent text-xs text-slate-300">
                {budget.items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold border ${
                        item.category === 'Material' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                        item.category === 'Labor' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                        item.category === 'Equipment' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                        'bg-slate-800 text-slate-300 border-slate-700'
                      }`}>
                        {item.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-200">
                      {item.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      {parseFloat(item.quantity).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      {parseFloat(item.unit_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right font-semibold text-white">
                      {parseFloat(item.total_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT: COMPARISON */}
      {activeSubTab === 'comparison' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-850 space-y-4">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide">Original Baseline Costs</h3>
            <div className="space-y-3 divide-y divide-slate-850/50">
              <div className="flex justify-between items-center py-2 text-xs">
                <span className="text-slate-400 font-medium">Materials Subtotal</span>
                <span className="text-white font-semibold">{matTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between items-center py-2 text-xs">
                <span className="text-slate-400 font-medium">Labor Subtotal</span>
                <span className="text-white font-semibold">{labTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between items-center py-2 text-xs">
                <span className="text-slate-400 font-medium">Equipment Subtotal</span>
                <span className="text-white font-semibold">{eqTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between items-center py-2 text-xs">
                <span className="text-slate-400 font-medium">Overhead Indirects (10%)</span>
                <span className="text-white font-semibold">{indTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between items-center py-2 text-xs">
                <span className="text-slate-400 font-medium">Contingency buffer (5%)</span>
                <span className="text-white font-semibold">{contTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between items-center pt-3 text-sm font-bold border-t border-slate-800 text-white">
                <span>Baseline Total</span>
                <span>{parseFloat(budget.estimated_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-emerald-500/20 bg-emerald-950/10 space-y-4">
            <div className="flex items-center space-x-2 text-emerald-400">
              <Sparkles className="w-5 h-5 animate-pulse" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wide">AI Optimized Targets</h3>
            </div>
            <div className="space-y-3">
              <div className="p-4 bg-slate-900/60 rounded-xl space-y-2 border border-slate-850">
                <span className="text-[10px] text-slate-450 uppercase font-bold tracking-wider">AI Suggested Limit</span>
                <div className="text-xl font-extrabold text-emerald-400">
                  {parseFloat(budget.optimized_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className="text-xs text-slate-400 flex items-center">
                  <TrendingDown className="w-4 h-4 mr-1 text-emerald-400" />
                  Estimated savings of {((savings / parseFloat(budget.estimated_cost)) * 100).toFixed(1)}% on initial budget.
                </div>
              </div>
              <div className="text-xs text-slate-350 leading-relaxed">
                Groq AI recommendation engines optimize operational timelines and substitute materials grades in real-time. Follow the guidelines in the overview tab to implement these cost reductions.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: HISTORY */}
      {activeSubTab === 'history' && (
        <div className="space-y-4">
          <div className="glass-panel rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
            <table className="min-w-full divide-y divide-slate-850">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Date calculated</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Estimated Cost</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Optimized Cost</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Savings</th>
                  {canModify && <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850/60 bg-transparent text-xs text-slate-300">
                {history.map((hist) => (
                  <tr key={hist.id} className="hover:bg-slate-900/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-slate-400">
                      {new Date(hist.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                      {parseFloat(hist.estimated_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-emerald-400 font-semibold">
                      {parseFloat(hist.optimized_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-indigo-400 font-semibold">
                      {(parseFloat(hist.estimated_cost) - parseFloat(hist.optimized_cost)).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    {canModify && (
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={() => handleDelete(hist.id)}
                          className="p-1.5 bg-slate-850 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-lg border border-transparent hover:border-rose-500/20 transition-all"
                          title="Delete Estimate"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default BudgetDashboard;
