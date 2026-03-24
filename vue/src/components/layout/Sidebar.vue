<template>
  <aside class="sidebar" :class="{ 'sidebar-collapsed': collapsed }">
    <nav class="nav-menu">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'nav-item-active': isActive(item.path) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
    <button class="collapse-btn" @click="collapsed = !collapsed" :title="collapsed ? '展开' : '收起'">
      {{ collapsed ? '→' : '←' }}
    </button>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const collapsed = ref(false)

const menuItems = [
  { path: '/dashboard', label: '数据面板', icon: '📊' },
  { path: '/qa', label: '问答管理', icon: '💬' },
  { path: '/graphs', label: '图谱管理', icon: '🔗' },
  { path: '/data', label: '数据管理', icon: '📁' },
  { path: '/logs', label: '运维监控', icon: '📋' },
  { path: '/access', label: '用户日志', icon: '👥' }
]

const isActive = (path: string) => {
  return route.path === path
}
</script>

<style scoped lang="scss">
.sidebar {
  width: 240px;
  background: var(--bg-1);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-base);
  overflow: hidden;

  &.sidebar-collapsed {
    width: 70px;
  }
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  color: var(--text-2);
  text-decoration: none;
  transition: all var(--transition-fast);
  white-space: nowrap;

  &:hover {
    background: var(--bg-2);
    color: var(--primary);
  }

  &.nav-item-active {
    background: var(--primary-light);
    color: var(--primary);
    font-weight: 600;
  }
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.nav-label {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapse-btn {
  background: none;
  border: none;
  color: var(--text-3);
  cursor: pointer;
  padding: 12px;
  font-size: 16px;
  transition: all var(--transition-fast);
  border-top: 1px solid var(--border-light);

  &:hover {
    color: var(--primary);
  }
}

// 响应式
@media (max-width: 768px) {
  .sidebar {
    width: 60px;

    &.sidebar-collapsed {
      width: 60px;
    }
  }

  .nav-label {
    display: none;
  }

  .nav-item {
    justify-content: center;
  }
}
</style>
