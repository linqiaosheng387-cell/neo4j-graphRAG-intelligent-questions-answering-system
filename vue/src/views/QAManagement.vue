<template>
  <div class="qa-management">
    <div class="page-header">
      <h1 class="text-h2">问答管理</h1>
      <p class="text-secondary">管理系统中的所有问答记录</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-bar">
      <el-input
        v-model="searchQuestion"
        placeholder="搜索问题..."
        style="width: 300px"
        clearable
      ></el-input>

      <el-select v-model="filterStatus" placeholder="筛选状态" style="width: 150px; margin-left: 10px">
        <el-option label="全部" value=""></el-option>
        <el-option label="待处理" value="pending"></el-option>
        <el-option label="已完成" value="completed"></el-option>
        <el-option label="错误" value="error"></el-option>
      </el-select>

      <el-button type="primary" @click="loadQARecords" style="margin-left: 10px">
        <i class="el-icon-search"></i> 搜索
      </el-button>

      <el-button @click="showCreateDialog = true" style="margin-left: 10px">
        <i class="el-icon-plus"></i> 新建问答
      </el-button>
    </div>

    <!-- 问答列表 -->
    <el-table
      :data="qaRecords"
      style="width: 100%; margin-top: 20px"
      v-loading="loading"
      stripe
      border
    >
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="question" label="问题" show-overflow-tooltip></el-table-column>
      <el-table-column prop="answer" label="答案" show-overflow-tooltip width="200"></el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag
            :type="row.status === 'completed' ? 'success' : row.status === 'error' ? 'danger' : 'info'"
          >
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="response_time" label="响应时间(ms)" width="120"></el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
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
      @change="loadQARecords"
    ></el-pagination>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建问答记录" width="600px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="用户ID">
          <el-input v-model.number="formData.user_id" type="number"></el-input>
        </el-form-item>
        <el-form-item label="问题">
          <el-input v-model="formData.question" type="textarea" rows="3"></el-input>
        </el-form-item>
        <el-form-item label="答案">
          <el-input v-model="formData.answer" type="textarea" rows="3"></el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="formData.status">
            <el-option label="待处理" value="pending"></el-option>
            <el-option label="已完成" value="completed"></el-option>
            <el-option label="错误" value="error"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { qaAPI } from '@/api/qa'

const qaRecords = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchQuestion = ref('')
const filterStatus = ref('')
const showCreateDialog = ref(false)
const editingId = ref<number | null>(null)

const formData = ref({
  question: '',
  answer: '',
  status: 'pending',
  user_id: 1,
  graph_id: 1
})

const loadQARecords = async () => {
  loading.value = true
  try {
    const response = await qaAPI.getRecords(
      currentPage.value,
      pageSize.value,
      undefined,
      filterStatus.value
    )
    qaRecords.value = response.data || []
    total.value = response.total || 0
  } catch (error) {
    ElMessage.error('加载问答列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleEdit = (row: any) => {
  editingId.value = row.id
  formData.value = { ...row }
  showCreateDialog.value = true
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除该问答记录吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await qaAPI.deleteRecord(id)
    ElMessage.success('删除成功')
    loadQARecords()
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

const handleSave = async () => {
  try {
    if (editingId.value) {
      await qaAPI.updateRecord(editingId.value, formData.value)
    } else {
      await qaAPI.createRecord(formData.value.user_id, formData.value.question, formData.value.graph_id)
    }
    ElMessage.success('保存成功')
    showCreateDialog.value = false
    editingId.value = null
    loadQARecords()
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  }
}

// 格式化时间，转换为本地时区（UTC+8）
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  
  try {
    // 如果时间字符串不包含 'Z' 或 '+' 或 '-'，说明是本地时间，直接格式化
    let date: Date
    if (timeStr.includes('Z') || timeStr.includes('+') || (timeStr.match(/-/g) || []).length > 2) {
      // UTC 时间，需要转换
      date = new Date(timeStr)
      // 转换为 UTC+8
      date = new Date(date.getTime() + 8 * 60 * 60 * 1000)
    } else {
      // 已经是本地时间
      date = new Date(timeStr)
    }
    
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch (error) {
    return timeStr
  }
}

onMounted(() => {
  loadQARecords()
})
</script>

<style scoped lang="scss">
.qa-management {
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
}
</style>
