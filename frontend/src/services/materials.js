import api from './api';

export const estimateMaterials = async (data) => {
  const response = await api.post('/materials/estimate', data);
  return response.data;
};

export const getProjectMaterials = async (projectId) => {
  const response = await api.get(`/materials/project/${projectId}`);
  return response.data;
};

export const updateMaterialLine = async (id, quantity, unitPrice) => {
  const response = await api.put(`/materials/${id}?quantity=${quantity}&unit_price=${unitPrice}`);
  return response.data;
};

export const deleteMaterialLine = async (id) => {
  const response = await api.delete(`/materials/${id}`);
  return response.data;
};

export const getInventory = async () => {
  const response = await api.get('/materials/inventory/list');
  return response.data;
};

export const updateInventory = async (data) => {
  const response = await api.post('/materials/inventory/update', data);
  return response.data;
};

export const getSuppliers = async () => {
  const response = await api.get('/materials/suppliers/list');
  return response.data;
};

export const createPurchaseOrder = async (data) => {
  const response = await api.post('/materials/purchase-orders', data);
  return response.data;
};

export const getPurchaseOrders = async (projectId = null) => {
  const url = projectId ? `/materials/purchase-orders/list?project_id=${projectId}` : '/materials/purchase-orders/list';
  const response = await api.get(url);
  return response.data;
};

export const downloadMaterialsCsv = async (projectId, fileName = 'materials.csv') => {
  const response = await api.get(`/materials/project/${projectId}/csv`, {
    responseType: 'blob'
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', fileName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
