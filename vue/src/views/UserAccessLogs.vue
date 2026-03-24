<template>
  <div class="user-access-logs">
    <h1>用户访问日志</h1>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">总访问次数</div>
        <div class="stat-value">{{ stats.total_visits }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">IP访问数</div>
        <div class="stat-value">{{ stats.unique_ips }}</div>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar" style="margin-top: 20px">
      <el-input
        v-model="filterIP"
        placeholder="搜索IP地址..."
        style="width: 250px"
        clearable
      ></el-input>

      <el-select v-model="filterEndpoint" placeholder="筛选端点" style="width: 200px; margin-left: 10px">
        <el-option label="全部" value=""></el-option>
        <el-option label="/api/qa/records" value="/api/qa/records"></el-option>
        <el-option label="/api/dashboard/overview" value="/api/dashboard/overview"></el-option>
      </el-select>

      <el-button type="primary" @click="loadAccessLogs" style="margin-left: 10px">
        <i class="el-icon-search"></i> 搜索
      </el-button>
    </div>

    <!-- 访问日志表 -->
    <el-table
      :data="accessLogs"
      style="width: 100%; margin-top: 20px"
      v-loading="loading"
      stripe
      border
    >
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="ip_address" label="IP地址" width="150"></el-table-column>
      <el-table-column prop="endpoint" label="访问端点" width="200"></el-table-column>
      <el-table-column prop="method" label="方法" width="80"></el-table-column>
      <el-table-column prop="status_code" label="状态码" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status_code === 200 ? 'success' : 'danger'">
            {{ row.status_code }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="response_time" label="响应时间(ms)" width="120"></el-table-column>
      <el-table-column prop="device_info" label="设备信息" show-overflow-tooltip></el-table-column>
      <el-table-column prop="access_time" label="访问时间" width="180"></el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      style="margin-top: 20px; text-align: right"
      @change="loadAccessLogs"
    ></el-pagination>

    <!-- IP排名 -->
    <div style="margin-top: 40px">
      <h3>热门IP排名</h3>
      <el-table :data="topIPs" style="width: 100%; margin-top: 20px" stripe border>
        <el-table-column prop="ip_address" label="IP地址" width="150"></el-table-column>
        <el-table-column prop="visit_count" label="访问次数" width="150"></el-table-column>
        <el-table-column prop="device_info" label="设备信息"></el-table-column>
        <el-table-column prop="last_access_time" label="最后访问" width="180"></el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logsAPI } from '@/api/logs'

const accessLogs = ref([])
const topIPs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterIP = ref('')
const filterEndpoint = ref('')

const stats = ref({
  total_visits: 0,
  unique_ips: 0
})

const loadAccessLogs = async () => {
  loading.value = true
  try {
    const [logsResponse, statsData, ipsData] = await Promise.all([
      logsAPI.getAccessLogs(currentPage.value, pageSize.value, filterIP.value, filterEndpoint.value),
      logsAPI.getAccessStats(),
      logsAPI.getTopIPs(10)
    ])

    accessLogs.value = logsResponse.data || []
    total.value = logsResponse.total || 0
    stats.value = statsData
    topIPs.value = ipsData.data || []
  } catch (error) {
    console.error('Failed to load access logs:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAccessLogs()
})
</script>

<style scoped lang="scss">
.user-access-logs {
  h1 {
    margin-bottom: 20px;
    color: #333;
  }

  h3 {
    color: #333;
    margin-bottom: 15px;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;

    .stat-card {
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      .stat-label {
        color: #999;
        font-size: 14px;
        margin-bottom: 10px;
      }

      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #667eea;
      }
    }
  }

  .filter-bar {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}
</style>
