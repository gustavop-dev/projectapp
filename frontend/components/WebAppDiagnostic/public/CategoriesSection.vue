<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Categorías evaluadas" />
    <p v-if="content.intro" class="text-esmerald/80 mb-6">{{ content.intro }}</p>

    <div class="space-y-3">
      <details
        v-for="(cat, idx) in content.categories"
        :key="cat.key || idx"
        class="group border-2 border-esmerald/10 rounded-2xl bg-esmerald/5 hover:border-esmerald/30 transition-all"
      >
        <summary class="px-6 py-5 cursor-pointer select-none flex items-center justify-between">
          <span class="font-semibold text-esmerald text-base">
            <span class="text-esmerald/50 mr-2 font-mono text-sm">{{ idx + 1 }}.</span>
            {{ cat.title }}
          </span>
          <span class="text-xs text-esmerald/60 flex gap-2 items-center">
            <span v-if="cat.findings?.length" class="font-bold text-white bg-esmerald/70 px-2.5 py-1 rounded-full">
              {{ cat.findings.length }} hallazgo(s)
            </span>
            <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </span>
        </summary>
        <div class="px-6 pb-6 border-t border-esmerald/15 bg-white/50 space-y-4 text-sm">
          <p v-if="cat.description" class="text-esmerald/70 leading-relaxed pt-3">{{ cat.description }}</p>

          <div v-if="cat.strengths?.length">
            <h4 class="font-semibold text-esmerald mb-1">Lo que se encontró bien</h4>
            <ul class="list-disc pl-5 space-y-1 text-esmerald/80">
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
                  <div class="font-medium text-esmerald">{{ f.title }}</div>
                  <div v-if="f.detail" class="text-esmerald/70">{{ f.detail }}</div>
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
                  <div class="font-medium text-esmerald">{{ r.title }}</div>
                  <div v-if="r.detail" class="text-esmerald/70">{{ r.detail }}</div>
                </div>
              </li>
            </ul>
          </div>

          <p v-if="!cat.strengths?.length && !cat.findings?.length && !cat.recommendations?.length"
             class="text-esmerald/45 italic text-xs pt-2">
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
