/**
 * API 客户端
 */
import axios, { type AxiosInstance } from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const client: AxiosInstance = axios.create({
  baseURL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
client.interceptors.request.use(
  (config) => {
    // Add auth token if needed
    const token = localStorage.getItem('api_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
client.interceptors.response.use(
  (response) => {
    return response.data as any
  },
  (error) => {
    if (error.response) {
      // Server responded with error
      console.error('API Error:', error.response.data)
      return Promise.reject(error.response.data)
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.request)
      return Promise.reject({ error: 'Network error' })
    } else {
      // Something else happened
      console.error('Error:', error.message)
      return Promise.reject({ error: error.message })
    }
  }
)

export default client

