import api from './api';

export const uploadDocument = async (projectId, file) => {
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('file', file);
  
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

export const queryDrawing = async (projectId, queryText, limit = 5) => {
  const response = await api.post('/documents/query', {
    project_id: parseInt(projectId),
    query_text: queryText,
    limit: limit
  });
  return response.data;
};

export const getDocument = async (docId) => {
  const response = await api.get(`/documents/${docId}`);
  return response.data;
};

export const getProjectDocuments = async (projectId) => {
  const response = await api.get(`/documents/project/${projectId}`);
  return response.data;
};
