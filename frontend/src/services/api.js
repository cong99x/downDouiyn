/**
 * API Service - Centralized API client for backend communication.
 * Single Responsibility: Handle all HTTP requests to backend.
 */

import axios from 'axios';

// Determine API Base URL based on environment
const getBaseUrl = () => {
    if (import.meta.env.DEV) {
        // In local development, if VITE_API_URL is missing, use current hostname
        // This allows mobile testing on the same network
        const apiUrl = import.meta.env.VITE_API_URL;
        if (apiUrl) return apiUrl.endsWith('/api') ? apiUrl : `${apiUrl.replace(/\/$/, '')}/api`;
        
        const host = window.location.hostname;
        return `http://${host}:5000/api`;
    }
    
    let url = import.meta.env.VITE_API_URL || '';
    
    // If empty, use relative path /api (assume same domain proxy)
    if (!url) return '/api';
    
    // Ensure URL doesn't end with slash before check
    url = url.replace(/\/$/, '');
    
    // If URL is provided but missing the /api suffix, append it
    if (!url.endsWith('/api')) {
        return `${url}/api`;
    }
    
    return url;
};

export const API_BASE_URL = getBaseUrl();

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 300000, // 300 seconds (5 minutes) for video downloads
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor
apiClient.interceptors.request.use(
    (config) => {
        console.log(`[API] ${config.method.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor
apiClient.interceptors.response.use(
    (response) => {
        console.log(`[API] Response:`, response.data);
        return response;
    },
    (error) => {
        console.error('[API] Response error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

/**
 * Download video from URL
 * @param {string} url - Douyin/TikTok video URL
 * @returns {Promise} API response
 */
export const downloadVideo = async (url) => {
    try {
        const response = await apiClient.post('/download', { url });
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

/**
 * Get list of downloaded files
 * @returns {Promise} API response with file list
 */
export const getFiles = async () => {
    try {
        const response = await apiClient.get('/files');
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

/**
 * Get information about a specific file
 * @param {string} filename - Name of the file
 * @returns {Promise} API response with file info
 */
export const getFileInfo = async (filename) => {
    try {
        const response = await apiClient.get(`/files/${filename}`);
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

/**
 * Delete a file
 * @param {string} filename - Name of the file to delete
 * @returns {Promise} API response
 */
export const deleteFile = async (filename) => {
    try {
        const response = await apiClient.delete(`/files/${filename}`);
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

/**
 * Get video stream URL for preview
 * @param {string} filename - Name of the file
 * @returns {string} Stream URL
 */
export const getVideoStreamUrl = (filename) => {
    return `${API_BASE_URL}/files/stream?path=${encodeURIComponent(filename)}`;
};

/**
 * Get video download URL
 * @param {string} filename - Name of the file
 * @returns {string} Download URL
 */
export const getFileDownloadUrl = (filename) => {
    return `${API_BASE_URL}/files/download?path=${encodeURIComponent(filename)}`;
};

// Auth APIs
export const getAuthCookie = async () => {
    try {
        const response = await apiClient.get('/auth/cookie');
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

export const updateAuthCookie = async (cookie) => {
    try {
        const response = await apiClient.post('/auth/cookie', { cookie });
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

export const getLoginQr = async () => {
    try {
        const response = await apiClient.get('/auth/qr');
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

export const getAuthStatus = async () => {
    try {
        const response = await apiClient.get('/auth/status');
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

export const stopLogin = async () => {
    try {
        const response = await apiClient.post('/auth/logout');
        return response.data;
    } catch (error) {
        throw error.response?.data || { status: 'error', message: error.message };
    }
};

export default {
    downloadVideo,
    getFiles,
    getFileInfo,
    deleteFile,
    getVideoStreamUrl,
    getFileDownloadUrl,
    getLoginQr,
    getAuthStatus,
    stopLogin
};
