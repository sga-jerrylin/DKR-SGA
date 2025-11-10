<template>
  <div class="chat-interface">
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" :class="['message', message.role]">
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(message.content)"></div>

          <!-- Agent 执行步骤 -->
          <div v-if="message.execution_steps && message.execution_steps.length > 0" class="agent-steps">
            <el-collapse>
              <el-collapse-item :name="index">
                <template #title>
                  <div class="collapse-title">
                    <el-icon><Operation /></el-icon>
                    <span>查看 Agent 执行步骤 ({{ message.execution_steps.length }} 步)</span>
                  </div>
                </template>

                <el-timeline>
                  <el-timeline-item
                    v-for="(step, idx) in message.execution_steps"
                    :key="idx"
                    :timestamp="`步骤 ${step.step}`"
                    placement="top"
                  >
                    <el-card class="step-card">
                      <!-- 工具调用 -->
                      <div v-if="step.type === 'tool_call'" class="step-content">
                        <div class="step-header">
                          <el-tag type="primary" size="small">
                            <el-icon><Tools /></el-icon>
                            调用工具
                          </el-tag>
                          <span class="tool-name">{{ step.tool_name }}</span>
                        </div>
                        <div class="step-body">
                          <pre class="tool-args">{{ JSON.stringify(step.tool_args, null, 2) }}</pre>
                        </div>
                      </div>

                      <!-- 工具返回 -->
                      <div v-else-if="step.type === 'tool_result'" class="step-content">
                        <div class="step-header">
                          <el-tag type="success" size="small">
                            <el-icon><Check /></el-icon>
                            工具返回
                          </el-tag>
                          <span class="tool-name">{{ step.tool_name }}</span>
                        </div>
                        <div class="step-body">
                          <div class="tool-result">{{ step.content }}</div>
                        </div>
                      </div>

                      <!-- AI 回答 -->
                      <div v-else-if="step.type === 'ai_response'" class="step-content">
                        <div class="step-header">
                          <el-tag type="warning" size="small">
                            <el-icon><ChatDotRound /></el-icon>
                            AI 回答
                          </el-tag>
                        </div>
                        <div class="step-body">
                          <div class="ai-response">{{ step.content }}</div>
                        </div>
                      </div>

                      <!-- 用户消息 -->
                      <div v-else-if="step.type === 'user'" class="step-content">
                        <div class="step-header">
                          <el-tag type="info" size="small">
                            <el-icon><User /></el-icon>
                            用户消息
                          </el-tag>
                        </div>
                        <div class="step-body">
                          <div class="user-message">{{ step.content }}</div>
                        </div>
                      </div>
                    </el-card>
                  </el-timeline-item>
                </el-timeline>
              </el-collapse-item>
            </el-collapse>
          </div>

          <div class="message-time">{{ message.time }}</div>
        </div>
      </div>
      <div v-if="loading" class="message assistant loading">
        <div class="message-content">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>Agent 正在思考...</span>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入您的问题，Agent 会自动帮您检索文档..."
        @keydown.enter.ctrl="sendMessage"
        :disabled="loading"
      />
      <el-button type="primary" @click="sendMessage" :loading="loading" :disabled="!inputText.trim()">
        发送 (Ctrl+Enter)
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Loading,
  Operation,
  Tools,
  Check,
  ChatDotRound,
  User
} from '@element-plus/icons-vue'
import { api } from '@/api'

interface ExecutionStep {
  step: number
  type: 'user' | 'tool_call' | 'tool_result' | 'ai_response'
  tool_name?: string
  tool_args?: any
  content?: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  time: string
  execution_steps?: ExecutionStep[]
}

const messages = ref<Message[]>([
  {
    role: 'assistant',
    content: '您好！我是 DKR 智能文档检索助手。请直接用自然语言提问，我会自动帮您在文档库中查找答案。',
    time: new Date().toLocaleTimeString()
  }
])

const inputText = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement>()

const sendMessage = async () => {
  if (!inputText.value.trim() || loading.value) return

  const userMessage: Message = {
    role: 'user',
    content: inputText.value,
    time: new Date().toLocaleTimeString()
  }

  messages.value.push(userMessage)
  const query = inputText.value
  inputText.value = ''

  await nextTick()
  scrollToBottom()

  loading.value = true

  try {
    const response = await api.query({ query }) as any

    const assistantMessage: Message = {
      role: 'assistant',
      content: response.answer || '抱歉，我没有找到相关信息。',
      time: new Date().toLocaleTimeString(),
      execution_steps: response.execution_steps || []
    }

    messages.value.push(assistantMessage)

    await nextTick()
    scrollToBottom()
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败，请重试')
    
    const errorMessage: Message = {
      role: 'assistant',
      content: '抱歉，查询过程中出现了错误，请稍后重试。',
      time: new Date().toLocaleTimeString()
    }
    messages.value.push(errorMessage)
  } finally {
    loading.value = false
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (content: string) => {
  // 简单的 Markdown 格式化（可以后续增强）
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}
</script>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  animation: fadeIn 0.3s;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  text-align: right;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.agent-steps {
  margin-top: 16px;
  font-size: 13px;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.step-card {
  margin-bottom: 8px;
}

.step-content {
  font-size: 13px;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.tool-name {
  font-weight: 500;
  color: #303133;
}

.step-body {
  margin-top: 8px;
}

.tool-args {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  overflow-x: auto;
  margin: 0;
}

.tool-result,
.ai-response,
.user-message {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.loading .message-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.chat-input {
  padding: 16px;
  background: white;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input :deep(.el-textarea__inner) {
  resize: none;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

