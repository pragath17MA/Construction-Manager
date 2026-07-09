import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getProjects, deleteProject } from '../services/projects';
import { useAuth } from '../context/AuthContext';
import { Search, Plus, Edit2, Trash2, Eye, MapPin, Calendar, IndianRupee } from 'lucide-react';

const ProjectsList = () => {
  const [projects, setProjects] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(10);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const response = await getProjects({
        page,
        size,
        search: search || undefined,
        status_filter: statusFilter || undefined,
      });
      setProjects(response.items || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Failed to fetch projects', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProjects();
  };

  const handleDelete = async (id, name) => {
    if (window.confirm(`Are you sure you want to delete the project "${name}"? This action is irreversible.`)) {
      try {
        await deleteProject(id);
        fetchProjects();
      } catch (err) {
        console.error(err);
        alert(err.response?.data?.detail || 'Failed to delete project.');
      }
    }
  };

  const totalPages = Math.ceil(total / size);

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Projects Workspace</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Overview and controls of all active construction contracts
          </p>
        </div>
        {(user?.role === 'Admin' || user?.role === 'Project Manager') && (
          <Link
            to="/projects/create"
            className="inline-flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-500 rounded-xl transition-all duration-200"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Project
          </Link>
        )}
      </div>

      {/* Filters Search Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Search className="w-5 h-5" />
            </span>
            <input
              type="text"
              placeholder="Search by name, client, or location..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="block w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all duration-200"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2.5 bg-slate-800 text-slate-200 border border-slate-700 rounded-xl hover:bg-slate-700 font-semibold text-sm transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => {
              setPage(1);
              setStatusFilter(e.target.value);
            }}
            className="px-3 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Statuses</option>
            <option value="Planning">Planning</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
            <option value="Delayed">Delayed</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Projects Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-brand-500"></div>
          </div>
        ) : projects.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            No projects found matching the criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-800">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Project</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Client</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Budget</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Expected End</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-transparent">
                {projects.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-900/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-100">{p.project_name}</div>
                      <div className="text-xs text-slate-400 flex items-center mt-1">
                        <MapPin className="w-3.5 h-3.5 mr-1 text-slate-500" />
                        {p.location}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                      {p.client_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-200">
                      ₹{parseFloat(p.budget).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1.5 text-slate-500" />
                        {new Date(p.expected_end_date).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2.5 py-1 text-xs font-bold rounded-xl border ${
                        p.status === 'Completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                        p.status === 'In Progress' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                        p.status === 'Delayed' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                        p.status === 'Cancelled' ? 'bg-slate-500/10 text-slate-400 border-slate-500/20' :
                        'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end space-x-2">
                        <Link
                          to={`/projects/${p.id}`}
                          className="p-1.5 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 hover:text-white transition-all"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        {/* Only Admin or PM can edit projects */}
                        {(user?.role === 'Admin' || user?.role === 'Project Manager') && (
                          <Link
                            to={`/projects/${p.id}/edit`}
                            className="p-1.5 bg-slate-800 text-slate-300 rounded-lg hover:bg-brand-600 hover:text-white transition-all"
                            title="Edit Project"
                          >
                            <Edit2 className="w-4 h-4" />
                          </Link>
                        )}
                        {/* Only Admin can delete projects */}
                        {user?.role === 'Admin' && (
                          <button
                            onClick={() => handleDelete(p.id, p.project_name)}
                            className="p-1.5 bg-slate-800 text-slate-300 rounded-lg hover:bg-rose-600 hover:text-white transition-all"
                            title="Delete Project"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="px-6 py-4 bg-slate-900/30 border-t border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">
              Showing page <strong className="text-slate-200">{page}</strong> of <strong className="text-slate-200">{totalPages}</strong> ({total} projects total)
            </span>
            <div className="flex space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded-lg font-semibold transition-colors"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded-lg font-semibold transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectsList;
