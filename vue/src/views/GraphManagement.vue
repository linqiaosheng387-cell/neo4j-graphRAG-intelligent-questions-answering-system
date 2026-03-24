<template>
  <div class="graph-management">
    <h1>图谱管理</h1>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-item">
        <span class="label">总图谱数</span>
        <span class="value">{{ stats.total_graphs }}</span>
      </div>
      <div class="stat-item">
        <span class="label">活跃图谱</span>
        <span class="value">{{ stats.active_graphs }}</span>
      </div>
      <div class="stat-item">
        <span class="label">总实体数</span>
        <span class="value">{{ stats.total_entities }}</span>
      </div>
      <div class="stat-item">
        <span class="label">总关系数</span>
        <span class="value">{{ stats.total_relations }}</span>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar" style="margin-top: 20px">
      <el-input
        v-model="searchName"
        placeholder="搜索图谱名称..."
        style="width: 300px"
        clearable
      ></el-input>
    </div>

    <!-- 图谱列表 -->
    <el-table
      :data="graphs"
      style="width: 100%; margin-top: 20px"
      v-loading="loading"
      stripe
      border
    >
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="name" label="图谱名称"></el-table-column>
      <el-table-column prop="description" label="描述" show-overflow-tooltip></el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="entity_count" label="实体数" width="100"></el-table-column>
      <el-table-column prop="relation_count" label="关系数" width="100"></el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180"></el-table-column>
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
      @change="loadGraphs"
    ></el-pagination>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建知识图谱" width="600px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="图谱名称">
          <el-input v-model="formData.name" placeholder="请输入图谱名称"></el-input>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" rows="3"></el-input>
        </el-form-item>
        <el-form-item label="Neo4j数据库">
          <el-input v-model="formData.neo4j_db_name" placeholder="数据库名"></el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="formData.status">
            <el-option label="活跃" value="active"></el-option>
            <el-option label="非活跃" value="inactive"></el-option>
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
import { graphAPI } from '@/api/graph'

const graphs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchName = ref('')
const showCreateDialog = ref(false)
const editingId = ref<number | null>(null)

const stats = ref({
  total_graphs: 0,
  active_graphs: 0,
  processing_graphs: 0,
  failed_graphs: 0,
  total_entities: 0,
  total_relations: 0
})

const formData = ref({
  name: '',
  description: '',
  neo4j_db_name: '',
  status: 'inactive'
})

const loadGraphs = async () => {
  loading.value = true
  try {
    const response = await graphAPI.getGraphs(
      currentPage.value,
      pageSize.value,
      searchName.value
    )
    graphs.value = response.data || []
    total.value = response.total || 0

    const statsData = await graphAPI.getGraphStats()
    stats.value = statsData
  } catch (error) {
    ElMessage.error('加载图谱失败')
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
    await ElMessageBox.confirm('确定删除该图谱吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await graphAPI.deleteGraph(id)
    ElMessage.success('删除成功')
    loadGraphs()
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

const handleSave = async () => {
  try {
    if (editingId.value) {
      await graphAPI.updateGraph(editingId.value, formData.value)
    } else {
      await graphAPI.createGraph(formData.value)
    }
    ElMessage.success('保存成功')
    showCreateDialog.value = false
    editingId.value = null
    loadGraphs()
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  }
}

onMounted(() => {
  loadGraphs()
})
</script>

<style scoped lang="scss">
.graph-management {
  h1 {
    margin-bottom: 20px;
    color: #333;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;

    .stat-item {
      background: white;
      padding: 15px;
      border-radius: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      .label {
        color: #999;
        font-size: 14px;
      }

      .value {
        font-size: 24px;
        font-weight: bold;
        color: #667eea;
      }
    }
  }

  .action-bar {
    display: flex;
    gap: 10px;
  }
}
</style>
