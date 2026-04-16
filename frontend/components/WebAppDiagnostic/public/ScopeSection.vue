<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Alcance y Consideraciones" />
    <ul class="list-disc pl-5 space-y-2 text-gray-700 leading-relaxed">
      <li v-for="(c, idx) in content.considerations" :key="idx">{{ c }}</li>
    </ul>
  </section>
</template>

<script setup>
import SectionHeader from './SectionHeader.vue';
defineProps({ content: { type: Object, required: true } });
</script>
