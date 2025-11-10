<template>
  <el-container id="app">
    <!-- 左侧边栏 -->
    <el-aside :width="sidebarWidth" class="app-sidebar">
      <div class="sidebar-header">
        <h1 class="logo">
          <el-icon><Notebook /></el-icon>
          <span v-if="!isCollapsed">DKR</span>
        </h1>
        <el-button
          v-if="!isCollapsed"
          :icon="Fold"
          circle
          size="small"
          @click="toggleSidebar"
          class="collapse-btn"
        />
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>智能检索</template>
        </el-menu-item>

        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <template #title>文档管理</template>
        </el-menu-item>

        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>

        <el-menu-item index="/prompts">
          <el-icon><EditPen /></el-icon>
          <template #title>提示词管理</template>
        </el-menu-item>
      </el-menu>

      <!-- 折叠按钮（折叠状态） -->
      <div v-if="isCollapsed" class="expand-btn-wrapper">
        <el-button :icon="Expand" circle size="small" @click="toggleSidebar" />
      </div>
    </el-aside>

    <!-- 右侧主内容区 -->
    <el-container class="main-container">
      <el-header class="app-header">
        <div class="header-content">
          <h2 class="page-title">{{ pageTitle }}</h2>
          <div class="header-actions">
            <!-- 可以添加全局操作按钮 -->
          </div>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChatDotRound,
  Document,
  Setting,
  EditPen,
  Notebook,
  Fold,
  Expand
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapsed = ref(false)

const activeMenu = computed(() => route.path)

const sidebarWidth = computed(() => (isCollapsed.value ? '64px' : '200px'))

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/': '智能检索',
    '/documents': '文档管理',
    '/settings': '系统设置',
    '/prompts': '提示词管理'
  }
  return titles[route.path] || 'DKR'
})

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

/* 左侧边栏样式 */
.app-sidebar {
  background: #001529;
  color: white;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
  color: white;
  margin: 0;
}

.logo .el-icon {
  font-size: 24px;
  color: #1890ff;
}

.collapse-btn {
  color: rgba(255, 255, 255, 0.65);
}

.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
}

.sidebar-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.65);
}

.sidebar-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.sidebar-menu .el-menu-item.is-active {
  background: #1890ff;
  color: white;
}

.expand-btn-wrapper {
  padding: 16px;
  text-align: center;
}

/* 主内容区样式 */
.main-container {
  background: #f0f2f5;
}

.app-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.page-title {
  font-size: 18px;
  color: #303133;
  font-weight: 500;
  margin: 0;
}

.app-main {
  padding: 0;
  height: calc(100vh - 60px);
  overflow: auto;
  background: #f0f2f5;
}
</style>

