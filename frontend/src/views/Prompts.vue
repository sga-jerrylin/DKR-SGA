<template>
  <div class="prompts-page">
    <el-card class="prompts-card">
      <template #header>
        <div class="card-header">
          <span>提示词管理</span>
          <el-button type="primary" size="small" @click="savePrompts" :loading="saving">
            保存所有提示词
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activePrompt" type="border-card" v-loading="loading">
        <el-tab-pane label="Agent System Prompt" name="agent_system">
          <div class="prompt-editor">
            <div class="editor-header">
              <span class="file-path">backend/prompts/agent_system_prompt.txt</span>
              <el-button size="small" @click="resetPrompt('agent_system_prompt')">重置</el-button>
            </div>
            <el-input
              v-model="prompts.agent_system_prompt"
              type="textarea"
              :rows="20"
              placeholder="Agent 系统提示词..."
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="Summary Generation Prompt" name="summary_generation">
          <div class="prompt-editor">
            <div class="editor-header">
              <span class="file-path">backend/prompts/summary_generation_prompt.txt</span>
              <el-button size="small" @click="resetPrompt('summary_generation_prompt')">重置</el-button>
            </div>
            <el-input
              v-model="prompts.summary_generation_prompt"
              type="textarea"
              :rows="20"
              placeholder="Summary 生成提示词..."
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="Classifier System Prompt" name="classifier_system">
          <div class="prompt-editor">
            <div class="editor-header">
              <span class="file-path">backend/prompts/classifier_system_prompt.txt</span>
              <el-button size="small" @click="resetPrompt('classifier_system_prompt')">重置</el-button>
            </div>
            <el-input
              v-model="prompts.classifier_system_prompt"
              type="textarea"
              :rows="20"
              placeholder="分类器系统提示词..."
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

interface Prompts {
  agent_system_prompt: string
  summary_generation_prompt: string
  classifier_system_prompt: string
}

const activePrompt = ref('agent_system')
const saving = ref(false)
const loading = ref(false)

const prompts = ref<Prompts>({
  agent_system_prompt: '',
  summary_generation_prompt: '',
  classifier_system_prompt: ''
})

// 原始提示词（用于重置）
const originalPrompts = ref<Prompts>({
  agent_system_prompt: '',
  summary_generation_prompt: '',
  classifier_system_prompt: ''
})

const loadPrompts = async () => {
  loading.value = true
  try {
    const response = await fetch(import.meta.env.VITE_API_BASE_URL + '/settings/prompts')
    const data = await response.json()

    if (data.success && data.prompts) {
      prompts.value = {
        agent_system_prompt: data.prompts.agent_system_prompt || '',
        summary_generation_prompt: data.prompts.summary_generation_prompt || '',
        classifier_system_prompt: data.prompts.classifier_system_prompt || ''
      }
      // 保存原始值
      originalPrompts.value = { ...prompts.value }
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载提示词失败')
  } finally {
    loading.value = false
  }
}

const savePrompts = async () => {
  saving.value = true
  try {
    // 保存所有提示词
    const savePromises = Object.entries(prompts.value).map(async ([key, content]) => {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/settings/prompts/${key}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content })
        }
      )

      const data = await response.json()
      if (!data.success) {
        throw new Error(data.error || `保存 ${key} 失败`)
      }
      return data
    })

    await Promise.all(savePromises)

    ElMessage.success('所有提示词保存成功')
    // 更新原始值
    originalPrompts.value = { ...prompts.value }
  } catch (error: any) {
    ElMessage.error(error.message || '保存提示词失败')
  } finally {
    saving.value = false
  }
}

const resetPrompt = (promptName: keyof Prompts) => {
  prompts.value[promptName] = originalPrompts.value[promptName]
  ElMessage.success(`已重置 ${promptName}`)
}

onMounted(() => {
  loadPrompts()
})
</script>

<style scoped>
.prompts-page {
  padding: 24px;
  height: 100%;
}

.prompts-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  height: calc(100vh - 108px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
}

.prompt-editor {
  padding: 16px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.file-path {
  font-size: 13px;
  color: #909399;
  font-family: 'Courier New', monospace;
}

.prompt-editor :deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}
</style>

