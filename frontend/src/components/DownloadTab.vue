<template>
  <div class="download-tab fade-in">
    <div class="download-container">
      <!-- Header -->
      <div class="download-header">
        <h2>📥 Download Video</h2>
        <p class="subtitle">Paste a Douyin or TikTok video URL to download without watermark</p>
      </div>

      <!-- Download Form -->
      <div class="download-form card">
        <div class="input-group">
          <input
            v-model="videoUrl"
            type="text"
            class="input"
            placeholder="https://v.douyin.com/xxxxx/ or https://www.tiktok.com/..."
            @keyup.enter="handleDownload"
            :disabled="isDownloading"
          />
          <button
            class="btn btn-primary"
            @click="handleDownload"
            :disabled="!videoUrl || isDownloading"
          >
            <span v-if="!isDownloading">Download</span>
            <span v-else class="flex items-center gap-sm">
              <div class="spinner spinner-sm"></div>
              Downloading...
            </span>
          </button>
        </div>

        <!-- Progress Bar -->
        <div v-if="isDownloading" class="download-progress-container fade-in">
          <div class="progress-info">
            <span>{{ progressStatus }}</span>
            <span>{{ downloadProgress }}%</span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: downloadProgress + '%' }"
            ></div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="alert alert-error slide-in">
          <span class="alert-icon">⚠️</span>
          <span>{{ errorMessage }}</span>
        </div>
      </div>

      <!-- Download Result -->
      <transition name="fade">
        <div v-if="downloadResult" class="download-result card fade-in">
          <div class="result-header">
            <span class="success-icon">✅</span>
            <h3>Download Successful!</h3>
          </div>
          
          <div class="result-content">
            <div class="result-info">
              <div class="info-item">
                <span class="label">Title:</span>
                <span class="value">{{ downloadResult.title }}</span>
              </div>
              <div class="info-item">
                <span class="label">Author:</span>
                <span class="value">{{ downloadResult.author }}</span>
              </div>
              <div class="info-item">
                <span class="label">File:</span>
                <span class="value">{{ downloadResult.filename }}</span>
              </div>
            </div>

            <div class="result-actions">
              <button class="btn btn-success" @click="manualDownload">
                📥 Download Video
              </button>
              <button class="btn btn-secondary" @click="clearResult">
                Download Another
              </button>
              <button class="btn btn-primary" @click="$emit('switch-tab', 'management')">
                View Downloads
              </button>
            </div>
          </div>
        </div>
      </transition>

      <!-- Instructions -->
      <div class="instructions card">
        <h4>📝 How to use:</h4>
        <ol>
          <li>Open Douyin or TikTok app and find the video you want to download</li>
          <li>Tap the <strong>Share</strong> button and copy the link</li>
          <li>Paste the link in the input field above</li>
          <li>Click <strong>Download</strong> and wait for the process to complete</li>
          <li>Your video will be saved without watermark!</li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { downloadVideo, API_BASE_URL, getFileDownloadUrl } from '../services/api';

export default {
  name: 'DownloadTab',
  emits: ['switch-tab'],
  setup() {
    const videoUrl = ref('');
    const isDownloading = ref(false);
    const errorMessage = ref('');
    const downloadResult = ref(null);
    const downloadProgress = ref(0);
    const progressStatus = ref('Preparing...');
    let eventSource = null;

    const startProgressTracking = () => {
      if (eventSource) eventSource.close();
      
      const sseUrl = `${API_BASE_URL}/download/progress`;
      
      eventSource = new EventSource(sseUrl);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          downloadProgress.value = data.progress;
          if (data.progress > 0 && data.progress < 100) {
            progressStatus.value = 'Downloading video...';
          } else if (data.progress >= 100) {
            progressStatus.value = 'Processing...';
          }
        } catch (err) {
          console.error('Error parsing SSE data:', err);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE Error:', err);
        eventSource.close();
      };
    };

    const stopProgressTracking = () => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    };

    const triggerAutoDownload = (fileInfo) => {
      // Use the filename/path returned from backend
      // downloadResult.file_path in background was absolute, 
      // but getFileDownloadUrl handles both relative and absolute if same domain
      // Better to use filename directly or ensure we pass relative path
      const downloadPath = fileInfo.file_path || fileInfo.filename;
      const url = getFileDownloadUrl(downloadPath);
      
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileInfo.filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const handleDownload = async () => {
      if (!videoUrl.value.trim()) {
        errorMessage.value = 'Please enter a video URL';
        return;
      }

      // Clear previous state
      errorMessage.value = '';
      downloadResult.value = null;
      isDownloading.value = true;
      downloadProgress.value = 0;
      progressStatus.value = 'Initializing download...';

      // Start tracking progress via SSE
      startProgressTracking();

      try {
        const response = await downloadVideo(videoUrl.value);
        
        if (response.status === 'success') {
          downloadResult.value = response.data;
          videoUrl.value = ''; // Clear input
          downloadProgress.value = 100;
        } else {
          errorMessage.value = response.message || 'Download failed';
        }
      } catch (error) {
        console.error('Download error:', error);
        errorMessage.value = error.message || 'Failed to download video. Please check the URL and try again.';
      } finally {
        isDownloading.value = false;
        stopProgressTracking();
      }
    };

    const clearResult = () => {
      downloadResult.value = null;
      errorMessage.value = '';
    };

    const manualDownload = () => {
      if (downloadResult.value) {
        triggerAutoDownload(downloadResult.value);
      }
    };

    return {
      videoUrl,
      isDownloading,
      errorMessage,
      downloadResult,
      downloadProgress,
      progressStatus,
      handleDownload,
      clearResult,
      manualDownload
    };
  }
};
</script>

<style scoped>
.download-tab {
  padding: var(--spacing-lg);
  max-width: 800px;
  margin: 0 auto;
}

.download-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.download-header {
  text-align: center;
}

.download-header h2 {
  font-size: var(--font-size-2xl);
  margin-bottom: var(--spacing-xs);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.download-form {
  padding: var(--spacing-xl);
}

.input-group {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.input-group .input {
  flex: 1;
}

.input-group .btn {
  white-space: nowrap;
  min-width: 140px;
}

/* Progress Bar Styles */
.download-progress-container {
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid hsla(var(--color-primary-hsl), 0.2);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.progress-bar {
  height: 8px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  transition: width 0.3s ease;
  box-shadow: 0 0 10px hsla(var(--color-primary-hsl), 0.5);
}

/* Alert Styles */
.alert {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.alert-error {
  background: hsla(0, 85%, 60%, 0.1);
  border: 1px solid hsla(0, 85%, 60%, 0.3);
  color: var(--color-error);
}

.alert-icon {
  font-size: var(--font-size-lg);
}

/* Download Result */
.download-result {
  padding: var(--spacing-xl);
  border: 2px solid var(--color-success);
}

.result-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.success-icon {
  font-size: var(--font-size-2xl);
}

.result-header h3 {
  color: var(--color-success);
  margin: 0;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.result-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.info-item {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
}

.info-item .label {
  font-weight: 600;
  color: var(--color-text-secondary);
  min-width: 80px;
}

.info-item .value {
  color: var(--color-text-primary);
  word-break: break-word;
}

.result-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
}

/* Instructions */
.instructions {
  padding: var(--spacing-lg);
}

.instructions h4 {
  margin-bottom: var(--spacing-md);
  color: var(--color-primary-light);
}

.instructions ol {
  padding-left: var(--spacing-lg);
  color: var(--color-text-secondary);
  line-height: 1.8;
}

.instructions li {
  margin-bottom: var(--spacing-xs);
}

.instructions strong {
  color: var(--color-text-primary);
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity var(--transition-normal);
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 640px) {
  .input-group {
    flex-direction: column;
  }
  
  .input-group .btn {
    width: 100%;
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .result-actions .btn {
    width: 100%;
  }
}
</style>
