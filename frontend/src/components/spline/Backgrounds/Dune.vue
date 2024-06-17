<template>
    <div ref="canvasContainer" class="canvas-container"></div>
  </template>
  
  <script setup>
  import { onMounted, ref } from 'vue';
  import { Application } from '@splinetool/runtime';
  
  const props = defineProps({
    spline: {
      type: String,
      required: true,
    }
  })
  const canvasContainer = ref(null);
  
  onMounted(() => {
    const canvas = document.createElement('canvas');
    canvasContainer.value.appendChild(canvas);
  
    const app = new Application(canvas);
    app.load(props.spline)
  });
  </script>
  
  <style scoped>
  .canvas-container {
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  </style>
  