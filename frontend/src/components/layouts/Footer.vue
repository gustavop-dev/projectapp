<template>
    <footer class="relative" aria-label="Website footer section">
        <component :is="isDesktop ? FooterDesktop : FooterMobile" />
    </footer>
</template>
<script setup>
import { defineAsyncComponent, ref, onMounted, onBeforeUnmount } from 'vue';

// Carga diferida de componentes para mejor rendimiento inicial
const FooterDesktop = defineAsyncComponent(() => import('@/components/layouts/FooterDesktop.vue'));
const FooterMobile = defineAsyncComponent(() => import('@/components/layouts/FooterMobile.vue'));

// Inicializar isDesktop con un valor por defecto de false
const isDesktop = ref(false);

// Debounce para optimizar la gestión de resize
let resizeTimeout;
function handleResize() {
  if (resizeTimeout) {
    clearTimeout(resizeTimeout);
  }
  resizeTimeout = setTimeout(() => {
    isDesktop.value = window.innerWidth >= 1024;
  }, 150);
}

// Añadir event listener para window resize y establecer valor inicial
onMounted(() => {
  // Verificar que window esté definido antes de usarlo
  if (typeof window !== 'undefined') {
    // Establecer el valor inicial después de montar el componente
    isDesktop.value = window.innerWidth >= 1024;
    window.addEventListener('resize', handleResize, { passive: true });
  }
});

// Limpiar event listener y timeout cuando el componente se desmonta
onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleResize);
    if (resizeTimeout) {
      clearTimeout(resizeTimeout);
    }
  }
});
</script>