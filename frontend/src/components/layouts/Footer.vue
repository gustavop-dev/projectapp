<template>
    <div class="relative">
        <component :is="isDesktop ? FooterDesktop : FooterMobile" />
    </div>
</template>
<script setup>
import { defineAsyncComponent, ref, onMounted, onBeforeUnmount, shallowRef } from 'vue';

// Carga diferida de componentes para mejor rendimiento inicial
const FooterDesktop = defineAsyncComponent(() => import('@/components/layouts/FooterDesktop.vue'));
const FooterMobile = defineAsyncComponent(() => import('@/components/layouts/FooterMobile.vue'));

const isDesktop = ref(window.innerWidth >= 1024);

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

// Añadir event listener para window resize
onMounted(() => {
  window.addEventListener('resize', handleResize, { passive: true });
});

// Limpiar event listener y timeout cuando el componente se desmonta
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (resizeTimeout) {
    clearTimeout(resizeTimeout);
  }
});
</script>