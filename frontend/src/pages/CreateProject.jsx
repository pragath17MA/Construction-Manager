import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createProject } from '../services/projects';
import { AlertCircle, ArrowLeft, Loader } from 'lucide-react';

const CreateProject = () => {
  const [formData, setFormData] = useState({
    project_name: '',
    description: '',
    client_name: '',
    location: '',
    start_date: '',
    expected_end_date: '',
    status: 'Planning',
    budget: '',
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Form validation checks
    const start = new Date(formData.start_date);
    const end = new Date(formData.expected_end_date);
    if (end <= start) {
      setError('Expected End Date must be strictly after the Start Date.');
      return;
    }

    const budgetVal = parseFloat(formData.budget);
    if (isNaN(budgetVal) || budgetVal <= 0) {
      setError('Budget must be a positive numeric value.');
      return;
    }

    setSubmitting(true);
    try {
      await createProject({
        ...formData,
        budget: budgetVal,
      });
      navigate('/projects');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to create project. Please verify inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center space-x-3">
        <Link
          to="/projects"
          className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 transition-colors text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Create New Contract</h1>
          <p className="text-xs text-slate-400 mt-0.5">Initialize a new project build scope</p>
        </div>
      </div>

      <div className="glass-panel p-8 rounded-3xl border border-slate-800 shadow-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-start space-x-3 text-rose-200">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span className="text-sm font-medium">{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Project Name
              </label>
              <input
                type="text"
                name="project_name"
                required
                value={formData.project_name}
                onChange={handleChange}
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                placeholder="e.g. Metro Line Extension Phase 2"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Description
              </label>
              <textarea
                name="description"
                rows={3}
                value={formData.description}
                onChange={handleChange}
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                placeholder="Scope of work, key deliverables, and client directives..."
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Client Name
              </label>
              <input
                type="text"
                name="client_name"
                required
                value={formData.client_name}
                onChange={handleChange}
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                placeholder="e.g. Municipal Transit Authority"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Location
              </label>
              <input
                type="text"
                name="location"
                required
                value={formData.location}
                onChange={handleChange}
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                placeholder="e.g. Sector 62, Noida"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Start Date
              </label>
              <input
                type="date"
                name="start_date"
                required
                value={formData.start_date}
                onChange={handleChange}
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Expected End Date
              </label>
              <input
                type="date"
                name="expected_end_date"
                required
                value={formData.expected_end_date}
                onChange={handleChange}
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Project Status
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
              >
                <option value="Planning" className="bg-slate-950">Planning</option>
                <option value="In Progress" className="bg-slate-950">In Progress</option>
                <option value="Completed" className="bg-slate-950">Completed</option>
                <option value="Delayed" className="bg-slate-950">Delayed</option>
                <option value="Cancelled" className="bg-slate-950">Cancelled</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Budget (INR)
              </label>
              <input
                type="number"
                name="budget"
                required
                value={formData.budget}
                onChange={handleChange}
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                placeholder="e.g. 5000000"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800/80">
            <Link
              to="/projects"
              className="px-5 py-3 bg-slate-900 border border-slate-800 text-slate-300 font-semibold text-sm rounded-xl hover:bg-slate-800 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-3 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm rounded-xl disabled:opacity-50 transition-colors flex items-center justify-center min-w-[120px]"
            >
              {submitting ? <Loader className="w-5 h-5 animate-spin" /> : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProject;
