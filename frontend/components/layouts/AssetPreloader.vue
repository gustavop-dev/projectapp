<template>
  <!-- Componente invisible que se encarga de precargar recursos estáticos -->
  <div style="display: none;">
    <!-- Slot para contenido personalizado -->
    <slot></slot>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue';
import { useAssetCache } from '~/composables/useAssetCache';

const props = defineProps({
  preloadImages: {
    type: Array,
    default: () => []
  },
  preloadVideos: {
    type: Array,
    default: () => []
  },
  imageExpiration: {
    type: Number,
    default: 7 * 24 * 60 * 60 * 1000 // 7 días para imágenes
  },
  videoExpiration: {
    type: Number,
    default: 30 * 24 * 60 * 60 * 1000 // 30 días para videos
  }
});

// Inicializar servicios de caché para imágenes y videos
const { 
  preloadAssets: preloadImageAssets,
  cleanExpiredResources: cleanExpiredImageResources
} = useAssetCache({
  cacheName: 'images-cache',
  expirationTime: props.imageExpiration
});

const { 
  preloadAssets: preloadVideoAssets,
  cleanExpiredResources: cleanExpiredVideoResources
} = useAssetCache({
  cacheName: 'videos-cache',
  expirationTime: props.videoExpiration
});

// Función para iniciar precarga
const startPreloading = async () => {
  // Limpiar recursos caducados primero
  await Promise.all([
    cleanExpiredImageResources(),
    cleanExpiredVideoResources()
  ]);

  // Iniciar precarga en segundo plano
  if (props.preloadImages.length > 0) {
    setTimeout(() => {
      preloadImageAssets(props.preloadImages);
    }, 1000);
  }

  if (props.preloadVideos.length > 0) {
    setTimeout(() => {
      preloadVideoAssets(props.preloadVideos);
    }, 2000); // Retrasar un poco más para no competir con las imágenes
  }
};

// Observar cambios en las listas de recursos
watch(() => props.preloadImages, (newAssets) => {
  if (newAssets.length > 0) {
    preloadImageAssets(newAssets);
  }
}, { deep: true });

watch(() => props.preloadVideos, (newAssets) => {
  if (newAssets.length > 0) {
    preloadVideoAssets(newAssets);
  }
}, { deep: true });

// Iniciar precarga cuando el componente se monta
onMounted(() => {
  // Utilizar requestIdleCallback si está disponible, sino setTimeout
  if (window.requestIdleCallback) {
    requestIdleCallback(() => {
      startPreloading();
    }, { timeout: 5000 });
  } else {
    setTimeout(() => {
      startPreloading();
    }, 3000);
  }
});
</script> 