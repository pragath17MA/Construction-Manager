import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  getWorkers, createWorker, updateWorker, deleteWorker, 
  runShiftPlanner, getProjectSchedules, logAttendance, 
  getAttendance, submitLeaveRequest, getLeaveRequests, 
  approveLeaveRequest, downloadAttendanceCsv, downloadWorkerReportPdf 
} from '../services/workers';
import { getProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { Bar, Pie } from 'react-chartjs-2';
import { 
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, 
  Title, Tooltip, Legend, ArcElement 
} from 'chart.js';
import { 
  ArrowLeft, Users, Calendar, FileText, FileSpreadsheet, Plus, 
  Trash2, Edit2, Check, X, ShieldAlert, BadgeHelp, IndianRupee, 
  Sparkles, RefreshCw, Loader, Clock, UserCheck, AlertTriangle
} from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const WorkersDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [workers, setWorkers] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview'); // overview, workers, shifts, attendance, leaves
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [optimizerOutput, setOptimizerOutput] = useState(null);

  // Date selectors for Shift Planner
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date(Date.now() + 7*24*60*60*1000).toISOString().split('T')[0]);

  // Worker Form State
  const [showWorkerModal, setShowWorkerModal] = useState(false);
  const [editingWorkerId, setEditingWorkerId] = useState(null);
  const [workerForm, setWorkerForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    role_title: 'Mason',
    worker_type: 'Skilled',
    wage_rate: '',
    skills_text: '' // comma separated
  });

  // Daily Attendance Log form state
  const [attendanceLogs, setAttendanceLogs] = useState({}); // worker_id: { status, hours_worked, overtime_hours }
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0]);

  // Leave Form State
  const [leaveForm, setLeaveForm] = useState({
    worker_id: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 2*24*60*60*1000).toISOString().split('T')[0],
    leave_type: 'Sick',
    reason: ''
  });

  const loadAllData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);

      const staff = await getWorkers();
      setWorkers(staff);

      const scheds = await getProjectSchedules(projectId);
      setSchedules(scheds);

      const logs = await getAttendance();
      setAttendance(logs);

      const leaves = await getLeaveRequests();
      setLeaveRequests(leaves);

      // Setup initial attendance log inputs matching active roster
      const initialLogs = {};
      staff.forEach(w => {
        initialLogs[w.id] = { status: 'Present', hours_worked: '8', overtime_hours: '0' };
      });
      setAttendanceLogs(initialLogs);

    } catch (err) {
      console.error(err);
      setError('Failed to retrieve project worker rosters.');
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadAllData();
      setLoading(false);
    };
    init();
  }, [projectId]);

  const handleWorkerSubmit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    const { full_name, email, phone, role_title, worker_type, wage_rate, skills_text } = workerForm;
    
    // Parse skills
    const skills = skills_text.split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0)
      .map(s => ({ skill_name: s, proficiency_level: 'Intermediate' }));

    const payload = {
      full_name,
      email,
      phone,
      role_title,
      worker_type,
      wage_rate: parseFloat(wage_rate),
      skills
    };

    try {
      if (editingWorkerId) {
        await updateWorker(editingWorkerId, payload);
      } else {
        await createWorker(payload);
      }
      setShowWorkerModal(false);
      setWorkerForm({ full_name: '', email: '', phone: '', role_title: 'Mason', worker_type: 'Skilled', wage_rate: '', skills_text: '' });
      setEditingWorkerId(null);
      await loadAllData();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to save worker profile.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteWorker = async (id) => {
    if (window.confirm('Delete this worker profile permanently?')) {
      try {
        await deleteWorker(id);
        await loadAllData();
      } catch (err) {
        console.error(err);
        alert('Failed to delete worker.');
      }
    }
  };

  const handleRunShiftPlanner = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      const resp = await runShiftPlanner({
        project_id: parseInt(projectId),
        start_date: startDate,
        end_date: endDate
      });
      setOptimizerOutput(resp);
      await loadAllData();
    } catch (err) {
      console.error(err);
      alert('AI Shift planner run failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleLogSingleAttendance = async (workerId) => {
    const log = attendanceLogs[workerId];
    if (!log) return;
    try {
      await logAttendance({
        worker_id: parseInt(workerId),
        date: attendanceDate,
        status: log.status,
        hours_worked: parseFloat(log.hours_worked),
        overtime_hours: parseFloat(log.overtime_hours)
      });
      alert('Attendance logged successfully.');
      await loadAllData();
    } catch (err) {
      console.error(err);
      alert('Failed to log attendance.');
    }
  };

  const handleLeaveSubmit = async (e) => {
    e.preventDefault();
    if (!leaveForm.worker_id) {
      alert('Please select a worker.');
      return;
    }
    try {
      await submitLeaveRequest({
        worker_id: parseInt(leaveForm.worker_id),
        start_date: leaveForm.start_date,
        end_date: leaveForm.end_date,
        leave_type: leaveForm.leave_type,
        reason: leaveForm.reason
      });
      setLeaveForm({ worker_id: '', start_date: new Date().toISOString().split('T')[0], end_date: new Date(Date.now() + 2*24*60*60*1000).toISOString().split('T')[0], leave_type: 'Sick', reason: '' });
      await loadAllData();
    } catch (err) {
      console.error(err);
      alert('Failed to file leave request.');
    }
  };

  const handleApproveLeave = async (id, status) => {
    try {
      await approveLeaveRequest(id, status);
      await loadAllData();
    } catch (err) {
      console.error(err);
      alert('Failed to update leave request status.');
    }
  };

  const handleDownloadCsv = async () => {
    try {
      await downloadAttendanceCsv(`attendance_report_project_${projectId}.csv`);
    } catch (err) {
      console.error(err);
      alert('Attendance CSV download failed.');
    }
  };

  const handleDownloadPdfReport = async () => {
    try {
      await downloadWorkerReportPdf(projectId, startDate, endDate, `shift_schedule_project_${projectId}.pdf`);
    } catch (err) {
      console.error(err);
      alert('PDF roster generation failed.');
    }
  };

  // Compile calculations
  const totalWorkers = workers.length;
  const activeSchedules = schedules.length;
  const pendingLeaves = leaveRequests.filter(l => l.status === 'Pending').length;
  
  // Chart configurations
  const rolesList = [...new Set(workers.map(w => w.role_title))];
  const pieData = {
    labels: rolesList,
    datasets: [{
      data: rolesList.map(r => workers.filter(w => w.role_title === r).length),
      backgroundColor: ['#6366f1', '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#14b8a6'],
      borderWidth: 1,
      borderColor: '#0f172a'
    }]
  };

  const canModify = user?.role === 'Admin' || user?.role === 'Project Manager';

  return (
    <div className="space-y-6">
      {/* Header Cockpit */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div className="flex items-center space-x-3">
          <Link
            to={`/projects/${projectId}`}
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">AI Worker Scheduling cockpit</h1>
            <p className="text-xs text-slate-400 mt-1">
              Active shifts for project: <span className="text-slate-200 font-semibold">{project?.project_name}</span>
            </p>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleDownloadCsv}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-855 text-slate-200 font-semibold text-xs rounded-xl border border-slate-800 flex items-center transition-all"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5" />
            Export Attendance CSV
          </button>
          {canModify && (
            <button
              onClick={() => {
                setEditingWorkerId(null);
                setWorkerForm({ full_name: '', email: '', phone: '', role_title: 'Mason', worker_type: 'Skilled', wage_rate: '', skills_text: '' });
                setShowWorkerModal(true);
              }}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl flex items-center shadow-lg transition-all"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Add System Worker
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-250 text-xs">
          {error}
        </div>
      )}

      {/* RENDER STATS METRICS CARDS */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total workers Pool</span>
          <span className="text-lg font-extrabold text-white mt-1 flex items-center">
            <Users className="w-4.5 h-4.5 mr-1.5 text-slate-500" />
            {totalWorkers} staff
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Active Shift Allocations</span>
          <span className="text-lg font-extrabold text-white mt-1 flex items-center">
            <Clock className="w-4.5 h-4.5 mr-1.5 text-slate-500" />
            {activeSchedules} active
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Attendance Rate</span>
          <span className="text-lg font-extrabold text-emerald-400 mt-1 flex items-center">
            <UserCheck className="w-4.5 h-4.5 mr-1.5" />
            94.2%
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Pending leaves reviews</span>
          <span className={`text-lg font-extrabold mt-1 flex items-center ${pendingLeaves > 0 ? 'text-amber-500' : 'text-slate-400'}`}>
            <AlertTriangle className="w-4.5 h-4.5 mr-1.5" />
            {pendingLeaves} pending
          </span>
        </div>
      </div>

      {/* Tabs list selectors */}
      <div className="flex border-b border-slate-850 space-x-6 text-xs font-bold uppercase tracking-wider">
        {['overview', 'workers', 'shifts', 'attendance', 'leaves'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 border-b-2 transition-all ${
              activeTab === tab ? 'border-brand-500 text-white' : 'border-transparent text-slate-450 hover:text-slate-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="glass-panel p-5 rounded-2xl border border-slate-850 flex flex-col items-center">
            <h3 className="text-xs font-semibold text-slate-350 mb-4 text-center">Trades & Roles Ratios</h3>
            <div className="w-52 h-52">
              <Pie data={pieData} options={{ plugins: { legend: { display: false } } }} />
            </div>
          </div>

          <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-850 space-y-4">
            <div className="flex items-center space-x-2 text-indigo-400">
              <Sparkles className="w-5 h-5 animate-pulse" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Shift Optimization Roster</h3>
            </div>
            {optimizerOutput ? (
              <div className="space-y-4">
                <div className="p-3 bg-indigo-950/20 border border-indigo-500/20 rounded-xl text-xs text-slate-300 whitespace-pre-line leading-relaxed pl-3 border-l-2 border-brand-500">
                  {optimizerOutput.optimization_summary}
                </div>
                {optimizerOutput.shortage_warnings?.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-amber-500 uppercase tracking-wide">AI Shortage warnings:</h4>
                    {optimizerOutput.shortage_warnings.map((warn, i) => (
                      <div key={i} className="p-2.5 bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs rounded-xl">
                        {warn}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6 text-slate-500 text-xs">
                No active optimization roster generated. Run the scheduler in the "Shifts" tab.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: SYSTEM WORKERS LIST */}
      {activeTab === 'workers' && (
        <div className="glass-panel rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
          <table className="min-w-full divide-y divide-slate-850">
            <thead className="bg-slate-900/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Worker Name</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Role & Class</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Contact</th>
                <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Daily Wage</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Skills list</th>
                {canModify && <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-850/60 bg-transparent text-xs text-slate-300">
              {workers.map((w) => (
                <tr key={w.id} className="hover:bg-slate-900/20 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-200">{w.full_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mr-2">
                      {w.role_title}
                    </span>
                    <span className="text-[10px] text-slate-400 font-semibold">{w.worker_type}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-slate-450">{w.email} • {w.phone}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right font-semibold text-white">
                    ₹{parseFloat(w.wage_rate).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-wrap gap-1.5">
                      {w.skills?.map((s, idx) => (
                        <span key={idx} className="bg-slate-850 text-slate-300 px-1.5 py-0.5 rounded text-[9px]">
                          {s.skill_name}
                        </span>
                      ))}
                    </div>
                  </td>
                  {canModify && (
                    <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                      <button
                        onClick={() => {
                          setEditingWorkerId(w.id);
                          setWorkerForm({
                            full_name: w.full_name,
                            email: w.email,
                            phone: w.phone,
                            role_title: w.role_title,
                            worker_type: w.worker_type,
                            wage_rate: w.wage_rate.toString(),
                            skills_text: w.skills?.map(s => s.skill_name).join(', ') || ''
                          });
                          setShowWorkerModal(true);
                        }}
                        className="p-1.5 bg-slate-850 hover:bg-slate-800 text-slate-450 hover:text-white rounded border border-transparent"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteWorker(w.id)}
                        className="p-1.5 bg-slate-850 hover:bg-rose-500/10 text-slate-450 hover:text-rose-400 rounded border border-transparent"
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
      )}

      {/* TAB 3: SHIFT PLANS AND ROSTERS */}
      {activeTab === 'shifts' && (
        <div className="space-y-6">
          {canModify && (
            <div className="glass-panel p-6 rounded-2xl border border-slate-850">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">Run AI Shift Roster Planner</h3>
              <form onSubmit={handleRunShiftPlanner} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Start Date</label>
                  <input
                    type="date"
                    required
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">End Date</label>
                  <input
                    type="date"
                    required
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
                <div className="flex space-x-2">
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="flex-1 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl shadow-md h-9 flex items-center justify-center disabled:opacity-50"
                  >
                    {actionLoading ? <Loader className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 mr-1.5" />}
                    Optimize Shift plans
                  </button>
                  {schedules.length > 0 && (
                    <button
                      type="button"
                      onClick={handleDownloadPdfReport}
                      className="px-3 py-2 bg-slate-900 hover:bg-slate-850 text-slate-350 hover:text-white rounded-xl border border-slate-800 h-9"
                      title="Download PDF Schedule Roster"
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </form>
            </div>
          )}

          {/* Roster table list */}
          <div className="glass-panel rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
            <table className="min-w-full divide-y divide-slate-850">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Worker Name</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Shift Rotation</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Start Date</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">End Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850/60 bg-transparent text-xs text-slate-300">
                {schedules.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-900/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-200">{s.worker?.full_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-slate-400">{s.worker?.role_title}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        s.shift_type === 'Day' ? 'bg-amber-500/10 text-amber-450 border-amber-500/20' :
                        'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                      }`}>
                        {s.shift_type} Shift
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-slate-450">{new Date(s.start_date).toLocaleDateString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-slate-450">{new Date(s.end_date).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: ATTENDANCE SHEETS */}
      {activeTab === 'attendance' && (
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Date context:</span>
              <input
                type="date"
                value={attendanceDate}
                onChange={(e) => setAttendanceDate(e.target.value)}
                className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
              />
            </div>
            <span className="text-[10px] text-slate-500 italic">Engineers and PMs log daily rosters here.</span>
          </div>

          <div className="glass-panel rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
            <table className="min-w-full divide-y divide-slate-850">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Worker Name</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Roster status</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Hours worked</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Overtime Hours</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850/60 bg-transparent text-xs text-slate-300">
                {workers.map((w) => {
                  const log = attendanceLogs[w.id] || { status: 'Present', hours_worked: '8', overtime_hours: '0' };
                  return (
                    <tr key={w.id} className="hover:bg-slate-900/20 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-200">
                        {w.full_name}
                        <span className="block text-[9px] text-slate-450 font-semibold">{w.role_title}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <select
                          value={log.status}
                          onChange={(e) => setAttendanceLogs(prev => ({
                            ...prev,
                            [w.id]: { ...log, status: e.target.value }
                          }))}
                          className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-xs text-white"
                        >
                          <option value="Present">Present</option>
                          <option value="Absent">Absent</option>
                          <option value="Late">Late</option>
                        </select>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <input
                          type="number"
                          value={log.hours_worked}
                          onChange={(e) => setAttendanceLogs(prev => ({
                            ...prev,
                            [w.id]: { ...log, hours_worked: e.target.value }
                          }))}
                          className="w-16 px-2 py-1 bg-slate-900 border border-slate-800 rounded text-right text-white"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <input
                          type="number"
                          value={log.overtime_hours}
                          onChange={(e) => setAttendanceLogs(prev => ({
                            ...prev,
                            [w.id]: { ...log, overtime_hours: e.target.value }
                          }))}
                          className="w-16 px-2 py-1 bg-slate-900 border border-slate-800 rounded text-right text-white"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={() => handleLogSingleAttendance(w.id)}
                          className="px-3 py-1 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-[10px] rounded"
                        >
                          Log
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: LEAVES MANAGEMENT */}
      {activeTab === 'leaves' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Leave Request Form */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-850 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">File Worker Leave request</h3>
            <form onSubmit={handleLeaveSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Worker profile</label>
                <select
                  required
                  value={leaveForm.worker_id}
                  onChange={(e) => setLeaveForm(prev => ({ ...prev, worker_id: e.target.value }))}
                  className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                >
                  <option value="">Select Worker...</option>
                  {workers.map(w => (
                    <option key={w.id} value={w.id}>{w.full_name} ({w.role_title})</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Start Date</label>
                  <input
                    type="date"
                    required
                    value={leaveForm.start_date}
                    onChange={(e) => setLeaveForm(prev => ({ ...prev, start_date: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">End Date</label>
                  <input
                    type="date"
                    required
                    value={leaveForm.end_date}
                    onChange={(e) => setLeaveForm(prev => ({ ...prev, end_date: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Leave Category</label>
                <select
                  value={leaveForm.leave_type}
                  onChange={(e) => setLeaveForm(prev => ({ ...prev, leave_type: e.target.value }))}
                  className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                >
                  <option value="Sick">Sick Leave</option>
                  <option value="Casual">Casual Leave</option>
                  <option value="Earned">Earned Leave</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Reason</label>
                <textarea
                  placeholder="Reason for requested leaves..."
                  value={leaveForm.reason}
                  onChange={(e) => setLeaveForm(prev => ({ ...prev, reason: e.target.value }))}
                  className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white h-16 resize-none"
                />
              </div>
              <button
                type="submit"
                className="w-full px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs border border-slate-700 rounded-xl shadow transition-all"
              >
                Submit Leave request
              </button>
            </form>
          </div>

          {/* Pending leave list */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Leave Requests Ledger</h3>
            <div className="space-y-3">
              {leaveRequests.length === 0 ? (
                <div className="text-center py-8 bg-slate-900/40 border border-slate-850 rounded-xl text-slate-500 text-xs">
                  No leave requests submitted.
                </div>
              ) : (
                leaveRequests.map((req) => (
                  <div key={req.id} className="glass-panel p-4 rounded-xl border border-slate-850 flex items-center justify-between shadow-sm">
                    <div className="space-y-1">
                      <h4 className="text-xs font-bold text-white">{req.worker?.full_name}</h4>
                      <span className="text-[10px] text-slate-450 block">
                        Dates: {new Date(req.start_date).toLocaleDateString()} to {new Date(req.end_date).toLocaleDateString()} • Type: {req.leave_type}
                      </span>
                      {req.reason && <p className="text-[10px] text-slate-400 italic">Reason: {req.reason}</p>}
                    </div>

                    <div className="flex items-center space-x-2">
                      {req.status === 'Pending' && canModify ? (
                        <>
                          <button
                            onClick={() => handleApproveLeave(req.id, 'Approved')}
                            className="p-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 rounded"
                            title="Approve"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleApproveLeave(req.id, 'Rejected')}
                            className="p-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-455 border border-rose-500/30 rounded"
                            title="Reject"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </>
                      ) : (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          req.status === 'Approved' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                          req.status === 'Rejected' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                          'bg-slate-800 text-slate-400 border-slate-700'
                        }`}>
                          {req.status}
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* CREATE WORKER PROFILE MODAL */}
      {showWorkerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel max-w-md w-full p-6 rounded-2xl border border-slate-800 space-y-4 relative shadow-2xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              {editingWorkerId ? 'Modify Worker Profile' : 'Register New System Worker'}
            </h3>
            <form onSubmit={handleWorkerSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Full Name</label>
                <input
                  type="text"
                  required
                  value={workerForm.full_name}
                  onChange={(e) => setWorkerForm(prev => ({ ...prev, full_name: e.target.value }))}
                  className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Email Address</label>
                  <input
                    type="email"
                    required
                    value={workerForm.email}
                    onChange={(e) => setWorkerForm(prev => ({ ...prev, email: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Phone Number</label>
                  <input
                    type="text"
                    required
                    value={workerForm.phone}
                    onChange={(e) => setWorkerForm(prev => ({ ...prev, phone: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-455 uppercase tracking-wider mb-2">Role/Trade</label>
                  <select
                    value={workerForm.role_title}
                    onChange={(e) => setWorkerForm(prev => ({ ...prev, role_title: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  >
                    <option value="Mason">Mason</option>
                    <option value="Electrician">Electrician</option>
                    <option value="Plumber">Plumber</option>
                    <option value="Supervisor">Supervisor</option>
                    <option value="Operator">Operator</option>
                    <option value="Carpenter">Carpenter</option>
                    <option value="Painter">Painter</option>
                    <option value="Engineer">Engineer</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-455 uppercase tracking-wider mb-2">Class</label>
                  <select
                    value={workerForm.worker_type}
                    onChange={(e) => setWorkerForm(prev => ({ ...prev, worker_type: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  >
                    <option value="Skilled">Skilled</option>
                    <option value="Semi-Skilled">Semi-Skilled</option>
                    <option value="Unskilled">Unskilled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-455 uppercase tracking-wider mb-2">Daily Wage (₹)</label>
                  <input
                    type="number"
                    required
                    value={workerForm.wage_rate}
                    onChange={(e) => setWorkerForm(prev => ({ ...prev, wage_rate: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Skills Tags (comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g. Concrete mix, Brickwork, Wiring"
                  value={workerForm.skills_text}
                  onChange={(e) => setWorkerForm(prev => ({ ...prev, skills_text: e.target.value }))}
                  className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowWorkerModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl disabled:opacity-50"
                >
                  {editingWorkerId ? 'Save changes' : 'Add Worker'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkersDashboard;
