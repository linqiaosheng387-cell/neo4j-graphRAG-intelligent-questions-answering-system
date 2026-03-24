<template>
  <div class="table-wrapper">
    <div v-if="loading" class="table-skeleton">
      <div v-for="i in 5" :key="i" class="skeleton-row">
        <div v-for="j in columns.length" :key="j" class="skeleton-cell skeleton"></div>
      </div>
    </div>
    <div v-else-if="data.length === 0" class="table-empty">
      <div class="empty-icon">📭</div>
      <div class="empty-text">暂无数据</div>
    </div>
    <table v-else class="data-table">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col.key" :style="{ width: col.width }">
            <div class="th-content">
              {{ col.label }}
              <span v-if="col.sortable" class="sort-icon">⇅</span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in data" :key="idx" class="data-row">
          <td v-for="col in columns" :key="col.key">
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
              {{ formatCellValue(row[col.key], col.type) }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
interface Column {
  key: string
  label: string
  width?: string
  type?: 'text' | 'number' | 'date' | 'status'
  sortable?: boolean
}

interface Props {
  columns: Column[]
  data: any[]
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false
})

const formatCellValue = (value: any, type?: string) => {
  if (value === null || value === undefined) return '-'

  switch (type) {
    case 'number':
      return typeof value === 'number' ? value.toLocaleString() : value
    case 'date':
      return new Date(value).toLocaleDateString('zh-CN')
    default:
      return value
  }
}
</script>

<style scoped lang="scss">
.table-wrapper {
  background: var(--bg-1);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;

  thead {
    background: var(--bg-2);
    border-bottom: 1px solid var(--border-light);
  }

  th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    color: var(--text-1);
  }

  .th-content {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .sort-icon {
    opacity: 0.5;
    font-size: 12px;
  }

  tbody tr {
    border-bottom: 1px solid var(--border-light);
    transition: background-color var(--transition-fast);

    &:hover {
      background: var(--bg-2);
    }

    &:last-child {
      border-bottom: none;
    }
  }

  td {
    padding: 12px 16px;
    color: var(--text-2);
  }
}

.table-skeleton {
  padding: 16px;
}

.skeleton-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.skeleton-cell {
  height: 20px;
  border-radius: 4px;
}

.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-3);

  .empty-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }

  .empty-text {
    font-size: 14px;
  }
}

// 响应式
@media (max-width: 768px) {
  .data-table {
    font-size: 12px;

    th,
    td {
      padding: 8px 12px;
    }
  }
}
</style>
