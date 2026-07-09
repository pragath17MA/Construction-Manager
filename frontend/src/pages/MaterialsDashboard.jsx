import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  getProjectMaterials, estimateMaterials, updateMaterialLine, 
  deleteMaterialLine, getInventory, updateInventory, 
  getSuppliers, createPurchaseOrder, getPurchaseOrders, downloadMaterialsCsv 
} from '../services/materials';
import { getProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { Pie, Bar } from 'react-chartjs-2';
import { 
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, 
  Title, Tooltip, Legend, ArcElement 
} from 'chart.js';
import { 
  ArrowLeft, Hammer, FileSpreadsheet, Plus, Trash2, Edit2, 
  Check, X, Truck, AlertTriangle, CheckCircle2, IndianRupee, 
  Sparkles, RefreshCw, Loader, ShoppingBag, Layers
} from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const MaterialsDashboard = () => {
  const { projectId } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [materials, setMaterials] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  
  // States for LangGraph outputs
  const [warnings, setWarnings] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [optimizationSummary, setOptimizationSummary] = useState('');
  
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview'); // overview, list, inventory, suppliers, po
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Edit Material State
  const [editingId, setEditingId] = useState(null);
  const [editQty, setEditQty] = useState('');
  const [editPrice, setEditPrice] = useState('');

  // PO Creation Form State
  const [poForm, setPoForm] = useState({
    material_name: '',
    supplier_id: '',
    quantity: '',
    unit_price: ''
  });
  const [poError, setPoError] = useState('');

  // Inventory Update Form State
  const [invForm, setInvForm] = useState({
    material_name: '',
    quantity_change: ''
  });

  // Run Estimator Modal/Form States
  const [estimatorForm, setEstimatorForm] = useState({
    area_sqft: '',
    floors: '1',
    building_type: 'Residential',
    rooms: '2',
    timeline_months: '12',
    budget: '',
    project_category: 'Residential'
  });
  const [showEstimatorModal, setShowEstimatorModal] = useState(false);

  const loadAllData = async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);
      
      // Pre-fill estimator inputs from project scope
      setEstimatorForm(prev => ({
        ...prev,
        area_sqft: '4000',
        budget: proj.budget ? proj.budget.toString() : '5000000',
        project_category: 'Residential'
      }));

      const mats = await getProjectMaterials(projectId);
      setMaterials(mats);

      const inv = await getInventory();
      setInventory(inv);

      const sups = await getSuppliers();
      setSuppliers(sups);

      const pos = await getPurchaseOrders(projectId);
      setPurchaseOrders(pos);

      // Re-trigger LangGraph client analysis if materials exist
      if (mats.length > 0) {
        // Mock matching shortages and recommendations on load to keep state robust
        const lowStock = [];
        const recs = [];
        mats.forEach(m => {
          const invItem = inv.find(i => i.material_name.toLowerCase() === m.material_name.toLowerCase());
          const net = invItem ? parseFloat(invItem.quantity_available) - parseFloat(invItem.quantity_reserved) : 0;
          if (net < parseFloat(m.quantity)) {
            lowStock.push(`Low Stock Alert: '${m.material_name}' needs ${parseFloat(m.quantity)} but warehouse only holds ${net}.`);
            // Add supplier recommendation
            const matchedSups = sups.filter(s => s.active).sort((a,b) => b.rating - a.rating);
            if (matchedSups.length > 0) {
              recs.push({
                material_name: m.material_name,
                supplier_id: matchedSups[0].id,
                supplier_name: matchedSups[0].supplier_name,
                rating: matchedSups[0].rating,
                unit_price: m.unit_price,
                availability_status: 'Ready to Deliver'
              });
            }
          }
        });
        setWarnings(lowStock);
        setRecommendations(recs);
      }

    } catch (err) {
      console.error(err);
      setError('Failed to retrieve material planning schedules.');
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

  const handleRunEstimator = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    setError('');
    try {
      const resp = await estimateMaterials({
        project_id: parseInt(projectId),
        area_sqft: parseFloat(estimatorForm.area_sqft),
        floors: parseInt(estimatorForm.floors),
        building_type: estimatorForm.building_type,
        rooms: parseInt(estimatorForm.rooms),
        timeline_months: parseInt(estimatorForm.timeline_months),
        budget: parseFloat(estimatorForm.budget),
        project_category: estimatorForm.project_category
      });
      setMaterials(resp.materials);
      setWarnings(resp.low_stock_warnings);
      setRecommendations(resp.supplier_recommendations);
      setOptimizationSummary(resp.optimization_summary);
      setShowEstimatorModal(false);
      await loadAllData();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'AI material estimation run failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEditSave = async (id) => {
    if (!editQty || parseFloat(editQty) <= 0 || !editPrice || parseFloat(editPrice) <= 0) {
      alert('Inputs must be positive numbers.');
      return;
    }
    try {
      await updateMaterialLine(id, parseFloat(editQty), parseFloat(editPrice));
      setEditingId(null);
      await loadAllData();
    } catch (err) {
      console.error(err);
      alert('Failed to update material details.');
    }
  };

  const handleDeleteLine = async (id) => {
    if (window.confirm('Delete this estimated material item?')) {
      try {
        await deleteMaterialLine(id);
        await loadAllData();
      } catch (err) {
        console.error(err);
        alert('Failed to delete material line.');
      }
    }
  };

  const handleInventoryUpdate = async (e) => {
    e.preventDefault();
    if (!invForm.material_name || !invForm.quantity_change) return;
    try {
      await updateInventory({
        material_name: invForm.material_name,
        quantity_change: parseFloat(invForm.quantity_change)
      });
      setInvForm({ material_name: '', quantity_change: '' });
      await loadAllData();
    } catch (err) {
      console.error(err);
      alert('Failed to modify warehouse inventory levels.');
    }
  };

  const handleCreatePO = async (e) => {
    e.preventDefault();
    setPoError('');
    const { material_name, supplier_id, quantity, unit_price } = poForm;
    if (!material_name || !supplier_id || !quantity || !unit_price) {
      setPoError('All purchase fields are required.');
      return;
    }
    try {
      await createPurchaseOrder({
        project_id: parseInt(projectId),
        supplier_id: parseInt(supplier_id),
        material_name,
        quantity: parseFloat(quantity),
        unit_price: parseFloat(unit_price)
      });
      setPoForm({ material_name: '', supplier_id: '', quantity: '', unit_price: '' });
      await loadAllData();
    } catch (err) {
      console.error(err);
      setPoError(err.response?.data?.detail || 'Failed to file purchase order.');
    }
  };

  const handleDownloadCsv = async () => {
    try {
      await downloadMaterialsCsv(projectId, `materials_estimate_project_${projectId}.csv`);
    } catch (err) {
      console.error(err);
      alert('CSV compilation download failed.');
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
  const totalMaterialCost = materials.reduce((sum, m) => sum + parseFloat(m.total_cost), 0);

  // Chart values
  const categoriesList = [...new Set(materials.map(m => m.category))];
  const pieData = {
    labels: categoriesList,
    datasets: [{
      data: categoriesList.map(cat => materials.filter(m => m.category === cat).reduce((s, m) => s + parseFloat(m.total_cost), 0)),
      backgroundColor: ['#6366f1', '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#ec4899', '#14b8a6'],
      borderWidth: 1,
      borderColor: '#0f172a'
    }]
  };

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
            <h1 className="text-xl font-bold tracking-tight text-white">AI Material Planning Center</h1>
            <p className="text-xs text-slate-400 mt-1">
              Active logistics for project: <span className="text-slate-200 font-semibold">{project?.project_name}</span>
            </p>
          </div>
        </div>

        <div className="flex space-x-3">
          {materials.length > 0 && (
            <button
              onClick={handleDownloadCsv}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-850 text-slate-200 font-semibold text-xs rounded-xl border border-slate-800 flex items-center transition-all"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5" />
              Export CSV Sheet
            </button>
          )}
          {canModify && (
            <button
              onClick={() => setShowEstimatorModal(true)}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl flex items-center shadow-lg transition-all"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5 animate-pulse" />
              {materials.length > 0 ? 'Run AI Recalculator' : 'Run AI Estimator'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-200 text-xs flex items-center">
          <AlertTriangle className="w-5 h-5 mr-3 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* RENDER PLACEHOLDER IF NO ESTIMATES YET */}
      {materials.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl border border-slate-850 text-center space-y-6 shadow-xl">
          <div className="mx-auto w-14 h-14 bg-brand-500/10 border border-brand-500/20 rounded-2xl flex items-center justify-center text-brand-400">
            <Hammer className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h2 className="text-lg font-bold text-white">No active material estimates</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Compile cement, structural steel, wiring, paint, and finishing requirements. Analyze warehouse stock and suppliers list automatically using AI planning nodes.
            </p>
          </div>
          {canModify ? (
            <button
              onClick={() => setShowEstimatorModal(true)}
              className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl shadow-lg transition-all"
            >
              Trigger AI Material Planner Agent
            </button>
          ) : (
            <p className="text-[10px] text-slate-500 italic">Material plans must be estimated by a Project Manager or Admin.</p>
          )}
        </div>
      ) : (
        <>
          {/* Main KPI Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="glass-panel p-4 rounded-xl border border-slate-850">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Estimated Materials</span>
              <span className="text-lg font-extrabold text-white mt-1 flex items-center">
                <Layers className="w-4.5 h-4.5 mr-1.5 text-slate-500" />
                {materials.length} Items
              </span>
            </div>
            <div className="glass-panel p-4 rounded-xl border border-slate-850">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Estimated Cost</span>
              <span className="text-lg font-extrabold text-white mt-1 flex items-center">
                <IndianRupee className="w-4 h-4 mr-0.5 text-slate-500" />
                {totalMaterialCost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="glass-panel p-4 rounded-xl border border-slate-850">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Stock Shortage alerts</span>
              <span className={`text-lg font-extrabold mt-1 flex items-center ${warnings.length > 0 ? 'text-amber-500' : 'text-emerald-400'}`}>
                <AlertTriangle className="w-4.5 h-4.5 mr-1.5" />
                {warnings.length} alerts
              </span>
            </div>
            <div className="glass-panel p-4 rounded-xl border border-slate-850">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Purchase Orders</span>
              <span className="text-lg font-extrabold text-white mt-1 flex items-center">
                <ShoppingBag className="w-4.5 h-4.5 mr-1.5 text-slate-500" />
                {purchaseOrders.length} logged
              </span>
            </div>
          </div>

          {/* Subtabs selectors */}
          <div className="flex border-b border-slate-850 space-x-6 text-xs font-bold uppercase tracking-wider">
            {['overview', 'list', 'inventory', 'suppliers', 'po'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 border-b-2 transition-all ${
                  activeTab === tab ? 'border-brand-500 text-white' : 'border-transparent text-slate-450 hover:text-slate-200'
                }`}
              >
                {tab === 'po' ? 'Purchase Orders' : tab}
              </button>
            ))}
          </div>

          {/* TAB 1: OVERVIEW & AI RECOMMENDATIONS */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Category pie chart */}
              <div className="glass-panel p-5 rounded-2xl border border-slate-850 flex flex-col items-center">
                <h3 className="text-xs font-semibold text-slate-350 mb-4 text-center">Cost Category Breakdown</h3>
                <div className="w-52 h-52">
                  <Pie data={pieData} options={{ plugins: { legend: { display: false } } }} />
                </div>
              </div>

              {/* Shortage alert list */}
              <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-850 space-y-4">
                <div className="flex items-center space-x-2 text-amber-500">
                  <AlertTriangle className="w-5 h-5 animate-pulse" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Real-Time Logistics Alerts</h3>
                </div>
                <div className="space-y-2">
                  {warnings.length === 0 ? (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs rounded-xl flex items-center">
                      <CheckCircle2 className="w-4 h-4 mr-2" />
                      All materials stock levels healthy. No shortages flagged.
                    </div>
                  ) : (
                    warnings.map((warn, i) => (
                      <div key={i} className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs rounded-xl">
                        {warn}
                      </div>
                    ))
                  )}
                </div>

                {/* AI Optimization Summary */}
                {optimizationSummary && (
                  <div className="border-t border-slate-800/80 pt-4 space-y-2">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center">
                      <Sparkles className="w-4 h-4 mr-1 text-indigo-400 animate-pulse" />
                      AI Procurement Optimization Strategy
                    </h4>
                    <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed pl-3 border-l-2 border-brand-500">
                      {optimizationSummary}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: ESTIMATED MATERIALS LIST */}
          {activeTab === 'list' && (
            <div className="glass-panel rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
              <table className="min-w-full divide-y divide-slate-850">
                <thead className="bg-slate-900/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Material</th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Category</th>
                    <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Quantity</th>
                    <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Unit Price</th>
                    <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Total Cost</th>
                    {canModify && <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850/60 bg-transparent text-xs text-slate-300">
                  {materials.map((mat) => (
                    <tr key={mat.id} className="hover:bg-slate-900/20 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-200">
                        {mat.material_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          {mat.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {editingId === mat.id ? (
                          <input
                            type="number"
                            value={editQty}
                            onChange={(e) => setEditQty(e.target.value)}
                            className="w-20 px-2 py-1 bg-slate-900 border border-slate-800 rounded text-right text-white"
                          />
                        ) : (
                          `${parseFloat(mat.quantity).toLocaleString()} ${mat.unit}`
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-mono">
                        {editingId === mat.id ? (
                          <input
                            type="number"
                            value={editPrice}
                            onChange={(e) => setEditPrice(e.target.value)}
                            className="w-20 px-2 py-1 bg-slate-900 border border-slate-800 rounded text-right text-white"
                          />
                        ) : (
                          `₹${parseFloat(mat.unit_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-semibold text-white">
                        ₹{parseFloat(mat.total_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      {canModify && (
                        <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                          {editingId === mat.id ? (
                            <>
                              <button
                                onClick={() => handleEditSave(mat.id)}
                                className="p-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 rounded"
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="p-1 bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 rounded"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => {
                                  setEditingId(mat.id);
                                  setEditQty(mat.quantity.toString());
                                  setEditPrice(mat.unit_price.toString());
                                }}
                                className="p-1.5 bg-slate-850 hover:bg-slate-800 text-slate-450 hover:text-white rounded border border-transparent"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleDeleteLine(mat.id)}
                                className="p-1.5 bg-slate-850 hover:bg-rose-500/10 text-slate-450 hover:text-rose-400 rounded border border-transparent"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 3: WAREHOUSE STOCKS */}
          {activeTab === 'inventory' && (
            <div className="space-y-6">
              {canModify && (
                <div className="glass-panel p-6 rounded-2xl border border-slate-850">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">Stock Ledger Update</h3>
                  <form onSubmit={handleInventoryUpdate} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Material Type</label>
                      <select
                        required
                        value={invForm.material_name}
                        onChange={(e) => setInvForm(prev => ({ ...prev, material_name: e.target.value }))}
                        className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                      >
                        <option value="">Select Material...</option>
                        {materials.map(m => (
                          <option key={m.id} value={m.material_name}>{m.material_name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Quantity Change (+ / -)</label>
                      <input
                        type="number"
                        step="any"
                        required
                        placeholder="e.g. 100 or -50"
                        value={invForm.quantity_change}
                        onChange={(e) => setInvForm(prev => ({ ...prev, quantity_change: e.target.value }))}
                        className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                      />
                    </div>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl shadow-md h-9"
                    >
                      Update Warehouse stock
                    </button>
                  </form>
                </div>
              )}

              <div className="glass-panel rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
                <table className="min-w-full divide-y divide-slate-850">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Material Stock</th>
                      <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Available Stock</th>
                      <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Reserved Stock</th>
                      <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Total Warehouse capacity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850/60 bg-transparent text-xs text-slate-300">
                    {inventory.map((inv) => (
                      <tr key={inv.id} className="hover:bg-slate-900/20 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-200">{inv.material_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-emerald-455 font-semibold">
                          {parseFloat(inv.quantity_available).toLocaleString()} {inv.unit}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-amber-500 font-semibold">
                          {parseFloat(inv.quantity_reserved).toLocaleString()} {inv.unit}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-slate-400">
                          {parseFloat(inv.warehouse_capacity).toLocaleString()} {inv.unit}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: SUPPLIERS ROSTER */}
          {activeTab === 'suppliers' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {suppliers.map((sup) => (
                <div key={sup.id} className="glass-panel p-5 rounded-xl border border-slate-850 space-y-3 relative shadow-md">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-sm font-bold text-white">{sup.supplier_name}</h4>
                      <span className="text-[10px] text-slate-400 font-semibold">{sup.contact_info}</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center">
                      ★ {parseFloat(sup.rating).toFixed(1)}
                    </span>
                  </div>
                  {sup.address && (
                    <p className="text-[10px] text-slate-400 italic">
                      Address: {sup.address}
                    </p>
                  )}
                  <div className="text-[10px] flex items-center">
                    <span className={`inline-block w-2 h-2 rounded-full mr-1.5 ${sup.active ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                    <span className="text-slate-300">{sup.active ? 'Contract Active' : 'Suspended'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 5: PURCHASE ORDERS */}
          {activeTab === 'po' && (
            <div className="space-y-6">
              {/* Purchase Order Creator Form */}
              {canModify && (
                <div className="glass-panel p-6 rounded-2xl border border-slate-850">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">File Procurement Purchase Order</h3>
                  {poError && (
                    <div className="p-3 mb-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-250 text-xs">
                      {poError}
                    </div>
                  )}
                  <form onSubmit={handleCreatePO} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Material Type</label>
                      <select
                        required
                        value={poForm.material_name}
                        onChange={(e) => {
                          const name = e.target.value;
                          const mat_spec = materials.find(m => m.material_name === name);
                          setPoForm(prev => ({
                            ...prev,
                            material_name: name,
                            unit_price: mat_spec ? mat_spec.unit_price.toString() : ''
                          }));
                        }}
                        className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                      >
                        <option value="">Select Material...</option>
                        {materials.map(m => (
                          <option key={m.id} value={m.material_name}>{m.material_name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Matched Supplier</label>
                      <select
                        required
                        value={poForm.supplier_id}
                        onChange={(e) => setPoForm(prev => ({ ...prev, supplier_id: e.target.value }))}
                        className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                      >
                        <option value="">Select Supplier...</option>
                        {suppliers.filter(s => s.active).map(s => (
                          <option key={s.id} value={s.id}>{s.supplier_name} (★{parseFloat(s.rating).toFixed(1)})</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Order Quantity</label>
                      <input
                        type="number"
                        required
                        placeholder="Quantity"
                        value={poForm.quantity}
                        onChange={(e) => setPoForm(prev => ({ ...prev, quantity: e.target.value }))}
                        className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                      />
                    </div>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl shadow-md h-9 flex items-center justify-center"
                    >
                      <ShoppingBag className="w-3.5 h-3.5 mr-1" /> Commit Purchase
                    </button>
                  </form>
                </div>
              )}

              {/* Purchase Orders Table */}
              <div className="glass-panel rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
                <table className="min-w-full divide-y divide-slate-850">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Order ID</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Material</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-450 uppercase tracking-wider">Supplier</th>
                      <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Quantity</th>
                      <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Total Price</th>
                      <th className="px-6 py-4 text-right text-xs font-bold text-slate-450 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850/60 bg-transparent text-xs text-slate-300">
                    {purchaseOrders.map((po) => (
                      <tr key={po.id} className="hover:bg-slate-900/20 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-slate-450 font-mono">PO-{po.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-200">{po.material_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-slate-400">{po.supplier?.supplier_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">{parseFloat(po.quantity).toLocaleString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right font-semibold text-white">
                          ₹{parseFloat(po.total_cost).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold border ${
                            po.status === 'Delivered' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                            'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                          }`}>
                            {po.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* AI MATERIAL ESTIMATION RUN MODAL */}
      {showEstimatorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel max-w-md w-full p-6 rounded-2xl border border-slate-800 space-y-4 relative shadow-2xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Material Requirements Estimator</h3>
            <form onSubmit={handleRunEstimator} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Build Area (Sq.Ft)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={estimatorForm.area_sqft}
                    onChange={(e) => setEstimatorForm(prev => ({ ...prev, area_sqft: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Floor Count</label>
                  <input
                    type="number"
                    required
                    value={estimatorForm.floors}
                    onChange={(e) => setEstimatorForm(prev => ({ ...prev, floors: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Building Type</label>
                  <select
                    value={estimatorForm.building_type}
                    onChange={(e) => setEstimatorForm(prev => ({ ...prev, building_type: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  >
                    <option value="Residential">Residential</option>
                    <option value="Commercial">Commercial</option>
                    <option value="Industrial">Industrial</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Room Counts</label>
                  <input
                    type="number"
                    required
                    value={estimatorForm.rooms}
                    onChange={(e) => setEstimatorForm(prev => ({ ...prev, rooms: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Timeline (Months)</label>
                  <input
                    type="number"
                    required
                    value={estimatorForm.timeline_months}
                    onChange={(e) => setEstimatorForm(prev => ({ ...prev, timeline_months: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-450 uppercase tracking-wider mb-2">Estimated Budget (₹)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={estimatorForm.budget}
                    onChange={(e) => setEstimatorForm(prev => ({ ...prev, budget: e.target.value }))}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEstimatorModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl disabled:opacity-50 flex items-center"
                >
                  {actionLoading ? <Loader className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : null}
                  Calculate Estimates
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaterialsDashboard;
