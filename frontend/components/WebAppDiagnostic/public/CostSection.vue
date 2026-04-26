<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Costo y Formas de Pago" />
    <p v-if="content.intro" class="text-esmerald/80 dark:text-esmerald-light/80">{{ content.intro }}</p>

    <ul
      v-if="valueBullets.length"
      class="mt-4 space-y-2 text-esmerald/80 dark:text-esmerald-light/80"
    >
      <li
        v-for="(bullet, idx) in valueBullets"
        :key="idx"
        class="flex gap-3"
      >
        <span class="mt-2 shrink-0 size-1.5 rounded-full bg-lemon dark:bg-lemon" aria-hidden="true" />
        <span>{{ bullet }}</span>
      </li>
    </ul>

    <div
      v-if="investmentFormatted"
      class="my-6 relative overflow-hidden bg-esmerald dark:bg-esmerald-dark text-bone rounded-2xl p-6 text-center shadow-lg ring-1 ring-transparent dark:ring-esmerald-light/15"
    >
      <div class="absolute inset-0 bg-gradient-to-br from-esmerald/0 via-lemon/5 to-lemon/20 pointer-events-none" />
      <div class="relative">
        <div class="text-xs font-medium text-bone/80 uppercase tracking-[0.2em]">Inversión</div>
        <div class="text-4xl font-semibold text-lemon mt-2 tabular-nums">
          {{ investmentFormatted }}
          <span class="text-2xl text-bone/80 ml-1">{{ diagnostic.currency || '' }}</span>
        </div>
      </div>
    </div>

    <ul v-if="paymentItems.length" class="space-y-2 text-esmerald/80 dark:text-esmerald-light/80">
      <li
        v-for="(item, idx) in paymentItems"
        :key="idx"
        class="flex gap-3 items-baseline"
      >
        <span class="shrink-0 font-semibold text-esmerald dark:text-esmerald-light">
          <template v-if="item.pct !== ''">{{ item.pct }}% </template>{{ item.label }}
        </span>
        <span class="text-esmerald/70 dark:text-esmerald-light/70">{{ item.detail }}</span>
      </li>
    </ul>

    <blockquote v-if="content.note" class="mt-6 border-l-4 border-esmerald/40 dark:border-lemon/60 bg-esmerald/5 dark:bg-esmerald-light/5 text-esmerald/80 dark:text-esmerald-light/80 italic px-4 py-3 rounded-r-lg text-sm">
      <strong class="not-italic">Nota:</strong> {{ content.note }}
    </blockquote>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import SectionHeader from './SectionHeader.vue';

const props = defineProps({
  content: { type: Object, required: true },
  diagnostic: { type: Object, required: true },
  renderContext: { type: Object, default: () => ({}) },
});

const investmentFormatted = computed(() => {
  const n = Number(props.diagnostic?.investment_amount);
  if (!n) return '';
  return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(n);
});

const valueBullets = computed(() => {
  const arr = props.content?.valueBullets;
  if (!Array.isArray(arr)) return [];
  return arr.map((s) => (typeof s === 'string' ? s.trim() : '')).filter(Boolean);
});

const paymentItems = computed(() => {
  const desc = props.content.paymentDescription || [];
  const ctx = props.renderContext || {};
  const terms = props.diagnostic?.payment_terms || {};
  const pctCandidates = [
    ctx.payment_initial_pct ?? terms.initial_pct,
    ctx.payment_final_pct ?? terms.final_pct,
  ];
  return desc.map((item, idx) => ({
    label: item.label,
    detail: item.detail,
    pct: pctCandidates[idx] ?? '',
  }));
});
</script>
