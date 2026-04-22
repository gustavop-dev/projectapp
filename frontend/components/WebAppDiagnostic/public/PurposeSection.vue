<template>
  <section class="prose prose-gray max-w-none">
    <SectionHeader :index="content.index" :title="content.title" fallback="Propósito" />

    <p v-for="(p, idx) in content.paragraphs" :key="idx" class="text-esmerald/80 leading-relaxed">
      {{ p }}
    </p>

    <blockquote
      v-if="content.scopeNote"
      class="border-l-4 border-esmerald bg-esmerald/5 text-esmerald italic px-4 py-3 rounded-r-lg"
    >
      <strong class="not-italic">Alcance:</strong> {{ content.scopeNote }}
    </blockquote>

    <div v-if="content.severityLevels?.length" class="mt-8">
      <h3 class="text-lg font-semibold text-esmerald mb-2">{{ content.severityTitle || 'Escala de Severidad' }}</h3>
      <p v-if="content.severityIntro" class="text-esmerald/75">{{ content.severityIntro }}</p>
      <div class="overflow-x-auto mt-3">
        <table class="min-w-full text-sm border border-esmerald/10 rounded-xl overflow-hidden">
          <thead class="bg-esmerald/5">
            <tr>
              <th class="px-3 py-2 text-left font-semibold text-esmerald w-28">Nivel</th>
              <th class="px-3 py-2 text-left font-semibold text-esmerald">Significado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(lvl, i) in content.severityLevels" :key="i" class="border-t border-esmerald/10">
              <td class="px-3 py-2 font-semibold text-esmerald">{{ lvl.level }}</td>
              <td class="px-3 py-2 text-esmerald/75">{{ lvl.meaning }}</td>
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
