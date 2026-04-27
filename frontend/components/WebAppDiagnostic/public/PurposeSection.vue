<template>
  <section class="prose prose-gray dark:prose-invert max-w-none">
    <SectionHeader :index="content.index" :title="content.title" fallback="Propósito" />

    <p v-for="(p, idx) in content.paragraphs" :key="idx" class="text-text-brand/80 dark:text-text-brand/80 leading-relaxed mb-6">
      {{ p }}
    </p>

    <blockquote
      v-if="content.scopeNote"
      class="border-l-4 border-input-border dark:border-lemon bg-primary/5 dark:bg-primary-soft/5 text-text-brand dark:text-text-brand italic px-4 py-3 rounded-r-lg"
    >
      <strong class="not-italic">Alcance:</strong> {{ content.scopeNote }}
    </blockquote>

    <div v-if="content.severityLevels?.length" class="mt-8">
      <h3 class="text-lg font-semibold text-text-brand dark:text-text-brand mb-2">{{ content.severityTitle || 'Escala de Severidad' }}</h3>
      <p v-if="content.severityIntro" class="text-text-brand/75 dark:text-text-brand/75">{{ content.severityIntro }}</p>
      <div class="overflow-x-auto mt-3">
        <table class="min-w-full text-sm border border-input-border/10 dark:border-input-border/15 rounded-xl overflow-hidden">
          <thead class="bg-primary/5 dark:bg-primary-soft/10">
            <tr>
              <th class="px-3 py-2 text-left font-semibold text-text-brand dark:text-text-brand w-28">Nivel</th>
              <th class="px-3 py-2 text-left font-semibold text-text-brand dark:text-text-brand">Significado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(lvl, i) in content.severityLevels" :key="i" class="border-t border-input-border/10 dark:border-input-border/15">
              <td class="px-3 py-2 font-semibold text-text-brand dark:text-text-brand">{{ lvl.level }}</td>
              <td class="px-3 py-2 text-text-brand/75 dark:text-text-brand/75">{{ lvl.meaning }}</td>
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
