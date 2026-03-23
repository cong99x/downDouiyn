<template>
  <div id="app">
    <!-- Header -->
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <span class="logo-icon">🎬</span>
          <h1>Douyin Downloader</h1>
        </div>
        <p class="tagline">Download videos without watermark</p>
        <div class="header-actions">
          <button class="btn btn-secondary btn-sm" @click="showAuthModal = true">
            <span>🔑</span> Login Douyin
          </button>
        </div>
      </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="tab-navigation">
      <button
        class="tab-button"
        :class="{ active: activeTab === 'download' }"
        @click="activeTab = 'download'"
      >
        <span class="tab-icon">📥</span>
        Download
      </button>
      <button
        class="tab-button"
        :class="{ active: activeTab === 'management' }"
        @click="activeTab = 'management'"
      >
        <span class="tab-icon">📂</span>
        Management
      </button>
      <div class="tab-indicator" :class="{ 'tab-right': activeTab === 'management' }"></div>
    </nav>

    <!-- Tab Content -->
    <main class="app-main">
      <transition name="tab" mode="out-in">
        <DownloadTab
          v-if="activeTab === 'download'"
          key="download"
          @switch-tab="switchTab"
        />
        <ManagementTab
          v-else
          key="management"
          @switch-tab="switchTab"
        />
      </transition>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <p>Made with ❤️ for video enthusiasts</p>
    </footer>

    <!-- Modals -->
    <AuthModal v-if="showAuthModal" @close="showAuthModal = false" />
  </div>
</template>

<script>
import { ref } from 'vue';
import DownloadTab from './components/DownloadTab.vue';
import ManagementTab from './components/ManagementTab.vue';
import AuthModal from './components/AuthModal.vue';

export default {
  name: 'App',
  components: {
    DownloadTab,
    ManagementTab,
    AuthModal
  },
  setup() {
    const activeTab = ref('download');
    const showAuthModal = ref(false);

    const switchTab = (tabName) => {
      activeTab.value = tabName;
    };

    return {
      activeTab,
      showAuthModal,
      switchTab
    };
  }
};
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.app-header {
  background: var(--color-glass-bg);
  border-bottom: 1px solid var(--color-glass-border);
  backdrop-filter: blur(20px);
  padding: var(--spacing-xl) var(--spacing-lg);
  text-align: center;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.logo-icon {
  font-size: var(--font-size-3xl);
  animation: pulse 2s ease-in-out infinite;
}

.logo h1 {
  font-size: var(--font-size-2xl);
  margin: 0;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tagline {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  margin: 0;
}

/* Tab Navigation */
.tab-navigation {
  position: relative;
  display: flex;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  max-width: 600px;
  margin: 0 auto;
}

.tab-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md) var(--spacing-lg);
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  z-index: 1;
}

.tab-button:hover {
  color: var(--color-text-primary);
  background: var(--color-glass-bg);
}

.tab-button.active {
  color: var(--color-text-primary);
}

.tab-icon {
  font-size: var(--font-size-lg);
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  left: var(--spacing-lg);
  width: calc(50% - var(--spacing-lg) - var(--spacing-md) / 2);
  height: 3px;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: 3px;
  transition: transform var(--transition-normal);
  z-index: 0;
}

.tab-indicator.tab-right {
  transform: translateX(calc(100% + var(--spacing-md)));
}

/* Main Content */
.app-main {
  flex: 1;
  padding: var(--spacing-lg) 0;
}

/* Footer */
.app-footer {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  border-top: 1px solid var(--color-glass-border);
}

/* Tab Transitions */
.tab-enter-active, .tab-leave-active {
  transition: opacity var(--transition-normal), transform var(--transition-normal);
}

.tab-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.tab-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* Responsive */
@media (max-width: 640px) {
  .app-header {
    padding: var(--spacing-lg) var(--spacing-md);
  }

  .logo h1 {
    font-size: var(--font-size-xl);
  }

  .tab-navigation {
    padding: var(--spacing-md);
  }

  .tab-button {
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: var(--font-size-sm);
  }
}
</style>
