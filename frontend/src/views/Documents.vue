<template>
  <div class="documents-page">
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="文档列表" name="list">
        <DocumentList ref="documentListRef" />
      </el-tab-pane>
      
      <el-tab-pane label="上传文档" name="upload">
        <DocumentUpload @success="handleUploadSuccess" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DocumentList from '@/components/DocumentList.vue'
import DocumentUpload from '@/components/DocumentUpload.vue'

const activeTab = ref('list')
const documentListRef = ref()

const handleUploadSuccess = () => {
  activeTab.value = 'list'
  documentListRef.value?.loadDocuments()
}
</script>

<style scoped>
.documents-page {
  padding: 20px;
  height: 100vh;
}
</style>

