import { request } from './client';

export const api = {
  health: () => request('/health'),
  readiness: () => request('/health/ready'),

  dashboardSummary: () => request('/dashboard/summary'),
  timeline: (hours = 24) => request('/dashboard/timeline', { params: { hours } }),
  recentAlerts: (limit = 20) => request('/dashboard/recent-alerts', { params: { limit } }),

  listEvents: (params = {}) => request('/events', { params }),
  getEvent: (id) => request(`/events/${id}`),
  getEventAnalysis: (id) => request(`/events/${id}/analysis`),

  listDevices: (params = {}) => request('/devices', { params }),
  createDevice: (body) => request('/devices', { method: 'POST', body }),
  updateDevice: (id, body) => request(`/devices/${id}`, { method: 'PATCH', body }),
  deviceEvents: (id, params = {}) => request(`/devices/${id}/events`, { params }),

  listDiscoveryHosts: (params = {}) => request('/discovery/hosts', { params }),
  startDiscoveryJob: (target_cidr) =>
    request('/discovery/jobs', { method: 'POST', body: { target_cidr } }),
  getDiscoveryJob: (id) => request(`/discovery/jobs/${id}`),

  listDemoScenarios: () => request('/demo/scenarios'),
  runDemoScenario: (scenarioName) => request(`/demo/scenarios/${scenarioName}`, { method: 'POST' }),
  resetDemo: () => request('/demo/reset', { method: 'POST' }),
};
