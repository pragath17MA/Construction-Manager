import api from './api';

export const getProjects = async (params = {}) => {
  const response = await api.get('/projects', { params });
  return response.data;
};

export const getProject = async (id) => {
  const response = await api.get(`/projects/${id}`);
  return response.data;
};

export const createProject = async (data) => {
  const response = await api.post('/projects', data);
  return response.data;
};

export const updateProject = async (id, data) => {
  const response = await api.patch(`/projects/${id}`, data);
  return response.data;
};

export const deleteProject = async (id) => {
  const response = await api.delete(`/projects/${id}`);
  return response.data;
};

export const uploadDocument = async (projectId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post(`/projects/${projectId}/documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const uploadDrawing = async (projectId, name, file) => {
  const formData = new FormData();
  formData.append('drawing_name', name);
  formData.append('file', file);
  const response = await api.post(`/projects/${projectId}/drawings`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const uploadSiteImage = async (projectId, captureDate, file) => {
  const formData = new FormData();
  formData.append('capture_date', captureDate);
  formData.append('file', file);
  const response = await api.post(`/projects/${projectId}/images`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const deleteProjectFile = async (projectId, fileId, category) => {
  const response = await api.delete(`/projects/${projectId}/files/${fileId}`, {
    params: { category },
  });
  return response.data;
};

export const addProjectMember = async (projectId, userId, role) => {
  const response = await api.post(`/projects/${projectId}/members`, {
    user_id: userId,
    role,
  });
  return response.data;
};

export const removeProjectMember = async (projectId, userId) => {
  const response = await api.delete(`/projects/${projectId}/members/${userId}`);
  return response.data;
};

export const getAllUsers = async () => {
  const response = await api.get('/auth/users');
  return response.data;
};
