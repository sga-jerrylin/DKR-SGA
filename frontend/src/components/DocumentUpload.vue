<template>
  <div class="document-upload">
    <el-upload
      ref="uploadRef"
      class="upload-area"
      drag
      :action="uploadAction"
      :before-upload="beforeUpload"
      :on-success="handleSuccess"
      :on-error="handleError"
      :show-file-list="false"
      accept=".pdf"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        拖拽 PDF 文件到此处，或 <em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          只支持 PDF 文件，Agent 会自动分类并处理文档
        </div>
      </template>
    </el-upload>

    <el-dialog v-model="processingVisible" title="文档处理中" :close-on-click-modal="false" width="500px">
      <div class="processing-content">
        <el-progress :percentage="progress" :status="progressStatus" />
        <div class="processing-steps">
          <div v-for="(step, index) in processingSteps" :key="index" class="step">
            <el-icon v-if="step.status === 'success'" color="#67c23a"><CircleCheck /></el-icon>
            <el-icon v-else-if="step.status === 'loading'" class="is-loading"><Loading /></el-icon>
            <el-icon v-else color="#909399"><CircleClose /></el-icon>
            <span>{{ step.text }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, CircleCheck, CircleClose, Loading } from '@element-plus/icons-vue'
import type { UploadInstance } from 'element-plus'

const emit = defineEmits<{
  success: [data: any]
}>()

const uploadRef = ref<UploadInstance>()
const processingVisible = ref(false)
const progress = ref(0)
const progressStatus = ref<'success' | 'exception' | undefined>()

interface ProcessingStep {
  text: string
  status: 'pending' | 'loading' | 'success' | 'error'
}

const processingSteps = ref<ProcessingStep[]>([
  { text: '上传 PDF 文件', status: 'pending' },
  { text: '转换为视频格式 (H.265)', status: 'pending' },
  { text: '生成文档摘要', status: 'pending' },
  { text: 'LLM 自动分类', status: 'pending' },
  { text: '添加到文档库', status: 'pending' }
])

const uploadAction = import.meta.env.VITE_API_BASE_URL + '/documents/upload'

const beforeUpload = (file: File) => {
  const isPDF = file.type === 'application/pdf'
  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isPDF) {
    ElMessage.error('只能上传 PDF 文件！')
    return false
  }
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB！')
    return false
  }

  processingVisible.value = true
  progress.value = 0
  progressStatus.value = undefined
  
  processingSteps.value.forEach(step => {
    step.status = 'pending'
  })

  simulateProgress()

  return true
}

const simulateProgress = () => {
  const steps = processingSteps.value
  let currentStep = 0

  const interval = setInterval(() => {
    if (currentStep < steps.length) {
      if (currentStep > 0) {
        steps[currentStep - 1].status = 'success'
      }
      steps[currentStep].status = 'loading'
      progress.value = ((currentStep + 1) / steps.length) * 100
      currentStep++
    } else {
      clearInterval(interval)
    }
  }, 2000)
}

const handleSuccess = (response: any) => {
  processingSteps.value.forEach(step => {
    step.status = 'success'
  })
  progress.value = 100
  progressStatus.value = 'success'

  setTimeout(() => {
    processingVisible.value = false
    ElMessage.success(response.message || '文档上传成功！')
    emit('success', response)
  }, 1000)
}

const handleError = (error: any) => {
  const currentStep = processingSteps.value.findIndex(s => s.status === 'loading')
  if (currentStep >= 0) {
    processingSteps.value[currentStep].status = 'error'
  }
  progressStatus.value = 'exception'
  
  ElMessage.error('文档上传失败：' + (error.message || '未知错误'))
  
  setTimeout(() => {
    processingVisible.value = false
  }, 2000)
}
</script>

<style scoped>
.document-upload {
  padding: 20px;
}

.upload-area {
  width: 100%;
}

.processing-content {
  padding: 20px 0;
}

.processing-steps {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}
</style>

