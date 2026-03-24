<template>
  <div class="data-management">
    <h1>数据管理</h1>

    <!-- 上传区域 -->
    <div class="upload-section">
      <h3>上传结构化数据</h3>
      <p class="tips">需要上传以下6个parquet文件：entities、relationships、text_units、communities、community_reports、documents</p>

      <div class="upload-grid">
        <div class="upload-item" v-for="file in requiredFiles" :key="file.name">
          <div class="upload-box">
            <i class="el-icon-upload"></i>
            <p>{{ file.label }}</p>
            <el-upload
              :auto-upload="false"
              :on-change="(file) => handleFileSelect(file, file.name)"
              accept=".parquet"
              drag
            >
              <template #default>
                <p class="el-upload__text">拖拽文件到此或<em>点击上传</em></p>
              </template>
            </el-upload>
          </div>
          <div class="file-status" v-if="uploadedFiles[file.name]">
            <i class="el-icon-success"></i> {{ uploadedFiles[file.name].name }}
          </div>
        </div>
      </div>

      <div class="upload-actions">
        <el-button type="primary" @click="handleUpload" :loading="uploading">
          <i class="el-icon-upload"></i> 上传所有文件
        </el-button>
        <el-button @click="resetUpload">重置</el-button>
      </div>
    </div>

    <!-- 上传历史 -->
    <div class="history-section" style="margin-top: 40px">
      <h3>上传历史</h3>

      <el-table
        :data="uploadHistory"
        style="width: 100%; margin-top: 20px"
        v-loading="loading"
        stripe
        border
      >
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="upload_name" label="上传名称"></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180"></el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetails(row)">详情</el-button>
            <el-button link type="danger" @click="handleDeleteUpload(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailsDialog" title="上传详情" width="700px">
      <div v-if="currentUpload" class="details-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="上传ID">{{ currentUpload.id }}</el-descriptions-item>
          <el-descriptions-item label="上传名称">{{ currentUpload.upload_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentUpload.status === 'completed' ? 'success' : 'danger'">
              {{ currentUpload.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentUpload.created_at }}</el-descriptions-item>
          <el-descriptions-item label="文件状态">
            <div class="file-checklist">
              <div v-for="file in requiredFiles" :key="file.name" class="file-item">
                <i :class="currentUpload[file.key] ? 'el-icon-success' : 'el-icon-close'"></i>
                {{ file.label }}
              </div>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dataAPI } from '@/api/data'

const requiredFiles = [
  { name: 'entities', label: 'entities.parquet', key: 'entities_file' },
  { name: 'relationships', label: 'relationships.parquet', key: 'relationships_file' },
  { name: 'text_units', label: 'text_units.parquet', key: 'text_units_file' },
  { name: 'communities', label: 'communities.parquet', key: 'communities_file' },
  { name: 'community_reports', label: 'community_reports.parquet', key: 'community_reports_file' },
  { name: 'documents', label: 'documents.parquet', key: 'documents_file' }
]

const uploadedFiles = ref<Record<string, any>>({})
const uploading = ref(false)
const loading = ref(false)
const uploadHistory = ref([])
const showDetailsDialog = ref(false)
const currentUpload = ref<any>(null)

const handleFileSelect = (file: any, fileName: string) => {
  uploadedFiles.value[fileName] = file.raw
  ElMessage.success(`${fileName} 已选择`)
}

const handleUpload = async () => {
  const uploadedCount = Object.keys(uploadedFiles.value).length
  if (uploadedCount === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  try {
    // 创建上传批次
    const uploadResponse = await dataAPI.createUpload(`Upload-${Date.now()}`)
    const uploadId = uploadResponse.id

    // 上传各个文件
    const uploadPromises = []
    if (uploadedFiles.value['entities']) {
      uploadPromises.push(dataAPI.uploadEntities(uploadId, uploadedFiles.value['entities']))
    }
    if (uploadedFiles.value['relationships']) {
      uploadPromises.push(dataAPI.uploadRelationships(uploadId, uploadedFiles.value['relationships']))
    }
    if (uploadedFiles.value['text_units']) {
      uploadPromises.push(dataAPI.uploadTextUnits(uploadId, uploadedFiles.value['text_units']))
    }
    if (uploadedFiles.value['communities']) {
      uploadPromises.push(dataAPI.uploadCommunities(uploadId, uploadedFiles.value['communities']))
    }
    if (uploadedFiles.value['community_reports']) {
      uploadPromises.push(dataAPI.uploadCommunityReports(uploadId, uploadedFiles.value['community_reports']))
    }
    if (uploadedFiles.value['documents']) {
      uploadPromises.push(dataAPI.uploadDocuments(uploadId, uploadedFiles.value['documents']))
    }

    await Promise.all(uploadPromises)
    ElMessage.success('文件上传成功')
    resetUpload()
    // 刷新上传历史
    const response = await dataAPI.getUploads()
    uploadHistory.value = response.data || []
  } catch (error) {
    ElMessage.error('文件上传失败')
    console.error(error)
  } finally {
    uploading.value = false
  }
}

const resetUpload = () => {
  uploadedFiles.value = {}
}

const handleViewDetails = (row: any) => {
  currentUpload.value = row
  showDetailsDialog.value = true
}

const handleDeleteUpload = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除该上传记录吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    ElMessage.success('删除成功')
  } catch (error) {
    console.error(error)
  }
}
</script>

<style scoped lang="scss">
.data-management {
  h1 {
    margin-bottom: 20px;
    color: #333;
  }

  .upload-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

    h3 {
      margin: 0 0 10px 0;
      color: #333;
    }

    .tips {
      color: #999;
      font-size: 14px;
      margin: 0 0 20px 0;
    }

    .upload-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin-bottom: 20px;

      .upload-item {
        .upload-box {
          border: 2px dashed #667eea;
          border-radius: 8px;
          padding: 20px;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s;

          &:hover {
            border-color: #764ba2;
            background: rgba(102, 126, 234, 0.05);
          }

          i {
            font-size: 32px;
            color: #667eea;
            display: block;
            margin-bottom: 10px;
          }

          p {
            margin: 0;
            color: #333;
            font-weight: 500;
          }
        }

        .file-status {
          margin-top: 10px;
          color: #67c23a;
          font-size: 14px;

          i {
            margin-right: 5px;
          }
        }
      }
    }

    .upload-actions {
      display: flex;
      gap: 10px;
    }
  }

  .history-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

    h3 {
      margin: 0 0 20px 0;
      color: #333;
    }
  }

  .details-content {
    .file-checklist {
      .file-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;

        i {
          font-size: 18px;

          &.el-icon-success {
            color: #67c23a;
          }

          &.el-icon-close {
            color: #f56c6c;
          }
        }
      }
    }
  }
}
</style>
