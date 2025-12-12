/**
 * API 接口定义
 */
import client from './client'
import type { Document, QueryRequest, QueryResponse } from '@/types'

export const api = {
  // Health check
  health: () => client.get('/health'),

  // Documents
  documents: {
    list: () => client.get<Document[]>('/documents/'),
    upload: (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return client.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    },
    get: (docId: string) => client.get<Document>(`/documents/${docId}`),
    delete: (docId: string) => client.delete(`/documents/${docId}`)
  },

  // Query
  query: (data: QueryRequest) => client.post<QueryResponse>('/query/', data),

  // Agent
  agent: {
    ask: (query: string, options?: Record<string, any>) =>
      client.post('/agent/ask', { query, options })
  },

  // Categories
  categories: {
    list: () => client.get('/categories')
  }
}

export default api

