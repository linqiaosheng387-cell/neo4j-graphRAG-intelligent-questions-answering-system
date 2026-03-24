<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="text-h2">数据面板</h1>
      <p class="text-secondary">实时监控系统运行状态</p>
    </div>

    <!-- 统计卡片网格 -->
    <div class="stats-grid">
      <StatCard
        label="总用户数"
        :value="overview.total_users"
        icon-bg="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
      >
        <template #icon>👥</template>
      </StatCard>

      <StatCard
        label="总问答数"
        :value="overview.total_qa"
        :trend="12"
        icon-bg="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
      >
        <template #icon>💬</template>
      </StatCard>

      <StatCard
        label="知识图谱"
        :value="overview.total_graphs"
        icon-bg="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
      >
        <template #icon>🔗</template>
      </StatCard>

      <StatCard
        label="访问次数"
        :value="overview.total_visits"
        :trend="8"
        icon-bg="linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
      >
        <template #icon>📊</template>
      </StatCard>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <Card elevated>
        <template #header>
          <h3 class="text-h4">访问趋势</h3>
          <p class="text-caption text-tertiary">最近7天的访问和问答数据</p>
        </template>
        <div ref="visitTrendChart" style="height: 300px"></div>
      </Card>

      <Card elevated>
        <template #header>
          <h3 class="text-h4">时间段统计</h3>
          <p class="text-caption text-tertiary">不同时间段的访问和问答对比</p>
        </template>
        <div ref="timePeriodChart" style="height: 300px"></div>
      </Card>
    </div>

    <!-- 数据表格 -->
    <div class="tables-section">
      <Card>
        <template #header>
          <h3 class="text-h4">热门IP排名</h3>
        </template>
        <Table :columns="ipColumns" :data="topIPs" :loading="loading">
          <template #cell-visit_count="{ value }">
            <span class="number-value">{{ value }}</span>
          </template>
        </Table>
      </Card>

      <Card>
        <template #header>
          <h3 class="text-h4">最近问题</h3>
        </template>
        <Table :columns="questionColumns" :data="recentQuestions" :loading="loading">
          <template #cell-created_at="{ value }">
            <span class="text-caption">{{ formatDate(value) }}</span>
          </template>
        </Table>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dashboardAPI } from '@/api/dashboard'
import StatCard from '@/components/common/StatCard.vue'
import Card from '@/components/common/Card.vue'
import Table from '@/components/common/Table.vue'
import * as echarts from 'echarts'

const overview = ref({
  total_users: 0,
  total_qa: 0,
  completed_qa: 0,
  total_graphs: 0,
  active_graphs: 0,
  total_visits: 0,
  unique_ips: 0
})

const topIPs = ref([])
const recentQuestions = ref([])
const loading = ref(false)
const visitTrendChart = ref<HTMLElement>()
const timePeriodChart = ref<HTMLElement>()

const ipColumns = [
  { key: 'ip_address', label: 'IP地址', width: '150px' },
  { key: 'visit_count', label: '访问次数', width: '100px', type: 'number' },
  { key: 'device_info', label: '设备信息' }
]

const questionColumns = [
  { key: 'question', label: '问题内容' },
  { key: 'username', label: '用户', width: '100px' },
  { key: 'created_at', label: '时间', width: '150px', type: 'date' }
]

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const loadDashboardData = async () => {
  loading.value = true
  try {
    const [overviewData, ipsData, questionsData, trendData, periodData] = await Promise.all([
      dashboardAPI.getOverview(),
      dashboardAPI.getTopIPs(10),
      dashboardAPI.getRecentQuestions(20),
      dashboardAPI.getVisitTrend(),
      dashboardAPI.getTimePeriodStats()
    ])

    overview.value = overviewData
    topIPs.value = ipsData.data || []
    recentQuestions.value = questionsData.data || []

    initVisitTrendChart(trendData.trend)
    initTimePeriodChart(periodData.data)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const initVisitTrendChart = (data: any[]) => {
  if (!visitTrendChart.value) return

  const chart = echarts.init(visitTrendChart.value)
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '60px', right: '20px', top: '20px', bottom: '40px' },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: isDark ? '#434343' : '#d9d9d9' } }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: isDark ? '#434343' : '#d9d9d9' } }
    },
    series: [
      {
        name: '访问次数',
        data: data.map(d => d.visits),
        type: 'line',
        smooth: true,
        itemStyle: { color: '#667eea' },
        areaStyle: { color: 'rgba(102, 126, 234, 0.1)' }
      },
      {
        name: '问答数',
        data: data.map(d => d.qa_count),
        type: 'line',
        smooth: true,
        itemStyle: { color: '#f5576c' },
        areaStyle: { color: 'rgba(245, 87, 108, 0.1)' }
      }
    ]
  }
  chart.setOption(option)
}

const initTimePeriodChart = (data: any) => {
  if (!timePeriodChart.value) return

  const chart = echarts.init(timePeriodChart.value)
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'

  // 获取最新的数据（最后一条日期的数据）
  let todayData: any[] = []
  
  if (data && typeof data === 'object') {
    // 如果 data 是对象，获取最后一个日期的数据
    const dates = Object.keys(data).sort().reverse()
    if (dates.length > 0) {
      todayData = data[dates[0]] || []
    }
  } else if (Array.isArray(data)) {
    // 如果 data 是数组，直接使用
    todayData = data
  }

  // 确保有 4 个时间段的数据（如果缺少则补充）
  const defaultPeriods = [
    { period: '00-06', period_label: '00:00-05:59', visit_count: 0, qa_count: 0 },
    { period: '06-12', period_label: '06:00-11:59', visit_count: 0, qa_count: 0 },
    { period: '12-18', period_label: '12:00-17:59', visit_count: 0, qa_count: 0 },
    { period: '18-24', period_label: '18:00-23:59', visit_count: 0, qa_count: 0 }
  ]

  // 合并数据，使用返回的数据覆盖默认值
  const periodMap = new Map()
  defaultPeriods.forEach(p => periodMap.set(p.period, p))
  
  if (Array.isArray(todayData)) {
    todayData.forEach((p: any) => {
      if (p.period) {
        periodMap.set(p.period, {
          period: p.period,
          period_label: p.period_label || '',
          visit_count: p.visit_count || 0,
          qa_count: p.qa_count || 0
        })
      }
    })
  }

  const periods = Array.from(periodMap.values())
  const labels = periods.map((p: any) => p.period_label || '')
  const visits = periods.map((p: any) => p.visit_count || 0)
  const qas = periods.map((p: any) => p.qa_count || 0)

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '60px', right: '20px', top: '20px', bottom: '40px' },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: isDark ? '#434343' : '#d9d9d9' } }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: isDark ? '#434343' : '#d9d9d9' } }
    },
    series: [
      {
        name: '访问数',
        data: visits,
        type: 'bar',
        itemStyle: { color: '#4A90E2' }
      },
      {
        name: '问答数',
        data: qas,
        type: 'bar',
        itemStyle: { color: '#E74C3C' }
      }
    ]
  }
  chart.setOption(option)
}

onMounted(() => {
  loadDashboardData()
  setInterval(loadDashboardData, 30000)
})
</script>

<style scoped lang="scss">
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  margin-bottom: 8px;

  h1 {
    margin-bottom: 4px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
}

.tables-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
}

// 响应式
@media (max-width: 1024px) {
  .charts-section,
  .tables-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .dashboard {
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
