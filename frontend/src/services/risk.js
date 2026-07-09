import api from './api';

export const analyzeProjectRisks = async (projectId) => {
  const response = await api.post('/risk/analyze', { project_id: parseInt(projectId) });
  return response.data;
};

export const getProjectRisk = async (projectId) => {
  const response = await api.get(`/risk/project/${projectId}`);
  return response.data;
};

export const getRiskHistory = async (projectId, skip = 0, limit = 10) => {
  const response = await api.get(`/risk/history/${projectId}?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const downloadRiskReport = async (projectId, format = 'pdf', fileName = 'risk_report') => {
  const response = await api.get(`/reports/risk/${projectId}?format=${format}`, {
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
