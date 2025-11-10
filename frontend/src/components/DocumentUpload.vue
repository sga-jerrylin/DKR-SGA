<template>
  <div class="document-upload">
    <el-upload
      ref="uploadRef"
      class="upload-area"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :file-list="fileList"
      accept=".pdf"
      multiple
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        拖拽 PDF 文件到此处，或 <em>点击选择</em>
      </div>
      <div class="el-upload__text">
        <el-tag type="info" size="small">支持批量上传</el-tag>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          只支持 PDF 文件，Agent 会自动分类并处理文档
        </div>
      </template>
    </el-upload>

    <div v-if="fileList.length > 0" class="upload-actions">
      <el-button type="primary" @click="startUpload" :loading="uploading">
        开始上传 ({{ fileList.length }} 个文件)
      </el-button>
      <el-button @click="clearFiles">清空列表</el-button>
    </div>

    <!-- 批量上传进度对话框 -->
    <el-dialog
      v-model="processingVisible"
      title="批量上传进度"
      :close-on-click-modal="false"
      width="700px"
    >
      <div class="batch-progress">
        <div class="overall-progress">
          <div class="progress-header">
            <span>总体进度</span>
            <span>{{ completedCount }} / {{ totalCount }}</span>
          </div>
          <el-progress
            :percentage="overallProgress"
            :status="overallStatus"
          />
        </div>

        <el-divider />

        <div class="file-list">
          <div
            v-for="(item, index) in uploadItems"
            :key="index"
            class="file-item"
          >
            <div class="file-info">
              <el-icon v-if="item.status === 'success'" color="#67c23a">
                <CircleCheck />
              </el-icon>
              <el-icon v-else-if="item.status === 'uploading'" class="is-loading">
                <Loading />
              </el-icon>
              <el-icon v-else-if="item.status === 'error'" color="#f56c6c">
                <CircleClose />
              </el-icon>
              <el-icon v-else color="#909399">
                <Document />
              </el-icon>

              <span class="filename">{{ item.filename }}</span>

              <el-tag
                v-if="item.status === 'success'"
                type="success"
                size="small"
              >
                {{ item.category }}
              </el-tag>
              <el-tag
                v-else-if="item.status === 'error'"
                type="danger"
                size="small"
              >
                失败
              </el-tag>
              <el-tag
                v-else-if="item.status === 'uploading'"
                type="warning"
                size="small"
              >
                处理中
              </el-tag>
            </div>

            <div v-if="item.error" class="error-message">
              {{ item.error }}
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled,
  CircleCheck,
  CircleClose,
  Loading,
  Document
} from '@element-plus/icons-vue'
import type { UploadInstance, UploadUserFile, UploadFile } from 'element-plus'

const emit = defineEmits<{
  success: [data: any]
}>()

const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadUserFile[]>([])
const processingVisible = ref(false)
const uploading = ref(false)

interface UploadItem {
  filename: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  category?: string
  doc_id?: string
  error?: string
}

const uploadItems = ref<UploadItem[]>([])
const totalCount = computed(() => uploadItems.value.length)
const completedCount = computed(() =>
  uploadItems.value.filter(item => item.status === 'success' || item.status === 'error').length
)
const overallProgress = computed(() =>
  totalCount.value > 0 ? Math.round((completedCount.value / totalCount.value) * 100) : 0
)
const overallStatus = computed<'success' | 'exception' | undefined>(() => {
  if (completedCount.value === 0) return undefined
  if (completedCount.value === totalCount.value) {
    const hasError = uploadItems.value.some(item => item.status === 'error')
    return hasError ? 'exception' : 'success'
  }
  return undefined
})

const handleFileChange = (file: UploadFile, files: UploadFile[]) => {
  // 验证文件类型和大小
  if (file.raw) {
    const isPDF = file.raw.type === 'application/pdf'
    const isLt50M = file.raw.size / 1024 / 1024 < 50

    if (!isPDF) {
      ElMessage.error(`${file.name} 不是 PDF 文件！`)
      files.splice(files.indexOf(file), 1)
      return
    }
    if (!isLt50M) {
      ElMessage.error(`${file.name} 文件大小超过 50MB！`)
      files.splice(files.indexOf(file), 1)
      return
    }
  }

  fileList.value = files
}

const clearFiles = () => {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

const startUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  processingVisible.value = true

  // 初始化上传项
  uploadItems.value = fileList.value.map(file => ({
    filename: file.name,
    status: 'pending'
  }))

  // 准备 FormData
  const formData = new FormData()
  fileList.value.forEach(file => {
    if (file.raw) {
      formData.append('files', file.raw)
    }
  })

  try {
    // 调用批量上传 API
    const response = await fetch(
      import.meta.env.VITE_API_BASE_URL + '/documents/upload/batch',
      {
        method: 'POST',
        body: formData
      }
    )

    if (!response.ok) {
      throw new Error('批量上传失败')
    }

    const result = await response.json()

    // 更新每个文件的状态
    result.results.forEach((fileResult: any, index: number) => {
      uploadItems.value[index].status = fileResult.success ? 'success' : 'error'
      uploadItems.value[index].category = fileResult.category
      uploadItems.value[index].doc_id = fileResult.doc_id
      uploadItems.value[index].error = fileResult.error
    })

    // 显示结果
    if (result.success_count > 0) {
      ElMessage.success(
        `成功上传 ${result.success_count} 个文件${
          result.failed_count > 0 ? `，${result.failed_count} 个失败` : ''
        }`
      )
      emit('success', result)
    } else {
      ElMessage.error('所有文件上传失败')
    }
  } catch (error: any) {
    ElMessage.error('批量上传失败：' + (error.message || '未知错误'))
    uploadItems.value.forEach(item => {
      if (item.status === 'pending' || item.status === 'uploading') {
        item.status = 'error'
        item.error = error.message || '上传失败'
      }
    })
  } finally {
    uploading.value = false

    // 3秒后自动关闭对话框（如果全部成功）
    if (overallStatus.value === 'success') {
      setTimeout(() => {
        processingVisible.value = false
        clearFiles()
      }, 3000)
    }
  }
}
</script>

<style scoped>
.document-upload {
  padding: 20px;
}

.upload-area {
  width: 100%;
}

.upload-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.batch-progress {
  padding: 12px 0;
}

.overall-progress {
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.file-list {
  max-height: 400px;
  overflow-y: auto;
}

.file-item {
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filename {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.error-message {
  margin-top: 4px;
  margin-left: 28px;
  font-size: 12px;
  color: #f56c6c;
}
</style>

