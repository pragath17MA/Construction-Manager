import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getProjects } from '../services/projects';
import { LayoutDashboard, Shield, Briefcase, FileText, CheckCircle, PlayCircle, AlertTriangle, Calendar, IndianRupee } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    running: 0,
    delayed: 0,
    totalBudget: 0,
    upcomingDeadlines: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await getProjects({ page: 1, size: 100 });
        const items = response.items || [];
        
        let completed = 0;
        let running = 0;
        let delayed = 0;
        let totalBudget = 0;
        
        const now = new Date();
        const thirtyDaysFromNow = new Date();
        thirtyDaysFromNow.setDate(now.getDate() + 30);

        const upcomingDeadlines = [];

        items.forEach(p => {
          totalBudget += parseFloat(p.budget);
          if (p.status === 'Completed') completed++;
          else if (p.status === 'In Progress') running++;
          else if (p.status === 'Delayed') delayed++;

          // Check deadline
          if (p.status !== 'Completed' && p.status !== 'Cancelled') {
            const endDate = new Date(p.expected_end_date);
            if (endDate >= now && endDate <= thirtyDaysFromNow) {
              upcomingDeadlines.push(p);
            }
          }
        });

        setStats({
          total: items.length,
          completed,
          running,
          delayed,
          totalBudget,
          upcomingDeadlines: upcomingDeadlines.slice(0, 3) // show top 3
        });
      } catch (err) {
        console.error('Failed to load dashboard statistics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-700 border-t-brand-500"></div>
          <p className="text-sm text-slate-400">Loading workspace statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Project Dashboard</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Control center mapping active contracts, budgets, and scheduling pipelines
          </p>
        </div>
        <div className="flex space-x-3">
          <Link
            to="/projects/create"
            className="inline-flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-white bg-brand-600 rounded-xl hover:bg-brand-500 transition-all duration-200"
          >
            Create New Project
          </Link>
          <Link
            to="/projects"
            className="inline-flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 transition-all duration-200"
          >
            View Projects Table
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5">
        {/* Total Projects */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 shadow-md flex items-center space-x-4">
          <div className="p-3 bg-brand-500/10 text-brand-400 rounded-xl">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total</h3>
            <p className="text-xl font-bold text-slate-100 mt-1">{stats.total}</p>
          </div>
        </div>

        {/* In Progress */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 shadow-md flex items-center space-x-4">
          <div className="p-3 bg-blue-500/10 text-blue-400 rounded-xl">
            <PlayCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Running</h3>
            <p className="text-xl font-bold text-slate-100 mt-1">{stats.running}</p>
          </div>
        </div>

        {/* Completed */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 shadow-md flex items-center space-x-4">
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
            <CheckCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Completed</h3>
            <p className="text-xl font-bold text-slate-100 mt-1">{stats.completed}</p>
          </div>
        </div>

        {/* Delayed */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 shadow-md flex items-center space-x-4">
          <div className="p-3 bg-rose-500/10 text-rose-400 rounded-xl">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Delayed</h3>
            <p className="text-xl font-bold text-slate-100 mt-1">{stats.delayed}</p>
          </div>
        </div>

        {/* Total Budget */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 shadow-md flex items-center space-x-4 xl:col-span-2">
          <div className="p-3 bg-amber-500/10 text-amber-400 rounded-xl">
            <IndianRupee className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Budget Summary</h3>
            <p className="text-xl font-bold text-slate-100 mt-1">
              ₹{stats.totalBudget.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Main split sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upcoming Deadlines (2 cols on large screen) */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-bold text-white flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-brand-400" />
            Upcoming Deadlines (Next 30 Days)
          </h2>

          {stats.upcomingDeadlines.length === 0 ? (
            <div className="glass-panel p-6 rounded-2xl text-center text-slate-400 border border-slate-800">
              No project deadlines expected in the next 30 days.
            </div>
          ) : (
            <div className="space-y-4">
              {stats.upcomingDeadlines.map(p => (
                <div key={p.id} className="glass-panel p-5 rounded-2xl border border-slate-800 flex justify-between items-center hover:border-slate-700 transition-colors">
                  <div className="space-y-1">
                    <Link to={`/projects/${p.id}`} className="text-sm font-semibold text-white hover:text-brand-300 transition-colors">
                      {p.project_name}
                    </Link>
                    <p className="text-xs text-slate-400">{p.client_name} • {p.location}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold text-amber-400 block">
                      Ends on {new Date(p.expected_end_date).toLocaleDateString()}
                    </span>
                    <span className={`inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-bold ${
                      p.status === 'Delayed' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                    }`}>
                      {p.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Info Box */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-white flex items-center">
            <Shield className="w-5 h-5 mr-2 text-brand-400" />
            Workspace Notes
          </h2>
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg mt-0.5">
                <FileText className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200">Drawings & Blueprints</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Always upload official PDFs to the Drawings repository. Site Engineers will cross-reference these for daily task reviews.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3 border-t border-slate-800/60 pt-4">
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg mt-0.5">
                <CheckCircle className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200">Site Status Reports</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Site Engineers can upload camera images directly using mobile devices. Capture dates are logged to generate daily galleries.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
