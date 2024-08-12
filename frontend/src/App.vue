<template>
  <LoadingScreen v-show="loading"></LoadingScreen>
  <RouterView v-show="!loading"/>
</template>

<script setup>
  import { ref, onMounted, onBeforeMount } from 'vue'
  import LoadingScreen from '@/components/layouts/LoadingScreen.vue';
  import { RouterView } from 'vue-router'

  const loading = ref(true);

  const handleLoad = () => {
    loading.value = false;
  }

  onMounted(() => {
    window.addEventListener('load', handleLoad);
  })

  onBeforeMount(() => {
    window.removeEventListener('load', handleLoad);
  })
</script>

<style>
body {
  overflow-x: hidden; 
}
</style>

