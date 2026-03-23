<template>
  <div class="auth-modal-overlay fade-in" @click.self="$emit('close')">
    <div class="auth-modal card slide-in">
      <div class="modal-header">
        <h3>🔑 Cập nhật Cookie Douyin</h3>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>
      
      <div class="modal-body">
        <!-- Current Cookie Status -->
        <div v-if="currentCookie" class="cookie-status">
          <p class="status-label">Cookie hiện tại:</p>
          <code class="cookie-preview">{{ currentCookie }}</code>
        </div>

        <!-- Instructions -->
        <div class="instructions">
          <h4>📋 Hướng dẫn lấy Cookie:</h4>
          <ol>
            <li>Truy cập <a href="https://www.douyin.com" target="_blank">douyin.com</a> và đăng nhập</li>
            <li>Nhấn <kbd>F12</kbd> để mở DevTools</li>
            <li>Chọn tab <strong>Network</strong> (Mạng)</li>
            <li>Nhấn <kbd>F5</kbd> để tải lại trang</li>
            <li>Click vào request đầu tiên (thường là tên miền)</li>
            <li>Tìm <strong>Request Headers</strong> → <strong>Cookie</strong></li>
            <li>Copy toàn bộ giá trị Cookie và paste vào ô bên dưới</li>
          </ol>
        </div>

        <!-- Cookie Input -->
        <div class="cookie-input-section">
          <label for="cookie-input">Paste Cookie vào đây:</label>
          <textarea
            id="cookie-input"
            v-model="cookieInput"
            placeholder="ttwid=xxx; msToken=xxx; sessionid=xxx; ..."
            rows="4"
          ></textarea>
        </div>

        <!-- Action Buttons -->
        <div class="modal-actions">
          <button 
            class="btn btn-primary" 
            @click="handleUpdateCookie"
            :disabled="!cookieInput || isUpdating"
          >
            <span v-if="isUpdating">Đang cập nhật...</span>
            <span v-else>💾 Lưu Cookie</span>
          </button>
          <button class="btn btn-secondary" @click="$emit('close')">Hủy</button>
        </div>

        <!-- Success/Error Message -->
        <div v-if="message" :class="['message', messageType]">
          {{ message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import axios from 'axios';

export default {
  name: 'AuthModal',
  emits: ['close'],
  setup(props, { emit }) {
    const cookieInput = ref('');
    const currentCookie = ref('');
    const isUpdating = ref(false);
    const message = ref('');
    const messageType = ref('');

    const fetchCurrentCookie = async () => {
      try {
        const response = await axios.get('/api/auth/cookie');
        if (response.data.status === 'success') {
          currentCookie.value = response.data.data.cookie_preview;
        }
      } catch (err) {
        console.error('Error fetching current cookie:', err);
      }
    };

    const handleUpdateCookie = async () => {
      if (!cookieInput.value.trim()) {
        message.value = 'Vui lòng nhập Cookie!';
        messageType.value = 'error';
        return;
      }

      isUpdating.value = true;
      message.value = '';

      try {
        const response = await axios.post('/api/auth/cookie', {
          cookie: cookieInput.value.trim()
        });

        if (response.data.status === 'success') {
          message.value = '✅ Cập nhật Cookie thành công!';
          messageType.value = 'success';
          
          // Refresh current cookie display
          await fetchCurrentCookie();
          
          // Clear input
          cookieInput.value = '';
          
          // Auto close after 2 seconds
          setTimeout(() => {
            emit('close');
          }, 2000);
        } else {
          message.value = `❌ ${response.data.message}`;
          messageType.value = 'error';
        }
      } catch (err) {
        message.value = `❌ Lỗi: ${err.response?.data?.message || err.message}`;
        messageType.value = 'error';
      } finally {
        isUpdating.value = false;
      }
    };

    onMounted(() => {
      fetchCurrentCookie();
    });

    return {
      cookieInput,
      currentCookie,
      isUpdating,
      message,
      messageType,
      handleUpdateCookie
    };
  }
};
</script>

<style scoped>
.auth-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.auth-modal {
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  background: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
}

.modal-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-bg-tertiary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  background: var(--color-bg-primary);
  z-index: 10;
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-primary-light);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
}

.cookie-status {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.status-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
}

.cookie-preview {
  display: block;
  padding: var(--spacing-sm);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--color-primary);
  word-break: break-all;
}

.instructions {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
  border-left: 3px solid var(--color-primary);
  border-radius: var(--radius-md);
}

.instructions h4 {
  margin-top: 0;
  margin-bottom: var(--spacing-sm);
  color: var(--color-primary);
}

.instructions ol {
  margin: 0;
  padding-left: var(--spacing-lg);
}

.instructions li {
  margin-bottom: var(--spacing-xs);
  line-height: 1.6;
}

.instructions a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}

.instructions a:hover {
  text-decoration: underline;
}

.instructions kbd {
  padding: 2px 6px;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.cookie-input-section {
  margin-bottom: var(--spacing-lg);
}

.cookie-input-section label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.cookie-input-section textarea {
  width: 100%;
  padding: var(--spacing-sm);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-family: monospace;
  font-size: 12px;
  resize: vertical;
  transition: border-color var(--transition-fast);
}

.cookie-input-section textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.modal-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.modal-actions .btn {
  flex: 1;
}

.message {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  text-align: center;
  font-weight: 500;
}

.message.success {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.message.error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}
</style>
