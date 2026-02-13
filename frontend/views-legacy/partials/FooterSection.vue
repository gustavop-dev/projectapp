<template>
  <section class="mt-16 relative">
    <Footer />
  </section>
</template>

<script setup>
import Footer from '~/components/layouts/Footer.vue'
</script>

<style scoped>
/* Use CSS containment for improved rendering performance */
section {
  contain: content;
}
</style> 