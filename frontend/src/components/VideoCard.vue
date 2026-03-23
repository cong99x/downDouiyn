<template>
  <div class="video-card card" @click="$emit('preview', video)">
    <div class="card-thumbnail">
      <div v-if="thumbnailUrl" class="thumbnail-image" :style="{ backgroundImage: `url(${thumbnailUrl})` }">
        <div class="play-overlay">
          <span class="play-icon">▶</span>
        </div>
      </div>
      <div v-else class="thumbnail-placeholder">
        <span class="video-icon">🎬</span>
      </div>
      
      <div v-if="video.duration" class="duration-badge">
        {{ formatDuration(video.duration) }}
      </div>
    </div>

    <div class="card-content">
      <h4 class="video-title" :title="video.title">{{ truncateTitle(video.title) }}</h4>
      <p class="video-author">👤 {{ video.author }}</p>
      
      <div class="video-meta">
        <span class="meta-item">
          <span class="meta-icon">📁</span>
          {{ video.file_size_mb }} MB
        </span>
        <span class="meta-item">
          <span class="meta-icon">📅</span>
          {{ formatDate(video.download_date_formatted) }}
        </span>
      </div>
    </div>

    <div class="card-actions" @click.stop>
      <button 
        class="btn-icon btn-primary" 
        @click="downloadVideo"
        title="Download to my computer"
      >
        📥
      </button>
      <button 
        class="btn-icon btn-danger" 
        @click="$emit('delete', video)"
        title="Delete video"
      >
        🗑️
      </button>
    </div>
  </div>
</template>

<script>
import { getFileDownloadUrl, getVideoStreamUrl } from '../services/api';

export default {
  name: 'VideoCard',
  props: {
    video: {
      type: Object,
      required: true
    }
  },
  emits: ['preview', 'delete'],
  computed: {
    thumbnailUrl() {
      if (!this.video.thumbnail) return null;
      // If it's already a full URL (external), return it
      if (this.video.thumbnail.startsWith('http')) return this.video.thumbnail;
      // Otherwise serve via API
      return getVideoStreamUrl(this.video.thumbnail);
    }
  },
  methods: {
    truncateTitle(title) {
      const maxLength = 60;
      return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
    },

    downloadVideo() {
      const url = getFileDownloadUrl(this.video.file_path);
      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', this.video.filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    
    formatDuration(seconds) {
      if (!seconds) return '0:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
    
    formatDate(dateStr) {
      if (!dateStr) return 'Unknown';
      // Format: YYYY-MM-DD HH:MM:SS -> MM/DD
      const parts = dateStr.split(' ')[0].split('-');
      return `${parts[1]}/${parts[2]}`;
    }
  }
};
</script>

<style scoped>
.video-card {
  position: relative;
  cursor: pointer;
  padding: 0;
  overflow: hidden;
  transition: all var(--transition-normal);
}

.video-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-lg), 0 0 30px rgba(138, 43, 226, 0.2);
}

.card-thumbnail {
  position: relative;
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: var(--color-bg-tertiary);
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  transition: transform var(--transition-slow);
}

.video-card:hover .thumbnail-image {
  transform: scale(1.1);
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-bg-secondary) 0%, var(--color-bg-tertiary) 100%);
}

.video-icon {
  font-size: 4rem;
  opacity: 0.3;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.video-card:hover .play-overlay {
  opacity: 1;
}

.play-icon {
  font-size: 3rem;
  color: white;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.duration-badge {
  position: absolute;
  bottom: var(--spacing-xs);
  right: var(--spacing-xs);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.card-content {
  padding: var(--spacing-md);
}

.video-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-primary);
  line-height: 1.4;
}

.video-author {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.video-meta {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.meta-icon {
  font-size: var(--font-size-sm);
}

.card-actions {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  display: flex;
  gap: var(--spacing-xs);
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.video-card:hover .card-actions {
  opacity: 1;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: var(--color-glass-bg);
  backdrop-filter: blur(10px);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-lg);
  transition: all var(--transition-normal);
}

.btn-icon:hover {
  transform: scale(1.1);
  box-shadow: var(--shadow-md);
}

.btn-danger:hover {
  background: var(--color-error);
}
</style>
