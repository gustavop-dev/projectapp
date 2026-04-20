<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Cronograma" />
    <p v-if="content.intro" class="text-esmerald/80 leading-relaxed">{{ content.intro }}</p>

    <p v-if="durationLabel" class="mt-3 text-esmerald/80">
      Duración estimada: <strong class="text-esmerald">{{ durationLabel }}</strong>.
    </p>

    <h3 v-if="content.distributionTitle" class="text-lg font-semibold text-esmerald mt-6 mb-4">
      {{ content.distributionTitle }}
    </h3>

    <ol class="space-y-4">
      <li
        v-for="(d, idx) in content.distribution"
        :key="idx"
        class="flex gap-4 items-start"
      >
        <span
          class="flex-none w-9 h-9 rounded-full bg-esmerald text-lemon text-sm font-semibold
                 flex items-center justify-center leading-none shadow-sm ring-4 ring-esmerald/10"
        >
          {{ idx + 1 }}
        </span>
        <div class="flex-1 min-w-0 border-l-2 border-esmerald/15 pl-4 pb-2">
          <div class="font-semibold text-esmerald">{{ d.dayRange }}</div>
          <div class="text-sm text-esmerald/70 leading-relaxed mt-0.5">{{ d.description }}</div>
        </div>
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
