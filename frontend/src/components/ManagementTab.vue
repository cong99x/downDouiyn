<template>
  <div class="management-tab fade-in">
    <div class="management-container">
      <!-- Header -->
      <div class="management-header">
        <div>
          <h2>📂 Downloaded Videos</h2>
          <p class="subtitle">Manage and preview your downloaded videos</p>
        </div>
        <button class="btn btn-secondary" @click="loadFiles" :disabled="isLoading">
          <span v-if="!isLoading">🔄 Refresh</span>
          <span v-else class="flex items-center gap-sm">
            <div class="spinner spinner-sm"></div>
            Loading...
          </span>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading && videos.length === 0" class="loading-state">
        <div class="spinner"></div>
        <p>Loading videos...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!isLoading && videos.length === 0" class="empty-state card">
        <div class="empty-icon">📭</div>
        <h3>No videos yet</h3>
        <p>Download some videos to see them here!</p>
        <button class="btn btn-primary mt-md" @click="$emit('switch-tab', 'download')">
          Start Downloading
        </button>
      </div>

      <!-- Video Grid -->
      <div v-else class="video-grid">
        <VideoCard
          v-for="video in videos"
          :key="video.filename"
          :video="video"
          @preview="openPreview"
          @delete="confirmDelete"
        />
      </div>

      <!-- Video Preview Modal -->
      <transition name="modal">
        <div v-if="previewVideo" class="modal-overlay" @click="closePreview">
          <div class="modal-content" @click.stop>
            <button class="modal-close" @click="closePreview">✕</button>
            
            <div class="modal-header">
              <h3>{{ previewVideo.title }}</h3>
              <p class="modal-author">by {{ previewVideo.author }}</p>
            </div>

            <div class="modal-body">
              <video
                :src="getVideoUrl(previewVideo.file_path)"
                controls
                autoplay
                class="preview-video"
              >
                Your browser does not support video playback.
              </video>
            </div>

            <div class="modal-footer">
              <div class="video-info">
                <span>📁 {{ previewVideo.file_size_mb }} MB</span>
                <span>📅 {{ previewVideo.download_date_formatted }}</span>
              </div>
              <div class="modal-actions">
                <button class="btn btn-primary" @click="downloadVideo(previewVideo)">
                  📥 Download
                </button>
                <button class="btn btn-danger" @click="confirmDelete(previewVideo)">
                  🗑️ Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- Delete Confirmation Modal -->
      <transition name="modal">
        <div v-if="deleteConfirm" class="modal-overlay" @click="deleteConfirm = null">
          <div class="modal-content modal-small" @click.stop>
            <div class="modal-header">
              <h3>⚠️ Confirm Delete</h3>
            </div>

            <div class="modal-body">
              <p>Are you sure you want to delete this video?</p>
              <p class="delete-filename">{{ deleteConfirm.filename }}</p>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="deleteConfirm = null">
                Cancel
              </button>
              <button class="btn btn-danger" @click="handleDelete">
                Delete
              </button>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import VideoCard from './VideoCard.vue';
import { getFiles, deleteFile, getVideoStreamUrl, getFileDownloadUrl } from '../services/api';

export default {
  name: 'ManagementTab',
  components: {
    VideoCard
  },
  emits: ['switch-tab'],
  setup() {
    const videos = ref([]);
    const isLoading = ref(false);
    const previewVideo = ref(null);
    const deleteConfirm = ref(null);

    const loadFiles = async () => {
      isLoading.value = true;
      try {
        const response = await getFiles();
        if (response.status === 'success') {
          videos.value = response.data.files || [];
        }
      } catch (error) {
        console.error('Failed to load files:', error);
      } finally {
        isLoading.value = false;
      }
    };

    const openPreview = (video) => {
      previewVideo.value = video;
    };

    const closePreview = () => {
      previewVideo.value = null;
    };

    const confirmDelete = (video) => {
      deleteConfirm.value = video;
      closePreview();
    };

    const handleDelete = async () => {
      if (!deleteConfirm.value) return;

      try {
        // Use file_path for more accurate deletion in subfolders
        const response = await deleteFile(deleteConfirm.value.file_path);
        if (response.status === 'success') {
          // Remove from list
          videos.value = videos.value.filter(v => v.file_path !== deleteConfirm.value.file_path);
          deleteConfirm.value = null;
        }
      } catch (error) {
        console.error('Failed to delete file:', error);
        alert('Failed to delete file. Please try again.');
      }
    };

    const getVideoUrl = (filename) => {
      return getVideoStreamUrl(filename);
    };

    const downloadVideo = (video) => {
      const url = getFileDownloadUrl(video.file_path);
      const filename = video.filename || 'video.mp4';
      
      console.log('Manually triggering download for:', url);
      
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      
      if (isMobile) {
        window.location.href = url;
      } else {
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    };

    onMounted(() => {
      loadFiles();
    });

    return {
      videos,
      isLoading,
      previewVideo,
      deleteConfirm,
      loadFiles,
      openPreview,
      closePreview,
      confirmDelete,
      handleDelete,
      getVideoUrl,
      downloadVideo
    };
  }
};
</script>

<style scoped>
.management-tab {
  padding: var(--spacing-lg);
}

.management-container {
  max-width: 1400px;
  margin: 0 auto;
}

.management-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.management-header h2 {
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

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  gap: var(--spacing-md);
  color: var(--color-text-secondary);
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: var(--spacing-xl) * 2;
}

.empty-icon {
  font-size: 5rem;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
}

.empty-state h3 {
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.empty-state p {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

/* Video Grid */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-lg);
}

.modal-content {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-glass-border);
  border-radius: var(--radius-lg);
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: var(--shadow-lg);
}

.modal-small {
  max-width: 500px;
}

.modal-close {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  width: 40px;
  height: 40px;
  border: none;
  background: var(--color-glass-bg);
  color: var(--color-text-primary);
  border-radius: 50%;
  font-size: var(--font-size-xl);
  cursor: pointer;
  transition: all var(--transition-normal);
  z-index: 10;
}

.modal-close:hover {
  background: var(--color-error);
  transform: rotate(90deg);
}

.modal-header {
  padding: var(--spacing-xl);
  border-bottom: 1px solid var(--color-glass-border);
}

.modal-header h3 {
  margin: 0;
  color: var(--color-text-primary);
  padding-right: var(--spacing-xl);
}

.modal-author {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-xs);
}

.modal-body {
  padding: var(--spacing-xl);
}

.preview-video {
  width: 100%;
  border-radius: var(--radius-md);
  background: black;
}

.delete-filename {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-family: monospace;
  background: var(--color-bg-tertiary);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-sm);
  word-break: break-all;
}

.modal-footer {
  padding: var(--spacing-xl);
  border-top: 1px solid var(--color-glass-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.video-info {
  display: flex;
  gap: var(--spacing-md);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.modal-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* Modal Transitions */
.modal-enter-active, .modal-leave-active {
  transition: opacity var(--transition-normal);
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform var(--transition-normal);
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
}

/* Responsive */
@media (max-width: 768px) {
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: var(--spacing-md);
  }

  .modal-content {
    max-width: 100%;
    margin: var(--spacing-md);
  }

  .modal-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .modal-footer .btn {
    width: 100%;
  }
}
</style>
