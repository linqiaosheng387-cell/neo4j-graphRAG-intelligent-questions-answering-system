import client from './client'

export const dashboardAPI = {
  // 获取总体统计
  getOverview() {
    return client.get('/api/dashboard/overview')
  },

  // 获取今日统计
  getTodayStats() {
    return client.get('/api/dashboard/today-stats')
  },

  // 获取访问趋势
  getVisitTrend() {
    return client.get('/api/dashboard/visit-trend')
  },

  // 获取热门IP
  getTopIPs(limit = 10) {
    return client.get('/api/dashboard/top-ips', {
      params: { limit }
    })
  },

  // 获取最近问题
  getRecentQuestions(limit = 20) {
    return client.get('/api/dashboard/recent-questions', {
      params: { limit }
    })
  },

  // 获取问答完成率
  getQACompletionRate() {
    return client.get('/api/dashboard/qa-completion-rate')
  },

  // 获取平均响应时间
  getAvgResponseTime() {
    return client.get('/api/dashboard/avg-response-time')
  },

  // 获取用户活跃度
  getUserActivity(limit = 10) {
    return client.get('/api/dashboard/user-activity', {
      params: { limit }
    })
  },

  // 获取图谱使用统计
  getGraphUsage() {
    return client.get('/api/dashboard/graph-usage')
  },

  // 获取地域分布
  getGeoDistribution(limit = 10) {
    return client.get('/api/dashboard/geo-distribution', {
      params: { limit }
    })
  },

  // 获取时间段统计
  getTimePeriodStats(days = 7) {
    return client.get('/api/dashboard/time-period-stats', {
      params: { days }
    })
  }
}
