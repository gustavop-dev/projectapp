<template>
    <div class="relative">
        <FooterDesktop v-if="isDesktop"></FooterDesktop>
        <FooterMobile v-else></FooterMobile>
    </div>
</template>
<script setup>
import FooterMobile from '@/components/layouts/FooterMobile.vue';
import FooterDesktop from '@/components/layouts/FooterDesktop.vue';
import { ref, onMounted, onBeforeUnmount } from 'vue';

const isDesktop = ref(window.innerWidth >= 1024);

// Function to handle screen resize events
function handleResize() {
  isDesktop.value = window.innerWidth >= 1024;
}

// Add event listener for window resize
onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
});
</script>