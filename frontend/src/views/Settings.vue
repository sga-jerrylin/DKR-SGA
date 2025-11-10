<template>
  <div class="settings-page">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>模型配置</span>
        </div>
      </template>

      <el-form :model="settings" label-width="150px" label-position="left">
        <!-- 1. 分类智能体 -->
        <div class="agent-section">
          <h3 class="agent-title">1. 分类智能体</h3>
          <el-form-item label="模型选择">
            <el-select v-model="settings.classifier_model" placeholder="选择模型">
              <el-option label="DeepSeek Chat" value="deepseek-chat" />
              <el-option label="Gemini 2.5 Flash" value="google/gemini-2.5-flash-preview-09-2025" />
            </el-select>
          </el-form-item>
        </div>

        <el-divider />

        <!-- 2. 页面总结智能体 -->
        <div class="agent-section">
          <h3 class="agent-title">2. 页面总结智能体</h3>
          <el-form-item label="模型选择">
            <el-select v-model="settings.summary_model" placeholder="选择模型">
              <el-option label="Gemini 2.5 Flash" value="google/gemini-2.5-flash-preview-09-2025" />
              <el-option label="Qwen 3 VL 235B" value="qwen/qwen3-vl-235b-a22b-instruct" />
            </el-select>
          </el-form-item>
        </div>

        <el-divider />

        <!-- 3. DKR 主智能体 -->
        <div class="agent-section">
          <h3 class="agent-title">3. DKR 主智能体</h3>
          <el-form-item label="模型选择">
            <el-select v-model="settings.agent_model" placeholder="选择模型">
              <el-option label="DeepSeek Chat" value="deepseek-chat" />
              <el-option label="Claude Haiku 4.5" value="anthropic/claude-haiku-4.5" />
              <el-option label="GPT-4.1" value="openai/gpt-4.1" />
              <el-option label="Kimi K2 (预留)" value="kimi-k2" disabled />
              <el-option label="MiniMax M2 (预留)" value="minimax-m2" disabled />
            </el-select>
          </el-form-item>
        </div>

        <el-divider />

        <!-- 4. OCR 智能体 -->
        <div class="agent-section">
          <h3 class="agent-title">4. OCR 智能体</h3>
          <el-form-item label="模型选择">
            <el-select v-model="settings.ocr_model" placeholder="选择模型">
              <el-option label="DeepSeek OCR" value="deepseek-ocr" />
              <el-option label="Paddle OCR (预留)" value="paddle-ocr" disabled />
              <el-option label="Gemini Flash (预留)" value="gemini-flash-ocr" disabled />
              <el-option label="Qwen 235B VL (预留)" value="qwen-235b-vl-ocr" disabled />
            </el-select>
          </el-form-item>
        </div>

        <el-divider />

        <!-- Agent 参数配置 -->
        <div class="agent-section">
          <h3 class="agent-title">Agent 参数配置</h3>
          <el-form-item label="Agent 最大迭代次数">
            <el-input-number
              v-model="settings.agent_max_iterations"
              :min="1"
              :max="50"
              :step="1"
            />
          </el-form-item>

          <el-form-item label="置信度阈值">
            <el-slider
              v-model="settings.agent_confidence_threshold"
              :min="0"
              :max="1"
              :step="0.05"
              show-stops
            />
            <span class="threshold-value">{{ settings.agent_confidence_threshold }}</span>
          </el-form-item>
        </div>

        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存配置</el-button>
          <el-button @click="loadSettings">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

interface Settings {
  classifier_model: string      // 分类智能体模型
  summary_model: string          // 页面总结智能体模型
  agent_model: string            // DKR 主智能体模型
  ocr_model: string              // OCR 智能体模型
  agent_max_iterations: number
  agent_confidence_threshold: number
}

const settings = ref<Settings>({
  classifier_model: 'deepseek-chat',
  summary_model: 'google/gemini-2.5-flash-preview-09-2025',
  agent_model: 'deepseek-chat',
  ocr_model: 'deepseek-ocr',
  agent_max_iterations: 10,
  agent_confidence_threshold: 0.9
})

const saving = ref(false)

const loadSettings = async () => {
  try {
    const response = await fetch(import.meta.env.VITE_API_BASE_URL + '/settings/models')
    const data = await response.json()

    if (data.success && data.settings) {
      settings.value = {
        ...settings.value,
        ...data.settings
      }
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载配置失败')
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const response = await fetch(
      import.meta.env.VITE_API_BASE_URL + '/settings/models',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings.value)
      }
    )

    const data = await response.json()

    if (data.success) {
      ElMessage.success(data.message || '配置保存成功')
    } else {
      throw new Error(data.error || '保存失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '保存配置失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  padding: 24px;
  max-width: 900px;
}

.settings-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.agent-section {
  margin-bottom: 16px;
}

.agent-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.threshold-value {
  margin-left: 12px;
  color: #606266;
  font-weight: 500;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-divider) {
  margin: 24px 0;
}
</style>

