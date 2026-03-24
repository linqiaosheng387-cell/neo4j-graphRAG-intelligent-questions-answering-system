<template>
  <div class="stat-card">
    <div class="stat-header">
      <div class="stat-icon" :style="{ background: iconBg }">
        <slot name="icon"></slot>
      </div>
      <div class="stat-title">
        <div class="text-caption text-secondary">{{ label }}</div>
        <div v-if="trend" :class="['stat-trend', trend > 0 ? 'positive' : 'negative']">
          <span>{{ trend > 0 ? '↑' : '↓' }}</span>
          <span>{{ Math.abs(trend) }}%</span>
        </div>
      </div>
    </div>
    <div class="stat-value">
      <span class="number-value" :class="{ positive: trend && trend > 0, negative: trend && trend < 0 }">
        {{ formatNumber(value) }}
      </span>
      <span v-if="unit" class="unit">{{ unit }}</span>
    </div>
    <div v-if="$slots.footer" class="stat-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string
  value: number
  unit?: string
  trend?: number
  iconBg?: string
}

withDefaults(defineProps<Props>(), {
  iconBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
})

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toLocaleString()
}
</script>

<style scoped lang="scss">
.stat-card {
  background: var(--bg-1);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 16px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);

  &:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }
}

.stat-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-title {
  flex: 1;
}

.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 4px;

  &.positive {
    color: var(--success);
  }

  &.negative {
    color: var(--error);
  }
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.stat-footer {
  padding-top: 8px;
  border-top: 1px solid var(--border-light);
  font-size: 12px;
  color: var(--text-3);
}
</style>
