import api from './api';

export const triggerVisualAudit = async (projectId, siteImageId) => {
  const response = await api.post('/image-analysis/analyze', {
    project_id: parseInt(projectId),
    site_image_id: parseInt(siteImageId),
  });
  return response.data;
};

export const getProjectVisualAudits = async (projectId) => {
  const response = await api.get(`/image-analysis/project/${projectId}`);
  return response.data;
};

export const getImageVisualAudit = async (siteImageId) => {
  const response = await api.get(`/image-analysis/image/${siteImageId}`);
  return response.data;
};

export const getAnnotatedImageUrl = (analysisId) => {
  // Return secure backend download URL that carries standard auth tokens when fetched via state or direct source
  const baseURL = import.meta.env.VITE_API_URL || '/api';
  return `${baseURL}/image-analysis/annotated-image/${analysisId}`;
};
