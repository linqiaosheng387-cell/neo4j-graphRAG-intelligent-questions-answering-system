<template>
  <div class="operation-monitoring">
    <h1>运维监控</h1>

    <!-- 日志筛选 -->
    <div class="filter-bar">
      <el-select v-model="filterLevel" placeholder="日志级别" style="width: 150px">
        <el-option label="全部" value=""></el-option>
        <el-option label="INFO" value="INFO"></el-option>
        <el-option label="WARNING" value="WARNING"></el-option>
        <el-option label="ERROR" value="ERROR"></el-option>
        <el-option label="CRITICAL" value="CRITICAL"></el-option>
      </el-select>

      <el-input
        v-model="searchModule"
        placeholder="搜索模块..."
        style="width: 300px; margin-left: 10px"
        clearable
      ></el-input>

      <el-button type="primary" @click="loadLogs" style="margin-left: 10px">
        <i class="el-icon-search"></i> 搜索
      </el-button>
    </div>

    <!-- 日志列表 -->
    <el-table
      :data="logs"
      style="width: 100%; margin-top: 20px"
      v-loading="loading"
      stripe
      border
    >
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="log_level" label="级别" width="100">
        <template #default="{ row }">
          <el-tag
            :type="
              row.log_level === 'ERROR' || row.log_level === 'CRITICAL'
                ? 'danger'
                : row.log_level === 'WARNING'
                ? 'warning'
                : 'info'
            "
          >
            {{ row.log_level }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="module" label="模块" width="120"></el-table-column>
      <el-table-column prop="message" label="消息" show-overflow-tooltip></el-table-column>
      <el-table-column prop="created_at" label="时间" width="180"></el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleViewLog(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      style="margin-top: 20px; text-align: right"
      @change="loadLogs"
    ></el-pagination>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="showLogDialog" title="日志详情" width="800px">
      <div v-if="currentLog" class="log-details">
        <div class="log-item">
          <span class="label">日志级别：</span>
          <el-tag :type="currentLog.log_level === 'ERROR' ? 'danger' : 'info'">
            {{ currentLog.log_level }}
          </el-tag>
        </div>
        <div class="log-item">
          <span class="label">模块：</span>
          <span>{{ currentLog.module }}</span>
        </div>
        <div class="log-item">
          <span class="label">消息：</span>
          <p class="message">{{ currentLog.message }}</p>
        </div>
        <div v-if="currentLog.stack_trace" class="log-item">
          <span class="label">堆栈跟踪：</span>
          <pre class="stack-trace">{{ currentLog.stack_trace }}</pre>
        </div>
        <div v-if="currentLog.solution" class="log-item">
          <span class="label">解决方案：</span>
          <p class="solution">{{ currentLog.solution }}</p>
        </div>
        <div class="log-item">
          <span class="label">时间：</span>
          <span>{{ currentLog.created_at }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logsAPI } from '@/api/logs'

const logs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterLevel = ref('')
const searchModule = ref('')
const showLogDialog = ref(false)
const currentLog = ref<any>(null)

const loadLogs = async () => {
  loading.value = true
  try {
    const response = await logsAPI.getSystemLogs(
      currentPage.value,
      pageSize.value,
      filterLevel.value,
      searchModule.value
    )
    logs.value = response.data || []
    total.value = response.total || 0
  } catch (error) {
    console.error('Failed to load logs:', error)
  } finally {
    loading.value = false
  }
}

const handleViewLog = (log: any) => {
  currentLog.value = log
  showLogDialog.value = true
}

onMounted(() => {
  loadLogs()
  // 每10秒自动刷新一次
  setInterval(loadLogs, 10000)
})
</script>

<style scoped lang="scss">
.operation-monitoring {
  h1 {
    margin-bottom: 20px;
    color: #333;
  }

  .filter-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
  }

  .log-details {
    .log-item {
      margin-bottom: 20px;

      .label {
        font-weight: bold;
        color: #333;
        display: inline-block;
        width: 100px;
      }

      .message {
        margin: 10px 0 0 100px;
        padding: 10px;
        background: #f5f7fa;
        border-radius: 4px;
        line-height: 1.6;
      }

      .stack-trace {
        margin: 10px 0 0 100px;
        padding: 10px;
        background: #f5f7fa;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 12px;
        line-height: 1.4;
      }

      .solution {
        margin: 10px 0 0 100px;
        padding: 10px;
        background: #f0f9ff;
        border-left: 3px solid #667eea;
        border-radius: 4px;
        line-height: 1.6;
      }
    }
  }
}
</style>
