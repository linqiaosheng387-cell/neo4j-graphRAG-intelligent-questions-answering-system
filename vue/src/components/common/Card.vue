<template>
  <div :class="['card-wrapper', { 'card-elevated': elevated }]">
    <div v-if="$slots.header" class="card-header">
      <slot name="header"></slot>
    </div>
    <div class="card-content">
      <slot></slot>
    </div>
    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  elevated?: boolean
}

withDefaults(defineProps<Props>(), {
  elevated: false
})
</script>

<style scoped lang="scss">
.card-wrapper {
  background: var(--bg-1);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);

  &:hover {
    box-shadow: var(--shadow-md);
  }

  &.card-elevated {
    box-shadow: var(--shadow-md);
  }
}

.card-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-2);
}

.card-content {
  padding: 16px;
}

.card-footer {
  padding: 16px;
  border-top: 1px solid var(--border-light);
  background: var(--bg-2);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
