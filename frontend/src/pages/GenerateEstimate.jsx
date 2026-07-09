import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { estimateBudget } from '../services/budget';
import { getProject } from '../services/projects';
import { ArrowLeft, Plus, Trash2, Calculator, Loader, AlertCircle } from 'lucide-react';

const GenerateEstimate = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [loadingProject, setLoadingProject] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  // Estimation Form Inputs State
  const [areaSqft, setAreaSqft] = useState('');
  const [currency, setCurrency] = useState('INR');
  
  const [materials, setMaterials] = useState([
    { material: 'Portland Cement', quantity: '', unit_price: '' },
    { material: 'Structural Steel', quantity: '', unit_price: '' }
  ]);
  
  const [labor, setLabor] = useState([
    { worker_type: 'Masons', worker_count: '', daily_rate: '', days: '' },
    { worker_type: 'General Helpers', worker_count: '', daily_rate: '', days: '' }
  ]);
  
  const [equipment, setEquipment] = useState([
    { equipment_name: 'Crawler Excavator', daily_rate: '', days_used: '' }
  ]);

  useEffect(() => {
    const fetchProjectDetails = async () => {
      try {
        const data = await getProject(projectId);
        setProject(data);
      } catch (err) {
        console.error(err);
        setError('Failed to load project context details.');
      } finally {
        setLoadingProject(false);
      }
    };
    fetchProjectDetails();
  }, [projectId]);

  // Materials Array Operations
  const handleMaterialChange = (index, field, value) => {
    const updated = [...materials];
    updated[index][field] = value;
    setMaterials(updated);
  };

  const addMaterialRow = () => {
    setMaterials([...materials, { material: '', quantity: '', unit_price: '' }]);
  };

  const removeMaterialRow = (index) => {
    if (materials.length > 1) {
      setMaterials(materials.filter((_, i) => i !== index));
    }
  };

  // Labor Array Operations
  const handleLaborChange = (index, field, value) => {
    const updated = [...labor];
    updated[index][field] = value;
    setLabor(updated);
  };

  const addLaborRow = () => {
    setLabor([...labor, { worker_type: '', worker_count: '', daily_rate: '', days: '' }]);
  };

  const removeLaborRow = (index) => {
    if (labor.length > 1) {
      setLabor(labor.filter((_, i) => i !== index));
    }
  };

  // Equipment Array Operations
  const handleEquipmentChange = (index, field, value) => {
    const updated = [...equipment];
    updated[index][field] = value;
    setEquipment(updated);
  };

  const addEquipmentRow = () => {
    setEquipment([...equipment, { equipment_name: '', daily_rate: '', days_used: '' }]);
  };

  const removeEquipmentRow = (index) => {
    if (equipment.length > 1) {
      setEquipment(equipment.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Pre-validation
    if (!areaSqft || parseFloat(areaSqft) <= 0) {
      setError('Project build area must be greater than zero.');
      return;
    }

    // Parse values
    const data = {
      project_id: parseInt(projectId),
      area_sqft: parseFloat(areaSqft),
      currency,
      materials: materials.map(m => ({
        material: m.material.trim(),
        quantity: parseFloat(m.quantity),
        unit_price: parseFloat(m.unit_price)
      })),
      labor: labor.map(l => ({
        worker_type: l.worker_type.trim(),
        worker_count: parseInt(l.worker_count),
        daily_rate: parseFloat(l.daily_rate),
        days: parseInt(l.days)
      })),
      equipment: equipment.map(eq => ({
        equipment_name: eq.equipment_name.trim(),
        daily_rate: parseFloat(eq.daily_rate),
        days_used: parseInt(eq.days_used)
      }))
    };

    // Client-side validations
    for (let m of data.materials) {
      if (!m.material || isNaN(m.quantity) || m.quantity <= 0 || isNaN(m.unit_price) || m.unit_price <= 0) {
        setError(`Material '${m.material || 'Unnamed'}' must have positive quantity and unit price.`);
        return;
      }
    }
    for (let l of data.labor) {
      if (!l.worker_type || isNaN(l.worker_count) || l.worker_count <= 0 || isNaN(l.daily_rate) || l.daily_rate <= 0 || isNaN(l.days) || l.days <= 0) {
        setError(`Labor '${l.worker_type || 'Unnamed'}' must have positive counts, daily wage rates, and days duration.`);
        return;
      }
    }
    for (let eq of data.equipment) {
      if (!eq.equipment_name || isNaN(eq.daily_rate) || eq.daily_rate <= 0 || isNaN(eq.days_used) || eq.days_used <= 0) {
        setError(`Equipment '${eq.equipment_name || 'Unnamed'}' must have positive rental rate and duration days.`);
        return;
      }
    }

    setSubmitting(true);
    try {
      await estimateBudget(data);
      // Redirect to the project budget dashboard
      navigate(`/projects/${projectId}/budget`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Calculation run failed. Verify server response log.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingProject) {
    return (
      <div className="h-64 flex items-center justify-center">
        <Loader className="w-10 h-10 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header Bar */}
      <div className="flex items-center space-x-3">
        <Link
          to={`/projects/${projectId}`}
          className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">AI Cost Estimation cockpit</h1>
          <p className="text-xs text-slate-400 mt-1">
            Running cost calculations for project: <span className="text-slate-200 font-semibold">{project?.project_name}</span>
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-200 text-xs flex items-center shadow-md">
          <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Base settings */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-6 shadow-lg">
          <div className="md:col-span-3 border-b border-slate-800/60 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">1. Project Specifications</h3>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Build Area (Sq. Ft.)</label>
            <input
              type="number"
              step="any"
              required
              value={areaSqft}
              onChange={(e) => setAreaSqft(e.target.value)}
              className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="e.g. 5200"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">ISO Currency Code</label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="INR">INR (₹)</option>
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
            </select>
          </div>
        </div>

        {/* Step 2: Materials */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 shadow-lg">
          <div className="flex justify-between items-center border-b border-slate-800/60 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">2. Itemized Materials List</h3>
            <button
              type="button"
              onClick={addMaterialRow}
              className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-brand-400 hover:text-brand-300 rounded-xl font-semibold text-xs transition-colors flex items-center"
            >
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Material
            </button>
          </div>
          <div className="space-y-3">
            {materials.map((m, idx) => (
              <div key={idx} className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
                <div className="sm:col-span-5">
                  <input
                    type="text"
                    required
                    placeholder="Material description (e.g. Cement Bags)"
                    value={m.material}
                    onChange={(e) => handleMaterialChange(idx, 'material', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-3">
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="Quantity"
                    value={m.quantity}
                    onChange={(e) => handleMaterialChange(idx, 'quantity', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-3">
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="Unit Price"
                    value={m.unit_price}
                    onChange={(e) => handleMaterialChange(idx, 'unit_price', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-1 text-right">
                  <button
                    type="button"
                    disabled={materials.length <= 1}
                    onClick={() => removeMaterialRow(idx)}
                    className="p-2 bg-slate-900 hover:bg-rose-500/10 text-slate-400 hover:text-rose-450 rounded-xl border border-slate-800 hover:border-rose-500/20 disabled:opacity-30 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step 3: Labor worker count */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 shadow-lg">
          <div className="flex justify-between items-center border-b border-slate-800/60 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">3. Labor & Workers Requirements</h3>
            <button
              type="button"
              onClick={addLaborRow}
              className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-brand-400 hover:text-brand-300 rounded-xl font-semibold text-xs transition-colors flex items-center"
            >
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Workers
            </button>
          </div>
          <div className="space-y-3">
            {labor.map((l, idx) => (
              <div key={idx} className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
                <div className="sm:col-span-4">
                  <input
                    type="text"
                    required
                    placeholder="Worker type (e.g. Mason)"
                    value={l.worker_type}
                    onChange={(e) => handleLaborChange(idx, 'worker_type', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-2">
                  <input
                    type="number"
                    required
                    placeholder="Worker Count"
                    value={l.worker_count}
                    onChange={(e) => handleLaborChange(idx, 'worker_count', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-3">
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="Daily Rate"
                    value={l.daily_rate}
                    onChange={(e) => handleLaborChange(idx, 'daily_rate', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-2">
                  <input
                    type="number"
                    required
                    placeholder="Duration Days"
                    value={l.days}
                    onChange={(e) => handleLaborChange(idx, 'days', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-1 text-right">
                  <button
                    type="button"
                    disabled={labor.length <= 1}
                    onClick={() => removeLaborRow(idx)}
                    className="p-2 bg-slate-900 hover:bg-rose-500/10 text-slate-400 hover:text-rose-450 rounded-xl border border-slate-800 hover:border-rose-500/20 disabled:opacity-30 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step 4: Equipment */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 shadow-lg">
          <div className="flex justify-between items-center border-b border-slate-800/60 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">4. Equipment & Machinery Rentals</h3>
            <button
              type="button"
              onClick={addEquipmentRow}
              className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-brand-400 hover:text-brand-300 rounded-xl font-semibold text-xs transition-colors flex items-center"
            >
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Equipment
            </button>
          </div>
          <div className="space-y-3">
            {equipment.map((eq, idx) => (
              <div key={idx} className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
                <div className="sm:col-span-5">
                  <input
                    type="text"
                    required
                    placeholder="Equipment Name (e.g. Concrete Mixer)"
                    value={eq.equipment_name}
                    onChange={(e) => handleEquipmentChange(idx, 'equipment_name', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-3">
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="Daily Rate"
                    value={eq.daily_rate}
                    onChange={(e) => handleEquipmentChange(idx, 'daily_rate', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-3">
                  <input
                    type="number"
                    required
                    placeholder="Days Used"
                    value={eq.days_used}
                    onChange={(e) => handleEquipmentChange(idx, 'days_used', e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="sm:col-span-1 text-right">
                  <button
                    type="button"
                    disabled={equipment.length <= 1}
                    onClick={() => removeEquipmentRow(idx)}
                    className="p-2 bg-slate-900 hover:bg-rose-500/10 text-slate-400 hover:text-rose-450 rounded-xl border border-slate-800 hover:border-rose-500/20 disabled:opacity-30 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end space-x-4">
          <Link
            to={`/projects/${projectId}`}
            className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs rounded-xl border border-slate-700 transition-all"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl disabled:opacity-50 flex items-center justify-center shadow-lg"
          >
            {submitting ? (
              <>
                <Loader className="w-4 h-4 animate-spin mr-2" />
                Orchestrating LangGraph workflow...
              </>
            ) : (
              <>
                <Calculator className="w-4 h-4 mr-2" />
                Calculate AI Cost Estimate
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default GenerateEstimate;
