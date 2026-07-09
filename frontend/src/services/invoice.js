import api from './api';

export const uploadInvoice = async (projectId, file) => {
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('file', file);
  
  const response = await api.post('/invoice/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

export const getInvoice = async (invoiceId) => {
  const response = await api.get(`/invoice/${invoiceId}`);
  return response.data;
};

export const analyzeInvoice = async (invoiceId) => {
  const response = await api.post('/invoice/analyze', {
    invoice_id: parseInt(invoiceId)
  });
  return response.data;
};

export const getProjectInvoices = async (projectId) => {
  const response = await api.get(`/invoice/project/${projectId}`);
  return response.data;
};

export const downloadInvoiceReport = async (invoiceId, format = 'pdf', fileName = 'invoice_audit_report') => {
  const response = await api.get(`/invoice/report/${invoiceId}?format=${format}`, {
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
