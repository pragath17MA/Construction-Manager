import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { getProject, updateProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { AlertCircle, ArrowLeft, Loader } from 'lucide-react';

const EditProject = () => {
  const { id } = useParams();
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    const loadProject = async () => {
      try {
        const data = await getProject(id);
        setFormData({
          project_name: data.project_name,
          description: data.description || '',
          client_name: data.client_name,
          location: data.location,
          start_date: data.start_date,
          expected_end_date: data.expected_end_date,
          status: data.status,
          budget: data.budget.toString(),
        });
      } catch (err) {
        console.error(err);
        setError('Failed to load project details.');
      } finally {
        setLoading(false);
      }
    };
    loadProject();
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Date range and budget validations
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
      await updateProject(id, {
        ...formData,
        budget: budgetVal,
      });
      navigate(`/projects/${id}`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to update project. Please verify inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-700 border-t-brand-500"></div>
      </div>
    );
  }

  // Site Engineers are blocked on the client interface
  if (user?.role === 'Site Engineer') {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-rose-500/20 max-w-md mx-auto text-center shadow-lg">
        <h2 className="text-xl font-bold text-slate-100">Access Denied</h2>
        <p className="text-slate-400 text-sm mt-2">Site Engineers are not authorized to edit project metadata directly.</p>
        <Link to={`/projects/${id}`} className="inline-block mt-4 text-xs font-semibold text-brand-400 hover:text-brand-300 underline">
          Return to Project Details
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center space-x-3">
        <Link
          to={`/projects/${id}`}
          className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 transition-colors text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Edit Contract Details</h1>
          <p className="text-xs text-slate-400 mt-0.5">Modify parameters for {formData.project_name}</p>
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
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
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
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
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
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
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
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
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
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
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
                className="block w-full px-4 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800/80">
            <Link
              to={`/projects/${id}`}
              className="px-5 py-3 bg-slate-900 border border-slate-800 text-slate-300 font-semibold text-sm rounded-xl hover:bg-slate-800 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-3 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm rounded-xl disabled:opacity-50 transition-colors flex items-center justify-center min-w-[120px]"
            >
              {submitting ? <Loader className="w-5 h-5 animate-spin" /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditProject;
