<template>
  <el-container id="app">
    <el-header class="app-header">
      <div class="header-content">
        <h1>DKR - Deep Knowledge Retrieval</h1>
        <el-menu mode="horizontal" :default-active="activeMenu" router>
          <el-menu-item index="/">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能检索</span>
          </el-menu-item>
          <el-menu-item index="/documents">
            <el-icon><Document /></el-icon>
            <span>文档管理</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChatDotRound, Document } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
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
}

.app-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
}

.header-content h1 {
  font-size: 20px;
  color: #303133;
  font-weight: 600;
}

.app-main {
  padding: 0;
  height: calc(100vh - 60px);
  overflow: hidden;
}
</style>

