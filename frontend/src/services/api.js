import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const api = {
  getDevices: async () => axios.get(`${API_BASE}/devices`),
  getRules: async () => axios.get(`${API_BASE}/rules`),
  toggleRule: async (category, enabled) =>
    axios.post(`${API_BASE}/rules/${category}?enabled=${enabled}`),
  addBlockedService: async (domain) =>
    axios.post(`${API_BASE}/services/block?domain=${encodeURIComponent(domain)}`),
  removeBlockedService: async (domain) =>
    axios.delete(`${API_BASE}/services/block?domain=${encodeURIComponent(domain)}`),
  setStrictMode: async (enabled) =>
    axios.post(`${API_BASE}/strict-mode?enabled=${enabled}`),
};
