import client from './client'

export const dataAPI = {
  // 创建上传批次
  createUpload: (uploadName: string) => {
    return client.post('/api/data/uploads', { upload_name: uploadName })
  },

  // 获取上传历史
  getUploads: (page = 1, pageSize = 10) => {
    return client.get('/api/data/uploads', {
      params: { page, page_size: pageSize }
    })
  },

  // 获取上传详情
  getUploadDetail: (id: number) => {
    return client.get(`/api/data/uploads/${id}`)
  },

  // 上传 entities 文件
  uploadEntities: (uploadId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/api/data/uploads/${uploadId}/entities`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 上传 relationships 文件
  uploadRelationships: (uploadId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/api/data/uploads/${uploadId}/relationships`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 上传 text_units 文件
  uploadTextUnits: (uploadId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/api/data/uploads/${uploadId}/text_units`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 上传 communities 文件
  uploadCommunities: (uploadId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/api/data/uploads/${uploadId}/communities`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 上传 community_reports 文件
  uploadCommunityReports: (uploadId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/api/data/uploads/${uploadId}/community_reports`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 上传 documents 文件
  uploadDocuments: (uploadId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/api/data/uploads/${uploadId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 检查上传状态
  checkUploadStatus: (uploadId: number) => {
    return client.get(`/api/data/uploads/${uploadId}/status`)
  },

  // 删除上传记录
  deleteUpload: (id: number) => {
    return client.delete(`/api/data/uploads/${id}`)
  }
}
