<template>
  <section class="prose prose-gray max-w-none">
    <SectionHeader :index="content.index" :title="content.title" fallback="Propósito" />

    <p v-for="(p, idx) in content.paragraphs" :key="idx" class="text-gray-700 leading-relaxed">
      {{ p }}
    </p>

    <blockquote v-if="content.scopeNote" class="border-l-4 border-emerald-500 bg-emerald-50 text-emerald-900 italic px-4 py-3 rounded-r-lg">
      <strong class="not-italic">Alcance:</strong> {{ content.scopeNote }}
    </blockquote>

    <div v-if="content.severityLevels?.length" class="mt-8">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ content.severityTitle || 'Escala de Severidad' }}</h3>
      <p v-if="content.severityIntro" class="text-gray-700">{{ content.severityIntro }}</p>
      <div class="overflow-x-auto mt-3">
        <table class="min-w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-3 py-2 text-left font-semibold text-gray-700 w-28">Nivel</th>
              <th class="px-3 py-2 text-left font-semibold text-gray-700">Significado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(lvl, i) in content.severityLevels" :key="i" class="border-t border-gray-200">
              <td class="px-3 py-2 font-semibold text-gray-800">{{ lvl.level }}</td>
              <td class="px-3 py-2 text-gray-700">{{ lvl.meaning }}</td>
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
