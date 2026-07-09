import api from './api';

export const getExecutiveAnalytics = async (params = {}) => {
  const response = await api.get('/projects/executive/analytics', { params });
  return response.data;
};
