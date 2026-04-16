<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Cronograma" />
    <p v-if="content.intro" class="text-gray-700">{{ content.intro }}</p>

    <p v-if="durationLabel" class="mt-3 text-gray-700">
      Duración estimada: <strong>{{ durationLabel }}</strong>.
    </p>

    <h3 v-if="content.distributionTitle" class="text-lg font-semibold text-gray-900 mt-6 mb-3">
      {{ content.distributionTitle }}
    </h3>

    <ol class="relative border-l-2 border-emerald-200 pl-6 space-y-4">
      <li
        v-for="(d, idx) in content.distribution"
        :key="idx"
        class="relative"
      >
        <span class="absolute -left-3 top-1 w-5 h-5 rounded-full bg-emerald-500 text-white text-[10px] font-semibold flex items-center justify-center shadow">
          {{ idx + 1 }}
        </span>
        <div class="font-semibold text-gray-800">{{ d.dayRange }}</div>
        <div class="text-sm text-gray-600">{{ d.description }}</div>
      </li>
    </ol>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import SectionHeader from './SectionHeader.vue';

const props = defineProps({
  content: { type: Object, required: true },
  diagnostic: { type: Object, required: true },
});

const durationLabel = computed(() => props.diagnostic?.duration_label || '');
</script>
