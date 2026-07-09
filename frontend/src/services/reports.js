import api from './api';

export const downloadReport = async (projectId, reportType, reportFormat = 'pdf') => {
  const response = await api.get('/reports/download', {
    params: {
      project_id: projectId,
      report_type: reportType,
      report_format: reportFormat
    },
    responseType: 'blob'
  });
  return response.data;
};
