import api from './api';

export const createWorker = async (data) => {
  const response = await api.post('/workers', data);
  return response.data;
};

export const getWorkers = async () => {
  const response = await api.get('/workers');
  return response.data;
};

export const updateWorker = async (id, data) => {
  const response = await api.put(`/workers/${id}`, data);
  return response.data;
};

export const deleteWorker = async (id) => {
  const response = await api.delete(`/workers/${id}`);
  return response.data;
};

export const runShiftPlanner = async (data) => {
  const response = await api.post('/workers/shift-planner', data);
  return response.data;
};

export const getProjectSchedules = async (projectId) => {
  const response = await api.get(`/workers/schedules/${projectId}`);
  return response.data;
};

export const logAttendance = async (data) => {
  const response = await api.post('/attendance', data);
  return response.data;
};

export const getAttendance = async () => {
  const response = await api.get('/attendance');
  return response.data;
};

export const submitLeaveRequest = async (data) => {
  const response = await api.post('/attendance/leave', data);
  return response.data;
};

export const getLeaveRequests = async () => {
  const response = await api.get('/attendance/leave');
  return response.data;
};

export const approveLeaveRequest = async (id, status) => {
  const response = await api.put(`/attendance/leave/${id}/approve`, { status });
  return response.data;
};

export const downloadAttendanceCsv = async (fileName = 'attendance_logs.csv') => {
  const response = await api.get('/attendance/csv', {
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

export const downloadWorkerReportPdf = async (projectId, startDate, endDate, fileName = 'worker_roster.pdf') => {
  const response = await api.get(`/workers/worker-report/${projectId}?start_date=${startDate}&end_date=${endDate}`, {
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
