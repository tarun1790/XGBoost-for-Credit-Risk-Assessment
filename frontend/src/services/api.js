import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor with automatic Refresh Token Rotation (RTR)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken && !originalRequest.url?.includes('/auth/token') && !originalRequest.url?.includes('/auth/refresh')) {
        originalRequest._retry = true;
        try {
          const res = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          });
          if (res.data && res.data.access_token) {
            localStorage.setItem('token', res.data.access_token);
            if (res.data.refresh_token) {
              localStorage.setItem('refresh_token', res.data.refresh_token);
            }
            api.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`;
            originalRequest.headers['Authorization'] = `Bearer ${res.data.access_token}`;
            return api(originalRequest);
          }
        } catch (refreshErr) {
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          return Promise.reject(refreshErr);
        }
      } else {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await api.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    return response.data;
  },
  refresh: async (refreshToken) => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // Ignore network error on logout
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  getAuditLogs: async () => {
    const response = await api.get('/auth/audit');
    return response.data;
  },
  verifyAuditChain: async () => {
    const response = await api.get('/auth/audit/verify');
    return response.data;
  },
  getSecurityTelemetry: async () => {
    const response = await api.get('/auth/security-telemetry');
    return response.data;
  },
};

export const customerAPI = {
  list: async (search = '', skip = 0, limit = 100) => {
    const response = await api.get('/customers/', {
      params: { search, skip, limit },
    });
    return response.data;
  },
  get: async (id) => {
    const response = await api.get(`/customers/${id}`);
    return response.data;
  },
  create: async (customerData) => {
    const response = await api.post('/customers/', customerData);
    return response.data;
  },
  update: async (id, customerData) => {
    const response = await api.put(`/customers/${id}`, customerData);
    return response.data;
  },
  delete: async (id) => {
    const response = await api.delete(`/customers/${id}`);
    return response.data;
  },
};

export const predictionAPI = {
  assess: async (customerId) => {
    const response = await api.post(`/predict/${customerId}`);
    return response.data;
  },
  getHistory: async (skip = 0, limit = 50) => {
    const response = await api.get('/predict/history', {
      params: { skip, limit },
    });
    return response.data;
  },
  getDetails: async (predictionId) => {
    const response = await api.get(`/predict/history/${predictionId}`);
    return response.data;
  },
};

export const dashboardAPI = {
  getSummary: async () => {
    const response = await api.get('/dashboard/summary');
    return response.data;
  },
};

export const quantAPI = {
  getPortfolioSummary: async () => {
    const response = await api.get('/quant/portfolio-summary');
    return response.data;
  },
  runSimulation: async (numSimulations = 50000) => {
    const response = await api.post('/quant/portfolio-simulation', {
      num_simulations: numSimulations,
    });
    return response.data;
  },
  runStressTest: async (shocks) => {
    const response = await api.post('/quant/stress-test', shocks);
    return response.data;
  },
  priceLoan: async (pricingParams) => {
    const response = await api.post('/quant/price-loan', pricingParams);
    return response.data;
  },
  getTransitionMatrix: async (years = 1) => {
    const response = await api.get('/quant/transition-matrix', {
      params: { tenure_years: years },
    });
    return response.data;
  },
};

export default api;
