<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Categorías evaluadas" />
    <p v-if="content.intro" class="text-gray-700 mb-6">{{ content.intro }}</p>

    <div class="space-y-3">
      <details
        v-for="(cat, idx) in content.categories"
        :key="cat.key || idx"
        class="group border border-gray-200 rounded-2xl bg-white shadow-sm"
      >
        <summary class="px-5 py-4 cursor-pointer select-none flex items-center justify-between">
          <span class="font-semibold text-gray-900 text-base">
            <span class="text-emerald-600 mr-2 font-mono text-sm">{{ idx + 1 }}.</span>
            {{ cat.title }}
          </span>
          <span class="text-xs text-gray-400 flex gap-2 items-center">
            <span v-if="cat.findings?.length" class="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full">
              {{ cat.findings.length }} hallazgo(s)
            </span>
            <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </span>
        </summary>
        <div class="px-5 pb-5 border-t border-gray-100 space-y-4 text-sm">
          <p v-if="cat.description" class="text-gray-600 leading-relaxed pt-3">{{ cat.description }}</p>

          <div v-if="cat.strengths?.length">
            <h4 class="font-semibold text-emerald-700 mb-1">Lo que se encontró bien</h4>
            <ul class="list-disc pl-5 space-y-1 text-gray-700">
              <li v-for="(s, si) in cat.strengths" :key="si">{{ s }}</li>
            </ul>
          </div>

          <div v-if="cat.findings?.length">
            <h4 class="font-semibold text-rose-700 mb-1">Hallazgos</h4>
            <ul class="space-y-2">
              <li v-for="(f, fi) in cat.findings" :key="fi" class="flex gap-2 items-start">
                <span
                  class="shrink-0 px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full"
                  :class="levelClass(f.level)"
                >{{ f.level }}</span>
                <div>
                  <div class="font-medium text-gray-800">{{ f.title }}</div>
                  <div v-if="f.detail" class="text-gray-600">{{ f.detail }}</div>
                </div>
              </li>
            </ul>
          </div>

          <div v-if="cat.recommendations?.length">
            <h4 class="font-semibold text-indigo-700 mb-1">Recomendaciones</h4>
            <ul class="space-y-2">
              <li v-for="(r, ri) in cat.recommendations" :key="ri" class="flex gap-2 items-start">
                <span
                  class="shrink-0 px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full"
                  :class="levelClass(r.level)"
                >{{ r.level }}</span>
                <div>
                  <div class="font-medium text-gray-800">{{ r.title }}</div>
                  <div v-if="r.detail" class="text-gray-600">{{ r.detail }}</div>
                </div>
              </li>
            </ul>
          </div>

          <p v-if="!cat.strengths?.length && !cat.findings?.length && !cat.recommendations?.length"
             class="text-gray-400 italic text-xs pt-2">
            Hallazgos y recomendaciones se completarán durante el diagnóstico.
          </p>
        </div>
      </details>
    </div>
  </section>
</template>

<script setup>
import SectionHeader from './SectionHeader.vue';
import { severityLevelClass as levelClass } from '~/stores/diagnostics_constants';

defineProps({ content: { type: Object, required: true } });
</script>
