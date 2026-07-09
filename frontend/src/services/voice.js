import api, { getBaseURL } from './api';

export const submitVoiceCommand = async (projectId, commandText = null, audioBlob = null) => {
  const formData = new FormData();
  if (projectId) {
    formData.append('project_id', projectId);
  }
  if (commandText) {
    formData.append('command_text', commandText);
  }
  if (audioBlob) {
    formData.append('audio', audioBlob, 'command.wav');
  }

  const response = await api.post('/voice/command', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getVoiceHistory = async (projectId) => {
  const response = await api.get(`/voice/history/${projectId}`);
  return response.data;
};

export const getVoiceAudioUrl = (filename) => {
  const baseURL = getBaseURL();
  return `${baseURL}/voice/audio/${filename}`;
};
