<template>
  <section class="prose prose-gray dark:prose-invert max-w-none">
    <SectionHeader :index="content.index" :title="content.title" fallback="Propósito" />

    <p v-for="(p, idx) in content.paragraphs" :key="idx" class="text-esmerald/80 dark:text-esmerald-light/80 leading-relaxed mb-6">
      {{ p }}
    </p>

    <blockquote
      v-if="content.scopeNote"
      class="border-l-4 border-esmerald dark:border-lemon bg-esmerald/5 dark:bg-esmerald-light/5 text-esmerald dark:text-esmerald-light italic px-4 py-3 rounded-r-lg"
    >
      <strong class="not-italic">Alcance:</strong> {{ content.scopeNote }}
    </blockquote>

    <div v-if="content.severityLevels?.length" class="mt-8">
      <h3 class="text-lg font-semibold text-esmerald dark:text-esmerald-light mb-2">{{ content.severityTitle || 'Escala de Severidad' }}</h3>
      <p v-if="content.severityIntro" class="text-esmerald/75 dark:text-esmerald-light/75">{{ content.severityIntro }}</p>
      <div class="overflow-x-auto mt-3">
        <table class="min-w-full text-sm border border-esmerald/10 dark:border-esmerald-light/15 rounded-xl overflow-hidden">
          <thead class="bg-esmerald/5 dark:bg-esmerald-light/10">
            <tr>
              <th class="px-3 py-2 text-left font-semibold text-esmerald dark:text-esmerald-light w-28">Nivel</th>
              <th class="px-3 py-2 text-left font-semibold text-esmerald dark:text-esmerald-light">Significado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(lvl, i) in content.severityLevels" :key="i" class="border-t border-esmerald/10 dark:border-esmerald-light/15">
              <td class="px-3 py-2 font-semibold text-esmerald dark:text-esmerald-light">{{ lvl.level }}</td>
              <td class="px-3 py-2 text-esmerald/75 dark:text-esmerald-light/75">{{ lvl.meaning }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup>
import SectionHeader from './SectionHeader.vue';
defineProps({ content: { type: Object, required: true } });
</script>
