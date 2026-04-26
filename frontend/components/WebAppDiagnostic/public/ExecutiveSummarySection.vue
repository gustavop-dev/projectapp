<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Resumen Ejecutivo" />
    <p v-if="content.intro" class="text-esmerald/80 dark:text-esmerald-light/80 mb-6">{{ content.intro }}</p>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <div
        v-for="(count, key) in counts"
        :key="key"
        class="bg-white dark:bg-esmerald-light/5 border border-esmerald/10 dark:border-esmerald-light/15 rounded-2xl p-4 text-center shadow-sm"
      >
        <div
          class="text-3xl font-semibold"
          :class="levelColor(key)"
        >{{ count }}</div>
        <div class="text-xs font-medium text-esmerald/55 dark:text-esmerald-light/60 uppercase mt-1 tracking-wide">{{ labelFor(key) }}</div>
      </div>
    </div>

    <p v-if="content.narrative" class="text-esmerald/80 dark:text-esmerald-light/80 leading-relaxed whitespace-pre-line">{{ content.narrative }}</p>

    <ul v-if="content.highlights?.length" class="mt-4 list-disc pl-5 space-y-1 text-esmerald/80 dark:text-esmerald-light/80">
      <li v-for="(h, idx) in content.highlights" :key="idx">{{ h }}</li>
    </ul>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import SectionHeader from './SectionHeader.vue';

const props = defineProps({ content: { type: Object, required: true } });

const counts = computed(() => ({
  critico: props.content.severityCounts?.critico ?? 0,
  alto: props.content.severityCounts?.alto ?? 0,
  medio: props.content.severityCounts?.medio ?? 0,
  bajo: props.content.severityCounts?.bajo ?? 0,
}));

function labelFor(key) {
  return { critico: 'Crítico', alto: 'Alto', medio: 'Medio', bajo: 'Bajo' }[key] || key;
}
function levelColor(key) {
  return {
    critico: 'text-rose-600 dark:text-rose-300',
    alto: 'text-amber-600 dark:text-amber-300',
    medio: 'text-yellow-600 dark:text-yellow-300',
    bajo: 'text-esmerald dark:text-lemon',
  }[key] || 'text-esmerald/60 dark:text-esmerald-light/60';
}
</script>
