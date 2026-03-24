<template>
  <header class="app-header">
    <div class="header-content">
      <div class="header-left">
        <h1 class="text-h3">GraphRAG</h1>
      </div>
      <div class="header-right">
        <button class="theme-toggle" @click="toggleTheme" title="切换主题">
          {{ theme === 'light' ? '🌙' : '☀️' }}
        </button>
        <div class="header-divider"></div>
        <div class="user-menu">
          <span class="text-body">Admin</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { theme, toggleTheme } = useTheme()
</script>

<style scoped lang="scss">
.app-header {
  background: var(--bg-1);
  border-bottom: 1px solid var(--border-light);
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 100%;
}

.header-left {
  h1 {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-toggle {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all var(--transition-fast);

  &:hover {
    background: var(--bg-2);
  }

  &:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
  }
}

.header-divider {
  width: 1px;
  height: 24px;
  background: var(--border-light);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    background: var(--bg-2);
  }
}

@media (max-width: 768px) {
  .app-header {
    padding: 0 16px;
  }

  .header-left h1 {
    font-size: 18px;
  }
}
</style>
