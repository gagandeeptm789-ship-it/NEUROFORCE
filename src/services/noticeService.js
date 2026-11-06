import { authApi, noticeApi } from './api.js';

/**
 * Notice and Verification Service
 * Direct interface to the backend API.
 * Contains no mock or simulated data.
 */
export const noticeService = {
  /**
   * Verify an uploaded file or Notice ID via the backend verification engine.
   * Only real backend responses are returned; no fake verdicts are invented.
   */
  verifyNotice: async ({ file, noticeId }) => {
    try {
      const response = await noticeApi.verifyDocument(file || noticeId);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const status = error.response?.status;
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        (error.code === 'ERR_NETWORK' || !error.response
          ? 'Backend connection pending. The verification service is currently offline or unreachable.'
          : `Verification failed (${status || 'Unknown error'}). Please check your document and try again.`);
      
      const err = new Error(message);
      err.status = status;
      err.isNetworkError = error.code === 'ERR_NETWORK' || !error.response;
      throw err;
    }
  },

  /**
   * Fetch notices and registry ledger data for the Admin Dashboard
   */
  getNotices: async (params = {}) => {
    try {
      const response = await noticeApi.getNotices(params);
      const data = response.data || {};
      return {
        items: data.items || [],
        stats: data.stats || {
          totalNotices: 0,
          publishedNotices: 0,
          flaggedTamperedAttempts: 0,
          activeVerificationsToday: 0,
        },
        recentActivities: data.recentActivities || [],
      };
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        (error.code === 'ERR_NETWORK' || !error.response
          ? 'Backend connection pending. Unable to load notices from server.'
          : 'Failed to fetch notices.');
      
      const err = new Error(message);
      err.isNetworkError = error.code === 'ERR_NETWORK' || !error.response;
      throw err;
    }
  },

  /**
   * Fetch a single notice by ID
   */
  getNoticeById: async (id) => {
    try {
      const response = await noticeApi.getNoticeById(id);
      return response.data;
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Notice record not found or server is unreachable.';
      throw new Error(message);
    }
  },

  /**
   * Create and cryptographically sign a notice via backend
   */
  createNotice: async (formData) => {
    try {
      const response = await noticeApi.createNotice(formData);
      return response.data;
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        (error.code === 'ERR_NETWORK' || !error.response
          ? 'Backend connection pending. Cannot publish notice while server is offline.'
          : 'Failed to publish notice.');
      throw new Error(message);
    }
  },

  /**
   * Admin Login authentication
   */
  adminLogin: async (credentials) => {
    try {
      const response = await authApi.login(credentials);
      return response.data;
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        (error.code === 'ERR_NETWORK' || !error.response
          ? 'Backend connection pending. Authentication server is offline or unreachable.'
          : 'Invalid institutional credentials.');
      throw new Error(message);
    }
  },
};
