<template>
  <button
    :class="[
      'btn',
      `btn-${variant}`,
      `btn-${size}`,
      { 'btn-disabled': disabled },
      { 'btn-loading': loading }
    ]"
    :disabled="disabled || loading"
    v-bind="$attrs"
  >
    <span v-if="loading" class="btn-spinner"></span>
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false
})
</script>

<style scoped lang="scss">
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  user-select: none;

  &:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
  }

  // 大小变体
  &.btn-sm {
    padding: 6px 12px;
    font-size: 12px;
    height: 28px;
  }

  &.btn-md {
    padding: 8px 16px;
    font-size: 14px;
    height: 36px;
  }

  &.btn-lg {
    padding: 10px 20px;
    font-size: 16px;
    height: 44px;
  }

  // 颜色变体
  &.btn-primary {
    background: var(--primary);
    color: white;

    &:hover:not(.btn-disabled) {
      background: var(--primary-hover);
      box-shadow: var(--shadow-md);
    }

    &:active:not(.btn-disabled) {
      background: var(--primary-active);
    }
  }

  &.btn-secondary {
    background: var(--bg-3);
    color: var(--text-1);
    border: 1px solid var(--border-color);

    &:hover:not(.btn-disabled) {
      background: var(--bg-4);
    }
  }

  &.btn-ghost {
    background: transparent;
    color: var(--primary);

    &:hover:not(.btn-disabled) {
      background: var(--primary-light);
    }
  }

  &.btn-danger {
    background: var(--error);
    color: white;

    &:hover:not(.btn-disabled) {
      background: #ff4d4f;
    }
  }

  // 禁用态
  &.btn-disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  // 加载态
  &.btn-loading {
    pointer-events: none;
  }

  .btn-spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
