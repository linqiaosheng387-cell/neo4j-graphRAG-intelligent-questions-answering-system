import client from './client'

export const logsAPI = {
  // 获取系统日志
  getSystemLogs: (page = 1, pageSize = 10, level = '', module = '') => {
    return client.get('/api/logs/system', {
      params: { page, page_size: pageSize, log_level: level, module }
    })
  },

  // 获取用户访问日志
  getAccessLogs: (page = 1, pageSize = 10, ipAddress = '', endpoint = '') => {
    return client.get('/api/logs/access', {
      params: { page, page_size: pageSize, ip_address: ipAddress, endpoint }
    })
  },

  // 获取访问统计
  getAccessStats: () => {
    return client.get('/api/logs/access/stats')
  },

  // 获取热门 IP
  getTopIPs: (limit = 10) => {
    return client.get('/api/logs/access/top-ips', {
      params: { limit }
    })
  },

  // 获取 IP 统计
  getIPStats: (ipAddress: string) => {
    return client.get(`/api/logs/access/ip-stats/${ipAddress}`)
  },

  // 清空日志
  clearLogs: (type: 'system' | 'access') => {
    return client.delete(`/api/logs/${type}`)
  }
}
