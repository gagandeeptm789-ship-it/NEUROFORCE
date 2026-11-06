import axios from 'axios';

/** API client for The Forwarded Seal FastAPI backend. */

const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request Interceptor: Attach Bearer Token if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('fs_admin_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Centralized error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Future Phase 2 session expiration handler
      localStorage.removeItem('fs_admin_token');
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  /**
   * Endpoint: POST /api/admin/login
   */
  login: async (credentials) => {
    return apiClient.post('/api/admin/login', credentials);
  },
  getCurrentAdmin: async () => {
    return apiClient.get('/api/admin/me');
  },
};

export const noticeApi = {
  /**
   * Endpoint: GET /api/notices
   */
  getNotices: async (params = {}) => {
    return apiClient.get('/api/notices', { params });
  },

  /**
   * Endpoint: GET /api/notices/{notice_id}
   */
  getNoticeById: async (noticeId) => {
    return apiClient.get(`/api/notices/${encodeURIComponent(noticeId)}`);
  },

  /**
   * Endpoint: POST /api/notices
   */
  createNotice: async (formData) => {
    return apiClient.post('/api/notices', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Verification Endpoint:
   * Supports file upload, Notice ID lookup, or combined verification.
   * Endpoint: POST /api/verification/verify or GET /api/verification/notices/{notice_id}
   */
  verifyDocument: async (input) => {
    let file = null;
    let noticeId = null;
    let qrData = null;

    if (input instanceof File || input instanceof Blob) {
      file = input;
    } else if (typeof input === 'string') {
      noticeId = input;
    } else if (input && typeof input === 'object') {
      file = input.file;
      noticeId = input.noticeId;
      qrData = input.qrData;
    }

    if (file) {
      const data = new FormData();
      data.append('file', file);
      if (noticeId) data.append('notice_id', noticeId);
      if (qrData) data.append('qr_data', qrData);
      return apiClient.post('/api/verification/verify', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    } else if (noticeId) {
      return apiClient.get(`/api/verification/notices/${encodeURIComponent(noticeId)}`);
    } else {
      throw new Error('Please provide an official document file or Notice ID to verify.');
    }
  },
};

export default apiClient;
