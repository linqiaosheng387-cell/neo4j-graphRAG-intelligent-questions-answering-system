import client from './client'

export const graphAPI = {
  // 获取图谱列表
  getGraphs: (page = 1, pageSize = 10, search = '') => {
    return client.get('/api/graphs', {
      params: { page, page_size: pageSize, search }
    })
  },

  // 获取图谱详情
  getGraphDetail: (id: number) => {
    return client.get(`/api/graphs/${id}`)
  },

  // 创建图谱
  createGraph: (data: {
    name: string
    description: string
    neo4j_db_name: string
    status: string
  }) => {
    return client.post('/api/graphs', data)
  },

  // 更新图谱
  updateGraph: (id: number, data: any) => {
    return client.put(`/api/graphs/${id}`, data)
  },

  // 删除图谱
  deleteGraph: (id: number) => {
    return client.delete(`/api/graphs/${id}`)
  },

  // 获取图谱统计
  getGraphStats: () => {
    return client.get('/api/graphs/stats/overview')
  }
}
