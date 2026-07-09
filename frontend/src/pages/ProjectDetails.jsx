import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProject, updateProject, addProjectMember, removeProjectMember, getAllUsers, uploadDocument, uploadDrawing, uploadSiteImage, deleteProjectFile } from '../services/projects';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  ArrowLeft, HardHat, Shield, Calendar, MapPin, IndianRupee, Users, 
  FileText, Image as ImageIcon, Plus, Trash2, Download, CheckCircle, 
  Loader, UploadCloud, AlertCircle, ArrowUpRight
} from 'lucide-react';

const ProjectDetails = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Forms & Interactions State
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [newMember, setNewMember] = useState({ user_id: '', role: 'Site Engineer' });
  const [memberSubmitting, setMemberSubmitting] = useState(false);
  const [memberError, setMemberError] = useState('');
  
  // File upload state
  const [uploadState, setUploadState] = useState({
    category: 'document', // document, drawing, image
    drawingName: '',
    captureDate: new Date().toISOString().split('T')[0],
    file: null,
    error: '',
    submitting: false
  });

  const loadProject = async () => {
    try {
      const data = await getProject(id);
      setProject(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadUsersList = async () => {
    if (user?.role === 'Admin' || user?.role === 'Project Manager') {
      try {
        const users = await getAllUsers();
        setAllUsers(users);
      } catch (err) {
        console.error(err);
      }
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([loadProject(), loadUsersList()]);
      setLoading(false);
    };
    init();
  }, [id]);

  const handleStatusChange = async (newStatus) => {
    setStatusUpdating(true);
    try {
      await updateProject(id, { status: newStatus });
      await loadProject();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to update project status.');
    } finally {
      setStatusUpdating(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    setMemberError('');
    if (!newMember.user_id) {
      setMemberError('Please select a system user.');
      return;
    }
    setMemberSubmitting(true);
    try {
      await addProjectMember(id, parseInt(newMember.user_id), newMember.role);
      setNewMember({ user_id: '', role: 'Site Engineer' });
      await loadProject();
    } catch (err) {
      console.error(err);
      setMemberError(err.response?.data?.detail || 'Failed to add member.');
    } finally {
      setMemberSubmitting(false);
    }
  };

  const handleRemoveMember = async (userId) => {
    if (window.confirm('Remove this member from the project?')) {
      try {
        await removeProjectMember(id, userId);
        await loadProject();
      } catch (err) {
        console.error(err);
        alert(err.response?.data?.detail || 'Failed to remove member.');
      }
    }
  };

  // Secure File Download (Blob + JWT Authorization header)
  const handleDownloadDocument = async (docId, fileName, contentType) => {
    try {
      const response = await api.get(`/projects/${id}/documents/${docId}/download`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: contentType }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('Failed to download document safely.');
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setUploadState(prev => ({
      ...prev,
      file: selectedFile,
      error: ''
    }));
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    setUploadState(prev => ({ ...prev, error: '', submitting: true }));

    const { category, file, drawingName, captureDate } = uploadState;
    if (!file) {
      setUploadState(prev => ({ ...prev, error: 'Please select a file to upload.', submitting: false }));
      return;
    }

    // Size limit check
    const sizeLimit = category === 'image' ? 5 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > sizeLimit) {
      const sizeMB = sizeLimit / (1024 * 1024);
      setUploadState(prev => ({
        ...prev,
        error: `File size exceeds the limit of ${sizeMB}MB.`,
        submitting: false
      }));
      return;
    }

    try {
      if (category === 'drawing') {
        if (!drawingName.trim()) {
          setUploadState(prev => ({ ...prev, error: 'Drawing name is required.', submitting: false }));
          return;
        }
        await uploadDrawing(id, drawingName, file);
      } else if (category === 'image') {
        await uploadSiteImage(id, captureDate, file);
      } else {
        await uploadDocument(id, file);
      }

      // Reset Form state
      setUploadState({
        category,
        drawingName: '',
        captureDate: new Date().toISOString().split('T')[0],
        file: null,
        error: '',
        submitting: false
      });
      
      // Reload details
      await loadProject();
    } catch (err) {
      console.error(err);
      setUploadState(prev => ({
        ...prev,
        error: err.response?.data?.detail || 'File upload failed.',
        submitting: false
      }));
    }
  };

  const handleDeleteFile = async (fileId, category) => {
    if (window.confirm('Delete this file permanently?')) {
      try {
        await deleteProjectFile(id, fileId, category);
        await loadProject();
      } catch (err) {
        console.error(err);
        alert(err.response?.data?.detail || 'Failed to delete file.');
      }
    }
  };

  // Calculated Progress bar values
  const calculateProgress = () => {
    if (!project) return 0;
    const start = new Date(project.start_date);
    const end = new Date(project.expected_end_date);
    const now = new Date();
    
    if (project.status === 'Completed') return 100;
    if (now < start) return 0;
    if (now > end) return 95; // cap at 95% if delayed

    const totalDuration = end - start;
    const elapsed = now - start;
    return Math.min(Math.round((elapsed / totalDuration) * 100), 95);
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <Loader className="w-10 h-10 animate-spin text-brand-500" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center p-8 bg-slate-900 border border-slate-800 rounded-2xl text-slate-400">
        Project details could not be loaded. Verify target permissions.
      </div>
    );
  }

  // Check role eligibility
  const canModifyProject = user?.role === 'Admin' || user?.role === 'Project Manager';

  return (
    <div className="space-y-6">
      {/* Header breadcrumb */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div className="flex items-center space-x-3">
          <Link
            to="/projects"
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">{project.project_name}</h1>
            <p className="text-xs text-slate-400 mt-1 flex items-center">
              <MapPin className="w-3.5 h-3.5 mr-1" />
              {project.location} • Client: {project.client_name}
            </p>
          </div>
        </div>

        {/* Dynamic Status Dropdown Selector */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Status:</span>
            {statusUpdating ? (
              <Loader className="w-4 h-4 animate-spin text-brand-400" />
            ) : (
              <select
                value={project.status}
                onChange={(e) => handleStatusChange(e.target.value)}
                className="px-3 py-1.5 bg-slate-900 border border-slate-850 rounded-xl text-xs font-semibold text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="Planning">Planning</option>
                <option value="In Progress">In Progress</option>
                <option value="Completed">Completed</option>
                <option value="Delayed">Delayed</option>
                <option value="Cancelled">Cancelled</option>
              </select>
            )}
          </div>
          <Link
            to={`/projects/${project.id}/budget`}
            className="px-4 py-2 text-xs font-semibold text-white bg-brand-650 hover:bg-brand-600 border border-brand-700/30 rounded-xl transition-all"
          >
            AI Cost Cockpit
          </Link>
          <Link
            to={`/projects/${project.id}/materials`}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl transition-all"
          >
            AI Materials Cockpit
          </Link>
          <Link
            to={`/projects/${project.id}/workers`}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl transition-all"
          >
            AI Workforce Cockpit
          </Link>
          <Link
            to={`/projects/${project.id}/risk`}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl transition-all"
          >
            AI Risk Cockpit
          </Link>
          <Link
            to={`/projects/${project.id}/progress`}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl transition-all"
          >
            AI Progress Cockpit
          </Link>
          <Link
            to={`/projects/${project.id}/documents`}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl transition-all"
          >
            AI Drawing Cockpit
          </Link>
          <Link
            to={`/projects/${project.id}/invoices`}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl transition-all"
          >
            AI Invoice Cockpit
          </Link>
          <Link
            to={`/projects/${project.id}/image-analysis`}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl transition-all"
          >
            AI Image Cockpit
          </Link>
          <Link
            to={`/projects/${project.id}/voice`}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl transition-all"
          >
            AI Voice Cockpit
          </Link>
          {canModifyProject && (
            <Link
              to={`/projects/${project.id}/edit`}
              className="px-4 py-2 text-xs font-semibold text-white bg-slate-850 hover:bg-slate-800 border border-slate-805 rounded-xl transition-all"
            >
              Modify Scope
            </Link>
          )}
        </div>
      </div>

      {/* Progress Timeline Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 shadow-lg">
        <div className="flex justify-between items-center text-sm font-medium">
          <span className="text-slate-400">Project Progress Timeline</span>
          <span className="text-brand-400">{calculateProgress()}% complete</span>
        </div>
        <div className="w-full bg-slate-950 rounded-full h-3.5 border border-slate-900 overflow-hidden">
          <div
            className="bg-gradient-to-r from-brand-600 to-indigo-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${calculateProgress()}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-slate-400">
          <div>
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-500">Start Date</span>
            <span className="text-slate-300 font-medium">{new Date(project.start_date).toLocaleDateString()}</span>
          </div>
          <div className="text-right">
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-500">Target Delivery</span>
            <span className="text-slate-300 font-medium">{new Date(project.expected_end_date).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      {/* Grid: Details tabs & Sidebar Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Main Details and Tabbed panels (Col-3) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Tab Navigation header */}
          <div className="flex border-b border-slate-800/80 space-x-6 text-sm font-semibold">
            {['overview', 'members', 'drawings', 'documents', 'images'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 capitalize border-b-2 transition-all ${
                  activeTab === tab
                    ? 'border-brand-500 text-white'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab === 'images' ? 'Site Images' : tab}
              </button>
            ))}
          </div>

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Project Description</h3>
                <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                  {project.description || 'No descriptive overview defined for this build contract.'}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-6 border-t border-slate-800/60 pt-6">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Location Area</h4>
                  <p className="text-sm text-slate-200 font-medium mt-1">{project.location}</p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Budget</h4>
                  <p className="text-sm text-brand-400 font-bold mt-1">
                    ₹{parseFloat(project.budget).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: MEMBERS */}
          {activeTab === 'members' && (
            <div className="space-y-6">
              {/* Member assigning form (Only Admin or PM) */}
              {canModifyProject && (
                <div className="glass-panel p-6 rounded-2xl border border-slate-800">
                  <h3 className="text-sm font-semibold text-white mb-4">Assign Project Member</h3>
                  {memberError && (
                    <div className="p-3 mb-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-200 text-xs flex items-center">
                      <AlertCircle className="w-4 h-4 mr-2" />
                      {memberError}
                    </div>
                  )}
                  <form onSubmit={handleAddMember} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <select
                      value={newMember.user_id}
                      onChange={(e) => setNewMember(prev => ({ ...prev, user_id: e.target.value }))}
                      className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="">Select User...</option>
                      {allUsers
                        .filter(u => !project.members.some(m => m.user_id === u.id))
                        .map(u => (
                          <option key={u.id} value={u.id}>
                            {u.full_name} ({u.role})
                          </option>
                        ))}
                    </select>

                    <select
                      value={newMember.role}
                      onChange={(e) => setNewMember(prev => ({ ...prev, role: e.target.value }))}
                      className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="Admin">Admin</option>
                      <option value="Project Manager">Project Manager</option>
                      <option value="Site Engineer">Site Engineer</option>
                    </select>

                    <button
                      type="submit"
                      disabled={memberSubmitting}
                      className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl disabled:opacity-50 flex items-center justify-center"
                    >
                      {memberSubmitting ? <Loader className="w-4 h-4 animate-spin" /> : 'Assign Member'}
                    </button>
                  </form>
                </div>
              )}

              {/* Members Table */}
              <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
                <table className="min-w-full divide-y divide-slate-800">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Member Name</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">System Role</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Project Assignment</th>
                      {canModifyProject && <th className="px-6 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider">Action</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-transparent text-sm">
                    {project.members.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-900/20 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-semibold text-slate-100">{m.user?.full_name || 'Assigned User'}</div>
                          <div className="text-xs text-slate-400">{m.user?.email || 'N/A'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-slate-300">
                          {m.user?.role}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-brand-400 font-semibold">
                          {m.role}
                        </td>
                        {canModifyProject && (
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <button
                              onClick={() => handleRemoveMember(m.user_id)}
                              className="p-1.5 bg-slate-850 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-lg border border-transparent hover:border-rose-500/20 transition-all"
                              title="Revoke Assignment"
                            >
                              <Trash2 className="w-4 h-4" />
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

          {/* TAB 3: DRAWINGS */}
          {activeTab === 'drawings' && (
            <div className="space-y-6">
              {/* Drawing Upload Form (Only Admin or PM) */}
              {canModifyProject && (
                <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
                  <h3 className="text-sm font-semibold text-white">Upload Construction Blueprint (PDF Only)</h3>
                  {uploadState.category === 'drawing' && uploadState.error && (
                    <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-200 text-xs flex items-center">
                      <AlertCircle className="w-4 h-4 mr-2" />
                      {uploadState.error}
                    </div>
                  )}
                  <form onSubmit={handleFileUpload} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Drawing Title</label>
                        <input
                          type="text"
                          required
                          value={uploadState.drawingName}
                          onChange={(e) => setUploadState(prev => ({ ...prev, category: 'drawing', drawingName: e.target.value }))}
                          className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                          placeholder="e.g. Electrical Layout 3rd Floor"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Select PDF File</label>
                        <input
                          type="file"
                          accept=".pdf"
                          required
                          onChange={handleFileChange}
                          onClick={() => setUploadState(prev => ({ ...prev, category: 'drawing' }))}
                          className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-850 file:text-slate-200 hover:file:bg-slate-800 file:cursor-pointer"
                        />
                      </div>
                    </div>
                    <button
                      type="submit"
                      disabled={uploadState.submitting}
                      className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl disabled:opacity-50 flex items-center justify-center"
                    >
                      {uploadState.submitting ? <Loader className="w-4 h-4 animate-spin" /> : 'Upload Drawing'}
                    </button>
                  </form>
                </div>
              )}

              {/* Drawings List */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {project.drawings.length === 0 ? (
                  <div className="sm:col-span-2 text-center p-8 bg-slate-900/40 border border-slate-800 rounded-xl text-slate-500 text-sm">
                    No construction blueprints uploaded.
                  </div>
                ) : (
                  project.drawings.map((draw) => (
                    <div key={draw.id} className="glass-panel p-4 rounded-xl border border-slate-850 flex items-center justify-between">
                      <div className="space-y-1">
                        <span className="text-sm font-semibold text-white block">{draw.drawing_name}</span>
                        <span className="text-[10px] text-slate-400">Uploaded {new Date(draw.uploaded_at).toLocaleDateString()}</span>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleDownloadDocument(draw.id, `${draw.drawing_name}.pdf`, 'application/pdf')}
                          className="p-2 bg-slate-850 hover:bg-slate-800 text-slate-300 rounded-lg"
                          title="Download PDF"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        {canModifyProject && (
                          <button
                            onClick={() => handleDeleteFile(draw.id, 'drawing')}
                            className="p-2 bg-slate-850 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-lg border border-transparent hover:border-rose-500/20"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 4: DOCUMENTS */}
          {activeTab === 'documents' && (
            <div className="space-y-6">
              {/* Document Upload Form (Only Admin or PM) */}
              {canModifyProject && (
                <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
                  <h3 className="text-sm font-semibold text-white">Upload Project Document</h3>
                  {uploadState.category === 'document' && uploadState.error && (
                    <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-200 text-xs flex items-center">
                      <AlertCircle className="w-4 h-4 mr-2" />
                      {uploadState.error}
                    </div>
                  )}
                  <form onSubmit={handleFileUpload} className="flex flex-col sm:flex-row items-end gap-4">
                    <div className="flex-1">
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Select File (PDF, Word, Excel, TXT)</label>
                      <input
                        type="file"
                        required
                        onChange={handleFileChange}
                        onClick={() => setUploadState(prev => ({ ...prev, category: 'document' }))}
                        className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-850 file:text-slate-200 hover:file:bg-slate-800 file:cursor-pointer"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={uploadState.submitting}
                      className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl disabled:opacity-50 flex items-center justify-center h-9"
                    >
                      {uploadState.submitting ? <Loader className="w-4 h-4 animate-spin" /> : 'Upload File'}
                    </button>
                  </form>
                </div>
              )}

              {/* Documents List */}
              <div className="space-y-3">
                {project.documents.length === 0 ? (
                  <div className="text-center p-8 bg-slate-900/40 border border-slate-800 rounded-xl text-slate-500 text-sm">
                    No documents uploaded to this workspace.
                  </div>
                ) : (
                  project.documents.map((doc) => (
                    <div key={doc.id} className="glass-panel p-4 rounded-xl border border-slate-850 flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-slate-850 text-slate-400 rounded-lg">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div>
                          <span className="text-sm font-semibold text-white block">{doc.file_name}</span>
                          <span className="text-[10px] text-slate-400">Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleDownloadDocument(doc.id, doc.file_name, doc.file_type)}
                          className="p-2 bg-slate-850 hover:bg-slate-800 text-slate-300 rounded-lg"
                          title="Download Document"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        {canModifyProject && (
                          <button
                            onClick={() => handleDeleteFile(doc.id, 'document')}
                            className="p-2 bg-slate-850 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-lg border border-transparent hover:border-rose-500/20"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 5: SITE IMAGES */}
          {activeTab === 'images' && (
            <div className="space-y-6">
              {/* Site Image Upload Form (Admin, PM, and Site Engineers) */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
                <h3 className="text-sm font-semibold text-white">Upload Daily Site Construction Progress Image</h3>
                {uploadState.category === 'image' && uploadState.error && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-200 text-xs flex items-center">
                    <AlertCircle className="w-4 h-4 mr-2" />
                    {uploadState.error}
                  </div>
                )}
                <form onSubmit={handleFileUpload} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Capture Date</label>
                    <input
                      type="date"
                      required
                      value={uploadState.captureDate}
                      onChange={(e) => setUploadState(prev => ({ ...prev, category: 'image', captureDate: e.target.value }))}
                      className="block w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Select Image File</label>
                    <input
                      type="file"
                      accept="image/*"
                      required
                      onChange={handleFileChange}
                      onClick={() => setUploadState(prev => ({ ...prev, category: 'image' }))}
                      className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-850 file:text-slate-200 hover:file:bg-slate-800 file:cursor-pointer"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={uploadState.submitting}
                    className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl disabled:opacity-50 flex items-center justify-center h-9"
                  >
                    {uploadState.submitting ? <Loader className="w-4 h-4 animate-spin" /> : 'Upload Progress Image'}
                  </button>
                </form>
              </div>

              {/* Site Images Gallery */}
              {project.images.length === 0 ? (
                <div className="text-center p-8 bg-slate-900/40 border border-slate-800 rounded-xl text-slate-500 text-sm">
                  No site images logged yet.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                  {project.images.map((img) => (
                    <div key={img.id} className="glass-panel rounded-xl border border-slate-850 overflow-hidden group relative shadow-md">
                      {/* Image loading source */}
                      {/* Note: since backend serves uploaded files, we can request them via standard paths or api proxies.
                          For full sandbox support, we fetch using absolute backend assets mapping */}
                      <img
                        src={`${import.meta.env.VITE_API_URL || ''}/${img.image_path}`}
                        alt={`Progress on ${img.capture_date}`}
                        className="w-full h-40 object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          // Fallback mock image placeholder
                          e.target.src = 'https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&w=400&q=80';
                        }}
                      />
                      <div className="p-3 flex justify-between items-center bg-slate-900/80 backdrop-blur-sm border-t border-slate-800">
                        <div>
                          <span className="text-xs font-semibold text-slate-200 block">Captured</span>
                          <span className="text-[10px] text-slate-400">{new Date(img.capture_date).toLocaleDateString()}</span>
                        </div>
                        {canModifyProject && (
                          <button
                            onClick={() => handleDeleteFile(img.id, 'image')}
                            className="p-1.5 bg-slate-800 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-lg border border-transparent hover:border-rose-500/20"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar Stats Panel (Col-1) */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6 shadow-md">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Budget Details</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400 font-medium">Estimated Budget</span>
                <span className="text-sm font-semibold text-slate-200 flex items-center">
                  <IndianRupee className="w-3.5 h-3.5 mr-0.5 text-slate-500" />
                  {parseFloat(project.budget).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between items-center border-t border-slate-850 pt-4">
                <span className="text-xs text-slate-400 font-medium">Site Status</span>
                <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold border ${
                  project.status === 'Completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  project.status === 'In Progress' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                  'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                }`}>
                  {project.status}
                </span>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 shadow-md">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Project Members</h3>
            <div className="flex items-center -space-x-2 overflow-hidden">
              {project.members.slice(0, 5).map((m) => (
                <div
                  key={m.id}
                  className="inline-block h-8 w-8 rounded-full ring-2 ring-slate-900 bg-slate-800 text-slate-300 font-bold text-xs flex items-center justify-center border border-slate-700 uppercase"
                  title={m.user?.full_name}
                >
                  {m.user?.full_name ? m.user.full_name.charAt(0) : '?'}
                </div>
              ))}
              {project.members.length > 5 && (
                <div className="flex items-center justify-center h-8 w-8 rounded-full ring-2 ring-slate-900 bg-slate-900 text-xs font-semibold text-slate-400 border border-slate-850">
                  +{project.members.length - 5}
                </div>
              )}
            </div>
            <button
              onClick={() => setActiveTab('members')}
              className="text-xs font-semibold text-brand-400 hover:text-brand-300 transition-colors flex items-center"
            >
              Manage Team Members <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetails;
