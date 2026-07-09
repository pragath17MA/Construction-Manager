import api from './api';

export const submitDailyProgress = async (formData) => {
  const response = await api.post('/progress/update', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

export const getProgressSummary = async (projectId) => {
  const response = await api.get(`/progress/project/${projectId}`);
  return response.data;
};

export const createOrUpdateMilestone = async (data) => {
  const response = await api.post('/milestone', data);
  return response.data;
};

export const getProjectMilestones = async (projectId) => {
  const response = await api.get(`/milestones/${projectId}`);
  return response.data;
};

export const downloadProgressReport = async (projectId, format = 'pdf', fileName = 'progress_report') => {
  const response = await api.get(`/reports/progress/${projectId}?format=${format}`, {
    responseType: 'blob'
  });
  
  const mimeType = format === 'excel' ? 'text/csv' : 'application/pdf';
  const extension = format === 'excel' ? 'csv' : 'pdf';
  
  const url = window.URL.createObjectURL(new Blob([response.data], { type: mimeType }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${fileName}.${extension}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
