<template>
  <div ref="canvasContainer" class="canvas-container rounded-xl"></div>
</template>

<script setup>
import { onMounted, ref, onBeforeUnmount } from 'vue';
import { Application } from '@splinetool/runtime';

const props = defineProps({
  spline: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['loaded']);
const canvasContainer = ref(null);
let app = null; // Almacena la instancia de Spline Application

/**
 * Inicializa el canvas de Spline y lo monta en el DOM.
 */
const initializeCanvas = () => {
  const canvas = document.createElement('canvas');
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvasContainer.value.appendChild(canvas);

  app = new Application(canvas);

  // Cargar el modelo de Spline y emitir el evento 'loaded' cuando esté listo
  app.load(props.spline).then(() => {
    emit('loaded');
  }).catch(error => {
    console.error("Error loading Spline model:", error);
  });
};

// Monta el canvas cuando el componente se monta
onMounted(() => {
  initializeCanvas();
});

// Limpia los recursos de Spline cuando el componente se desmonta
onBeforeUnmount(() => {
  if (app) {
    app.dispose();
    app = null;
  }
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