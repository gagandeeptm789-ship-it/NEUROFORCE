import axios from 'axios';

/**
 * The Forwarded Seal — Backend API Service Client (Phase 2 Contract)
 * 
 * Configured to connect to the upcoming Python FastAPI backend.
 * Endpoints are prepared as documented placeholders.
 */

const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || 'http://localhost:8000';

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

/**
 * Phase 2 Backend Contract Endpoints:
 * 
 * 1. POST /api/admin/login
 *    Payload: { email, password }
 *    Returns: { access_token, token_type, admin: { id, name, role } }
 * 
 * 2. POST /api/notices
 *    Payload: FormData (title, department, file, metadata)
 *    Returns: { notice_id, status, hash, signature, qr_url, created_at }
 * 
 * 3. GET /api/notices
 *    Params: { page, limit, status, search }
 *    Returns: { items: Notice[], total, page, pages }
 * 
 * 4. GET /api/notices/{notice_id}
 *    Path param: notice_id
 *    Returns: Notice details with cryptographic verification records
 */

export const authApi = {
  /**
   * Endpoint: POST /api/admin/login
   */
  login: async (credentials) => {
    return apiClient.post('/api/admin/login', credentials);
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
   * Verification Endpoint placeholder for Phase 2:
   * Endpoint: POST /api/verify
   */
  verifyDocument: async (fileOrNoticeId) => {
    if (typeof fileOrNoticeId === 'string') {
      return apiClient.get(`/api/notices/${encodeURIComponent(fileOrNoticeId)}`);
    } else {
      const data = new FormData();
      data.append('file', fileOrNoticeId);
      return apiClient.post('/api/verify', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    }
  },
};

export default apiClient;
