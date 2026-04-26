<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Alcance y Consideraciones" />
    <ul class="space-y-2.5 text-esmerald/80 dark:text-esmerald-light/80 leading-relaxed">
      <li v-for="(c, idx) in content.considerations" :key="idx" class="flex gap-3">
        <span class="mt-1.5 flex-none w-1.5 h-1.5 rounded-full bg-esmerald dark:bg-lemon" />
        <span>{{ c }}</span>
      </li>
    </ul>
  </section>
</template>

<script setup>
import SectionHeader from './SectionHeader.vue';
defineProps({ content: { type: Object, required: true } });
</script>
