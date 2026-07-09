import React, { useEffect, useState } from 'react';
import { getProjects } from '../services/projects';
import { downloadReport } from '../services/reports';
import { 
  FileText, FileSpreadsheet, Download, RefreshCw, Sparkles, 
  Layers, CheckCircle, AlertCircle, Info, HelpCircle
} from 'lucide-react';

const ReportCenter = () => {
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [selectedType, setSelectedType] = useState('project_summary');
  const [selectedFormat, setSelectedFormat] = useState('pdf');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const fetchProjectsList = async () => {
    try {
      setLoading(true);
      const response = await getProjects();
      const items = response.items || [];
      setProjects(items);
      if (items.length > 0) {
        setSelectedProject(items[0].id);
      }
    } catch (err) {
      console.error("Failed to load projects list in report center: ", err);
      setError("Failed to initialize projects selection catalog.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectsList();
  }, []);

  const handleExport = async (e) => {
    e.preventDefault();
    if (!selectedProject) {
      setError("Please select a project to proceed.");
      return;
    }

    try {
      setExporting(true);
      setError('');
      setMessage('Compiling report data and generating files...');
      
      const blob = await downloadReport(selectedProject, selectedType, selectedFormat);
      
      // Setup download trigger
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      
      const ext = selectedFormat === 'pdf' ? 'pdf' : 'csv';
      link.setAttribute('download', `${selectedType}_report_project_${selectedProject}.${ext}`);
      
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      
      setMessage('Export completed successfully! Check your downloads directory.');
    } catch (err) {
      console.error("Failed to download ledger report: ", err);
      setError("Export execution crashed. Check server logs or permission levels.");
    } finally {
      setExporting(false);
    }
  };

  const reportTypesList = [
    { id: 'project_summary', title: 'Project Overview Summary', desc: 'Core contract details, client profile, and overall completion flags.' },
    { id: 'budget', title: 'Budget Estimation Ledger', desc: 'Itemized material vs. labor costs estimates and AI budget target overrides.' },
    { id: 'material', title: 'Material Quantities Report', desc: 'Aggregate materials needed for the structure matching warehouse stock levels.' },
    { id: 'worker', title: 'Workforce Roster Sheet', desc: 'Daily labor schedulers list, shift allocations, and active trade classifications.' },
    { id: 'attendance', title: 'Attendance Audit Records', desc: 'Audit sheet of daily check-ins, recorded hours, and overtime workloads.' },
    { id: 'risk', title: 'Risk Audit Timeline', desc: 'Chronological composite risk index, delay predictions, and severe forecast logs.' },
    { id: 'invoice', title: 'Invoice Auditor Log', desc: 'OCR verification logs, vendor names, total tax, and budget comparison states.' },
    { id: 'image_analysis', title: 'Visual Safety Audits', desc: 'Hazards list compiled during visual audits (missing PPE vests, hardhats).' },
    { id: 'drawing', title: 'Blueprint RAG Catalog', desc: 'Indexed technical blueprints specifications, vector references, and RAG logs.' },
    { id: 'executive', title: 'Executive Oversight KPIs', desc: 'Combined summary KPIs (materials shortages, worker deficits, and active cost overruns).' },
    { id: 'progress', title: 'Milestones Completion Logs', desc: 'Chronological timeline metrics, planned vs actual variance days, and daily notes.' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900 text-white">
        <div className="text-center">
          <RefreshCw className="h-10 w-10 animate-spin text-indigo-500 mx-auto mb-4" />
          <p className="text-slate-400 font-medium">Assembling file templates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Title */}
      <div className="mb-8 pb-5 border-b border-slate-800">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm tracking-wider uppercase">
          <FileText className="h-4 w-4" />
          APEXBuild Document Exporter
        </div>
        <h1 className="text-3xl font-extrabold text-white mt-1">Multi-Format Project Report Center</h1>
        <p className="text-slate-400 mt-1 text-sm">Download operational metrics as styled PDFs, standardized CSV catalogs, or Excel spreadsheet structures.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Options Form */}
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-6 h-fit">
          <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-400" />
            Export Settings
          </h2>

          <form onSubmit={handleExport} className="space-y-6">
            {/* 1. Project */}
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Target Project</label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full bg-slate-850 border border-slate-700 rounded-lg py-2.5 px-3.5 text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">Select Project</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.project_name}</option>
                ))}
              </select>
            </div>

            {/* 2. Format Selection */}
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase mb-2">Export Format</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'pdf', label: 'PDF Doc', icon: FileText },
                  { id: 'csv', label: 'CSV Tabular', icon: FileSpreadsheet },
                  { id: 'excel', label: 'Excel Sheet', icon: FileSpreadsheet }
                ].map((fmt) => {
                  const Icon = fmt.icon;
                  const active = selectedFormat === fmt.id;
                  return (
                    <button
                      key={fmt.id}
                      type="button"
                      onClick={() => setSelectedFormat(fmt.id)}
                      className={`flex flex-col items-center justify-center py-3 rounded-lg border text-xs transition duration-200 ${
                        active 
                          ? 'bg-indigo-500/20 border-indigo-500 text-indigo-300 font-semibold' 
                          : 'bg-slate-850 border-slate-700 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                      }`}
                    >
                      <Icon className="h-5 w-5 mb-1.5" />
                      {fmt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Status alerts */}
            {message && (
              <div className="bg-indigo-950/40 border border-indigo-900 rounded-lg p-3.5 flex gap-2.5 text-xs text-indigo-300">
                <Info className="h-4.5 w-4.5 flex-shrink-0" />
                <p>{message}</p>
              </div>
            )}

            {error && (
              <div className="bg-rose-950/40 border border-rose-900 rounded-lg p-3.5 flex gap-2.5 text-xs text-rose-300">
                <AlertCircle className="h-4.5 w-4.5 flex-shrink-0" />
                <p>{error}</p>
              </div>
            )}

            {/* Button */}
            <button
              type="submit"
              disabled={exporting}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed group shadow-lg shadow-indigo-600/20"
            >
              {exporting ? (
                <>
                  <RefreshCw className="h-4.5 w-4.5 animate-spin" />
                  Generating Ledger...
                </>
              ) : (
                <>
                  <Download className="h-4.5 w-4.5 group-hover:translate-y-0.5 transition-transform" />
                  Download File
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Choices Catalog list */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-400" />
            Select Report Template
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {reportTypesList.map((type) => {
              const active = selectedType === type.id;
              return (
                <div
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  className={`border rounded-xl p-4.5 cursor-pointer transition duration-200 relative group overflow-hidden ${
                    active 
                      ? 'bg-indigo-950/20 border-indigo-500 text-slate-100 shadow-md shadow-indigo-500/5' 
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:bg-slate-850'
                  }`}
                >
                  {active && (
                    <div className="absolute top-0 right-0 bg-indigo-500 text-white text-xxs font-bold px-2 py-0.5 rounded-bl">
                      Selected
                    </div>
                  )}
                  <h3 className={`text-sm font-bold mb-1 ${active ? 'text-white' : 'text-slate-300'}`}>
                    {type.title}
                  </h3>
                  <p className="text-xs leading-relaxed text-slate-400">{type.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportCenter;
