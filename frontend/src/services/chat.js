import api from './api';

export const createChatSession = async (data = {}) => {
  const response = await api.post('/chat/sessions', data);
  return response.data;
};

export const listChatSessions = async (projectId = null) => {
  const params = projectId ? { project_id: projectId } : {};
  const response = await api.get('/chat/sessions', { params });
  return response.data;
};

export const getChatSession = async (sessionId) => {
  const response = await api.get(`/chat/sessions/${sessionId}`);
  return response.data;
};

export const deleteChatSession = async (sessionId) => {
  const response = await api.delete(`/chat/sessions/${sessionId}`);
  return response.data;
};

export const sendChatMessage = async (sessionId, data) => {
  const response = await api.post(`/chat/sessions/${sessionId}/message`, data);
  return response.data;
};

export const sendAudioChatMessage = async (sessionId, audioBlob, filename = 'command.wav') => {
  const formData = new FormData();
  formData.append('audio', audioBlob, filename);
  const response = await api.post(`/chat/sessions/${sessionId}/audio-message`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const sendImageChatMessage = async (sessionId, queryText, imageFile) => {
  const formData = new FormData();
  formData.append('query_text', queryText);
  formData.append('image', imageFile);
  const response = await api.post(`/chat/sessions/${sessionId}/image-message`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};
