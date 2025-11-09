<template>
  <div class="home">
    <ChatInterface />
  </div>
</template>

<script setup lang="ts">
import ChatInterface from '@/components/ChatInterface.vue'
</script>

<style scoped>
.home {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>

