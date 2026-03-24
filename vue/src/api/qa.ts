import client from './client'

export interface QARecord {
  id: number
  user_id: number
  question: string
  answer?: string
  graph_id?: number
  status: 'pending' | 'completed' | 'error'
  response_time?: number
  error_message?: string
  created_at: string
  updated_at: string
}

export interface QAListResponse {
  total: number
  page: number
  page_size: number
  data: QARecord[]
}

export const qaAPI = {
  // 获取问答列表
  getRecords(page = 1, pageSize = 10, userId?: number, status?: string) {
    return client.get<QAListResponse>('/api/qa/records', {
      params: { page, page_size: pageSize, user_id: userId, status }
    })
  },

  // 创建问答记录
  createRecord(userId: number, question: string, graphId?: number) {
    return client.post<QARecord>('/api/qa/records', {
      user_id: userId,
      question,
      graph_id: graphId
    })
  },

  // 获取单个问答记录
  getRecord(recordId: number) {
    return client.get<QARecord>(`/api/qa/records/${recordId}`)
  },

  // 更新问答记录
  updateRecord(recordId: number, data: Partial<QARecord>) {
    return client.put<QARecord>(`/api/qa/records/${recordId}`, data)
  },

  // 删除问答记录
  deleteRecord(recordId: number) {
    return client.delete(`/api/qa/records/${recordId}`)
  },

  // 获取用户统计
  getUserStats(userId: number) {
    return client.get(`/api/qa/users/${userId}/stats`)
  },

  // 获取最近问答
  getRecentRecords(limit = 10) {
    return client.get<QAListResponse>('/api/qa/recent', {
      params: { limit }
    })
  }
}
