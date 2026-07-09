import api from './api';

/**
 * Calculates a new project budget estimate.
 * @param {Object} data - Estimate parameters (project_id, area_sqft, materials, labor, equipment)
 */
export const estimateBudget = async (data) => {
  const response = await api.post('/budget/estimate', data);
  return response.data;
};

/**
 * Retrieves the latest active budget detail for a project.
 * @param {number} projectId 
 */
export const getBudgetDetail = async (projectId) => {
  const response = await api.get(`/budget/${projectId}`);
  return response.data;
};

/**
 * Lists paginated history of estimates for a project.
 * @param {number} projectId 
 * @param {number} page 
 * @param {number} size 
 */
export const getBudgetHistory = async (projectId, page = 1, size = 10) => {
  const response = await api.get(`/budget/history/${projectId}?page=${page}&size=${size}`);
  return response.data;
};

/**
 * Updates an existing budget estimate.
 * @param {number} budgetId 
 * @param {Object} data 
 */
export const updateBudget = async (budgetId, data) => {
  const response = await api.put(`/budget/update/${budgetId}`, data);
  return response.data;
};

/**
 * Deletes a budget estimate by ID.
 * @param {number} budgetId 
 */
export const deleteBudget = async (budgetId) => {
  const response = await api.delete(`/budget/${budgetId}`);
  return response.data;
};

/**
 * Streams the PDF report download from the server.
 * @param {number} budgetId 
 * @param {string} fileName 
 */
export const downloadBudgetReport = async (budgetId, fileName = 'budget_report.pdf') => {
  const response = await api.get(`/budget/report/${budgetId}`, {
    responseType: 'blob'
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', fileName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
