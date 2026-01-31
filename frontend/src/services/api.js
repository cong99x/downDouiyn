/**
 * API Service - Centralized API client for backend communication.
 * Single Responsibility: Handle all HTTP requests to backend.
 */

import axios from 'axios';

// Create axios instance with base configuration
// Use relative path for production (Nginx proxy) or absolute for local dev if needed
// Recommend using vite proxy in dev to keep this relative
const apiClient = axios.create({
    baseURL: '/api',
    timeout: 60000, // 60 seconds for video downloads
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
    return `/api/files/${encodeURIComponent(filename)}/stream`;
};

export default {
    downloadVideo,
    getFiles,
    getFileInfo,
    deleteFile,
    getVideoStreamUrl
};
