import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  getProjectInvoices, uploadInvoice, 
  getInvoice, analyzeInvoice, downloadInvoiceReport 
} from '../services/invoice';
import { getProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { 
  ArrowLeft, FileText, UploadCloud, ShieldAlert, AlertTriangle, 
  CheckCircle2, RefreshCw, Layers, FileSpreadsheet, Plus, 
  TrendingUp, Search, IndianRupee, Eye, Loader, CornerDownRight, X 
} from 'lucide-react';

const InvoiceDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  // Statuses
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Form uploader
  const [invoiceFile, setInvoiceFile] = useState(null);

  const loadData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);
      const invs = await getProjectInvoices(projectId);
      setInvoices(invs);
    } catch (err) {
      console.error(err);
      setError('Failed to retrieve project invoices registry.');
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
    if (!invoiceFile) return;

    setUploadLoading(true);
    setError('');
    try {
      await uploadInvoice(projectId, invoiceFile);
      setInvoiceFile(null);
      await loadData();
    } catch (err) {
      console.error(err);
      setError('Invoice file upload failed.');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleSelectInvoice = async (invoiceId) => {
    setError('');
    setAnalysisResult(null);
    try {
      const inv = await getInvoice(invoiceId);
      setSelectedInvoice(inv);
      
      // Auto trigger fetch analysis results if invoice is completed
      if (inv.status !== 'Pending' && inv.status !== 'Processing') {
        const analysis = await analyzeInvoice(invoiceId);
        setAnalysisResult(analysis);
      }
    } catch (err) {
      console.error(err);
      setError('Could not fetch invoice details.');
    }
  };

  const handleTriggerAnalysis = async () => {
    if (!selectedInvoice) return;
    setActionLoading(true);
    setError('');
    try {
      const analysis = await analyzeInvoice(selectedInvoice.id);
      setAnalysisResult(analysis);
      // Reload invoices list to capture updated status
      await loadData();
      
      // Update selected invoice details
      const updated = await getInvoice(selectedInvoice.id);
      setSelectedInvoice(updated);
    } catch (err) {
      console.error(err);
      setError('AI invoice analysis run failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownloadReport = async (format) => {
    if (!selectedInvoice) return;
    try {
      await downloadInvoiceReport(
        selectedInvoice.id, 
        format, 
        `invoice_audit_report_${selectedInvoice.invoice_number || selectedInvoice.id}`
      );
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

  const totalBilled = invoices.reduce((sum, inv) => sum + parseFloat(inv.total_amount || 0), 0);
  const duplicateAlerts = invoices.filter(inv => inv.status === 'Duplicate-Alert').length;
  const fraudAlerts = invoices.filter(inv => inv.status === 'Fraud-Alert').length;
  const canModify = user?.role === 'Admin' || user?.role === 'Project Manager';

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
            <h1 className="text-xl font-bold tracking-tight text-white">AI Invoice & OCR Cockpit</h1>
            <p className="text-xs text-slate-400 mt-1">
              Double-billing audit and budget reconciliation dashboard: <span className="text-slate-205 font-semibold">{project?.project_name}</span>
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-250 text-xs">
          {error}
        </div>
      )}

      {/* OVERVIEW STATS ROW */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Billed Costs</span>
          <span className="text-lg font-extrabold text-white mt-1 flex items-center">
            <IndianRupee className="w-4.5 h-4.5 mr-1.5 text-brand-450" />
            ₹{totalBilled.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Processed Invoices</span>
          <span className="text-lg font-extrabold text-white mt-1 flex items-center">
            <Layers className="w-4.5 h-4.5 mr-1.5 text-slate-500" />
            {invoices.length} Registered
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Double-Billing Alerts</span>
          <span className={`text-lg font-extrabold mt-1 flex items-center ${duplicateAlerts > 0 ? 'text-rose-450' : 'text-slate-400'}`}>
            <ShieldAlert className="w-4.5 h-4.5 mr-1.5" />
            {duplicateAlerts} flagged
          </span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-850">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">AI Fraud Warnings</span>
          <span className={`text-lg font-extrabold mt-1 flex items-center ${fraudAlerts > 0 ? 'text-amber-500' : 'text-slate-400'}`}>
            <AlertTriangle className="w-4.5 h-4.5 mr-1.5" />
            {fraudAlerts} flagged
          </span>
        </div>
      </div>

      {/* COCKPIT GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Upload and Invoices list ledger */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-850 space-y-4 shadow-lg h-[500px] flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Invoices Ledger</h3>
              <span className="text-[9px] text-slate-550">Double-click to select</span>
            </div>

            {/* Drag & Drop selector */}
            {canModify && (
              <form onSubmit={handleUploadSubmit} className="p-4 bg-slate-905 border border-dashed border-slate-800 rounded-xl flex flex-col items-center space-y-3">
                <input
                  type="file"
                  accept=".pdf,image/*"
                  required
                  onChange={(e) => setInvoiceFile(e.target.files[0])}
                  className="hidden"
                  id="invoice-file-picker"
                />
                <label 
                  htmlFor="invoice-file-picker"
                  className="cursor-pointer text-center flex flex-col items-center space-y-1.5 text-slate-400 hover:text-white transition-all"
                >
                  <UploadCloud className="w-8 h-8 text-brand-400 animate-bounce" />
                  <span className="text-xs font-semibold block">{invoiceFile ? invoiceFile.name : 'Select Invoice PDF/Image'}</span>
                  <span className="text-[9px] text-slate-550">Supported: PDF, PNG, JPG up to 10MB</span>
                </label>
                {invoiceFile && (
                  <button
                    type="submit"
                    disabled={uploadLoading}
                    className="w-full py-1.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-[10px] rounded-lg transition-all disabled:opacity-50"
                  >
                    {uploadLoading ? 'Uploading...' : 'Index Invoice'}
                  </button>
                )}
              </form>
            )}

            {/* List */}
            <div className="space-y-2 overflow-y-auto max-h-56 pr-1 scrollbar-thin">
              {invoices.length === 0 ? (
                <p className="text-xs text-slate-500 italic text-center py-4">No invoices uploaded yet.</p>
              ) : (
                invoices.map((inv) => (
                  <div 
                    key={inv.id}
                    onClick={() => handleSelectInvoice(inv.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                      selectedInvoice?.id === inv.id 
                        ? 'bg-brand-600/10 border-brand-500/30 text-white' 
                        : 'bg-slate-900/40 border-slate-850 hover:bg-slate-800 text-slate-350'
                    }`}
                  >
                    <div className="min-w-0">
                      <span className="text-xs font-bold block truncate">{inv.vendor_name || 'Processing...'}</span>
                      <span className="text-[9px] text-slate-500">
                        {inv.invoice_number ? `#${inv.invoice_number}` : 'OCR Extracting'} • ₹{parseFloat(inv.total_amount).toLocaleString('en-IN')}
                      </span>
                    </div>

                    <span className={`px-2 py-0.5 text-[8px] font-bold rounded-full ${
                      inv.status === 'Completed' ? 'bg-emerald-500/10 text-emerald-400' :
                      inv.status === 'Duplicate-Alert' ? 'bg-rose-500/10 text-rose-400 animate-pulse' :
                      inv.status === 'Fraud-Alert' ? 'bg-amber-500/10 text-amber-400 animate-pulse' :
                      inv.status === 'Processing' ? 'bg-indigo-500/10 text-indigo-400 animate-pulse' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {inv.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Detailed audit panel */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-850 flex flex-col justify-between shadow-lg h-[500px]">
          {!selectedInvoice ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500 italic">
              Choose an invoice from ledger to view reconciliation.
            </div>
          ) : (
            <div className="h-full flex flex-col justify-between space-y-4">
              
              {/* Top summary header */}
              <div className="flex justify-between items-start border-b border-slate-800/80 pb-3">
                <div className="min-w-0">
                  <h4 className="text-sm font-bold text-white truncate">{selectedInvoice.vendor_name || 'Extracting Vendor Info...'}</h4>
                  <span className="text-[10px] text-slate-400">
                    GSTIN: <span className="font-mono text-slate-300 font-semibold">{selectedInvoice.vendor_gst || 'N/A'}</span>
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDownloadReport('pdf')}
                    className="p-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-all"
                    title="Download Audit PDF"
                  >
                    <FileText className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDownloadReport('excel')}
                    className="p-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-all"
                    title="Export Audit CSV"
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                  </button>
                  {canModify && (
                    <button
                      onClick={handleTriggerAnalysis}
                      disabled={actionLoading || selectedInvoice.status === 'Pending' || selectedInvoice.status === 'Processing'}
                      className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-[10px] rounded-lg flex items-center shadow-lg transition-all disabled:opacity-50"
                    >
                      {actionLoading ? <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <TrendingUp className="w-3.5 h-3.5 mr-1.5" />}
                      Recheck AI Compliance
                    </button>
                  )}
                </div>
              </div>

              {/* Grid content */}
              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 min-h-0">
                
                {/* Variance comparison & line items */}
                <div className="space-y-3 flex flex-col min-h-0">
                  <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider block shrink-0">Line Items vs Budget Ceilings</span>
                  
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-thin">
                    {selectedInvoice.items?.length === 0 ? (
                      <p className="text-xs text-slate-500 italic text-center py-4">No items parsed yet.</p>
                    ) : (
                      selectedInvoice.items.map((item) => {
                        // Find matching comparison
                        const comparison = selectedInvoice.comparisons?.find(c => c.item_id === item.id);
                        const isOverrun = comparison && parseFloat(comparison.variance) > 0;
                        return (
                          <div key={item.id} className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl space-y-1.5">
                            <div className="flex justify-between text-xs">
                              <span className="font-semibold text-slate-200">{item.description}</span>
                              <span className="font-bold text-white">₹{parseFloat(item.total_price).toLocaleString('en-IN')}</span>
                            </div>
                            <div className="flex justify-between text-[9px] text-slate-500">
                              <span>Qty: {float(item.quantity)} x ₹{float(item.unit_price)}/unit</span>
                              {comparison && (
                                <span className={isOverrun ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                                  {isOverrun ? `Overrun: +₹${float(comparison.variance)}` : `Savings: ₹${Math.abs(float(comparison.variance))}`}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

                {/* Audit and Fraud alerts */}
                <div className="space-y-3 flex flex-col min-h-0 border-t md:border-t-0 md:border-l border-slate-800/80 md:pl-4">
                  <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider block shrink-0">Audit Indicators & Logs</span>
                  
                  <div className="flex-1 overflow-y-auto space-y-3 pr-1 scrollbar-thin">
                    {/* Duplicate Alerts */}
                    {selectedInvoice.is_duplicate && (
                      <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 rounded-xl text-xs flex items-start space-x-2">
                        <ShieldAlert className="w-5 h-5 shrink-0 animate-bounce" />
                        <div>
                          <span className="font-bold block">Double-Billing Conflict Detected</span>
                          <span>Invoice #{selectedInvoice.invoice_number} is duplicate of Invoice ID {selectedInvoice.duplicate_parent_id}.</span>
                        </div>
                      </div>
                    )}

                    {/* Fraud score gauge */}
                    {analysisResult && (
                      <div className="p-3 bg-slate-900 border border-slate-850 rounded-xl space-y-2">
                        <div className="flex justify-between items-center text-[10px] font-bold">
                          <span className="text-slate-400 uppercase tracking-wider">AI Fraud Risk Index</span>
                          <span className={parseFloat(analysisResult.fraud_risk_score) > 60 ? 'text-rose-400' : 'text-emerald-400'}>
                            {parseFloat(analysisResult.fraud_risk_score)} / 100
                          </span>
                        </div>
                        <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all ${
                              parseFloat(analysisResult.fraud_risk_score) > 60 ? 'bg-rose-500' : 'bg-emerald-500'
                            }`}
                            style={{ width: `${parseFloat(analysisResult.fraud_risk_score)}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* AI reconciliation suggestions */}
                    {analysisResult?.ai_fraud_recommendations && (
                      <div className="p-3 bg-slate-900/60 border border-slate-900 rounded-xl space-y-2">
                        <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-wider block">AI Reconciliation Plan</span>
                        <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line pl-2 border-l-2 border-brand-500">
                          {analysisResult.ai_fraud_recommendations}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

              </div>

            </div>
          )}
        </div>

      </div>
    </div>
  );
};

// Quick helper to convert SQLite decimal strings into standard decimals
const float = (strVal) => {
  return parseFloat(strVal || 0.0);
};

export default InvoiceDashboard;
