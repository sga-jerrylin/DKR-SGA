/**
 * 通用类型定义
 */

// 文档元数据
export interface DocumentMetadata {
  filename: string
  file_size: number
  page_count: number
  upload_time: string
  video_path: string
  video_size: number
  compression_ratio: number
}

// 文档信息
export interface Document {
  doc_id: string
  title: string
  category: string
  file_path?: string
  video_path?: string
  summary_path?: string
  page_count: number
  keywords?: string[]
  upload_time?: string
}

// 查询请求
export interface QueryRequest {
  query: string
  context?: Record<string, any>
  options?: Record<string, any>
}

// Agent 步骤
export interface AgentStep {
  step: number
  action: string
  description: string
  layer?: string
  result?: Record<string, any>
  confidence?: number
}

// 来源引用
export interface SourceReference {
  doc_id: string
  doc_title: string
  page_number: number
  content: string
  relevance_score: number
}

// 执行步骤
export interface ExecutionStep {
  step: number
  type: 'user' | 'tool_call' | 'tool_result' | 'ai_response'
  tool_name?: string
  tool_args?: any
  content?: string
}

// 查询响应
export interface QueryResponse {
  success: boolean
  answer?: string
  execution_steps?: ExecutionStep[]
  processing_time: number
  error?: string
}

// 消息类型
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: SourceReference[]
  agent_steps?: AgentStep[]
}

// 分类信息
export interface Category {
  name: string
  description: string
  document_count: number
}

