<template>
  <div class="document-list">
    <div class="list-header">
      <el-input
        v-model="searchText"
        placeholder="搜索文档..."
        clearable
        style="width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select v-model="selectedCategory" placeholder="选择分类" clearable style="width: 200px">
        <el-option label="全部分类" value="" />
        <el-option
          v-for="category in categories"
          :key="category"
          :label="category"
          :value="category"
        />
      </el-select>
    </div>

    <el-table
      v-loading="loading"
      :data="filteredDocuments"
      style="width: 100%; margin-top: 16px"
      stripe
    >
      <el-table-column prop="title" label="文档标题" min-width="200" />
      <el-table-column prop="category" label="分类" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="page_count" label="页数" width="100" />
      <el-table-column prop="upload_time" label="上传时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.upload_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" link @click="viewDocument(row)">
            查看
          </el-button>
          <el-button type="danger" size="small" link @click="deleteDocument(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { api } from '@/api'

interface Document {
  doc_id: string
  title: string
  category: string
  page_count: number
  upload_time: string
}

const documents = ref<Document[]>([])
const loading = ref(false)
const searchText = ref('')
const selectedCategory = ref('')

const categories = computed(() => {
  const cats = new Set(documents.value.map(d => d.category))
  return Array.from(cats)
})

const filteredDocuments = computed(() => {
  let result = documents.value

  if (selectedCategory.value) {
    result = result.filter(d => d.category === selectedCategory.value)
  }

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(d => d.title.toLowerCase().includes(search))
  }

  return result
})

const loadDocuments = async () => {
  loading.value = true
  try {
    const response = await api.documents.list()
    documents.value = response as any
  } catch (error: any) {
    ElMessage.error('加载文档列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

const viewDocument = (_doc: Document) => {
  ElMessage.info('文档查看功能开发中...')
}

const deleteDocument = async (doc: Document) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${doc.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.documents.delete(doc.doc_id)
    ElMessage.success('文档已删除')
    await loadDocuments()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error.message)
    }
  }
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadDocuments()
})

defineExpose({
  loadDocuments
})
</script>

<style scoped>
.document-list {
  padding: 20px;
}

.list-header {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>

