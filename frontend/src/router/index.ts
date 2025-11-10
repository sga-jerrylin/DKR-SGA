import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: 'DKR - 智能检索' }
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('@/views/Documents.vue'),
    meta: { title: 'DKR - 文档管理' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: 'DKR - 系统设置' }
  },
  {
    path: '/prompts',
    name: 'Prompts',
    component: () => import('@/views/Prompts.vue'),
    meta: { title: 'DKR - 提示词管理' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = (to.meta.title as string) || 'DKR 1.0'
  next()
})

export default router

