<script setup>
import { onMounted, ref } from 'vue';
import { Application } from '@splinetool/runtime';

const props = defineProps({
  spline: {
    type: String,
    required: true,
  }
});

const emit = defineEmits(['loaded']); // Define the 'loaded' event
const canvasContainer = ref(null);

onMounted(() => {
  const canvas = document.createElement('canvas');
  canvasContainer.value.appendChild(canvas);

  const app = new Application(canvas);

  // Load the Spline model and listen for when it's fully loaded
  app.load(props.spline).then(() => {
    emit('loaded'); // Emit the 'loaded' event when the model is ready
  });
});
</script>

<template>
  <div ref="canvasContainer" class="canvas-container rounded-xl"></div>
</template>

<style scoped>
.canvas-container {
  width: 95%;
  height: 90%;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>

  