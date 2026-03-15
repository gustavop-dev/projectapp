<template>
  <section class="mt-16">
    <Contact />
  </section>
</template>

<script setup>
import Contact from '~/components/layouts/Contact.vue'
</script>

<style scoped>
/* Use CSS containment for improved rendering performance */
section {
  contain: content;
}
</style> 
