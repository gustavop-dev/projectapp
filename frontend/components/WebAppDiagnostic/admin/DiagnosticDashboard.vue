<script setup>
import { computed, ref, onMounted } from 'vue';
import { useAnimatedNumber } from '~/composables/useAnimatedNumber';
import { getDiagnosticAttention } from '~/utils/diagnosticAttention';

/**
 * KPI strip above the diagnostics list. Everything is derived client-side
 * from the already-loaded list — no extra endpoint. The "attention" tile is
 * the actionable one: it counts rows flagged by getDiagnosticAttention (the
 * same chips shown per row).
 */
const props = defineProps({
  diagnostics: { type: Array, default: () => [] },
});

const STORAGE_KEY = 'diagnostics_dashboard_collapsed';
const collapsed = ref(false);
onMounted(() => {
  collapsed.value = localStorage.getItem(STORAGE_KEY) === '1';
});
function toggle() {
  collapsed.value = !collapsed.value;
  localStorage.setItem(STORAGE_KEY, collapsed.value ? '1' : '0');
}

const ACTIVE_STATUSES = new Set(['sent', 'viewed', 'negotiating']);

const activeCount = computed(() =>
  props.diagnostics.filter((d) => ACTIVE_STATUSES.has(d.status)).length,
);

const pipelineAmount = computed(() =>
  props.diagnostics
    .filter((d) => ACTIVE_STATUSES.has(d.status))
    .reduce((sum, d) => sum + Number(d.investment_amount || 0), 0),
);

const responseRate = computed(() => {
  const sentEver = props.diagnostics.filter((d) => d.initial_sent_at);
  if (!sentEver.length) return null;
  const responded = sentEver.filter(
    (d) => d.responded_at || ['accepted', 'rejected', 'finished'].includes(d.status),
  );
  return Math.round((responded.length / sentEver.length) * 100);
});

const attentionCount = computed(() =>
  props.diagnostics.filter((d) => getDiagnosticAttention(d)).length,
);

const { animated: animatedActive } = useAnimatedNumber(activeCount);
const { animated: animatedPipeline } = useAnimatedNumber(pipelineAmount);
const { animated: animatedAttention } = useAnimatedNumber(attentionCount);

const moneyFormatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
</script>

<template>
  <section class="mb-6" aria-label="Resumen de diagnósticos">
    <button
      type="button"
      class="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-text-muted hover:text-text-brand rounded-lg px-1 py-1 focus:outline-none focus:ring-2 focus:ring-focus-ring/40 motion-safe:transition-colors motion-safe:duration-fast"
      :aria-expanded="!collapsed"
      aria-controls="diagnostics-dashboard-body"
      @click="toggle"
    >
      <svg
        class="w-3.5 h-3.5 motion-safe:transition-transform motion-safe:duration-fast"
        :class="collapsed ? '-rotate-90' : ''"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
      Resumen
    </button>

    <BaseCollapse id="diagnostics-dashboard-body" :open="!collapsed">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 pt-3">
        <div class="bg-surface rounded-xl border border-border-muted shadow-card px-4 py-3">
          <p class="text-2xs uppercase tracking-wider text-text-muted">En curso</p>
          <p class="text-2xl font-light text-text-default tabular-nums mt-1" data-testid="dashboard-active">
            {{ animatedActive }}
          </p>
          <p class="text-2xs text-text-subtle mt-0.5">enviados o en negociación</p>
        </div>

        <div class="bg-surface rounded-xl border border-border-muted shadow-card px-4 py-3">
          <p class="text-2xs uppercase tracking-wider text-text-muted">Pipeline activo</p>
          <p class="text-2xl font-light text-text-default tabular-nums mt-1">
            {{ moneyFormatter.format(animatedPipeline) }}
          </p>
          <p class="text-2xs text-text-subtle mt-0.5">inversión propuesta en curso</p>
        </div>

        <div class="bg-surface rounded-xl border border-border-muted shadow-card px-4 py-3">
          <p class="text-2xs uppercase tracking-wider text-text-muted">Tasa de respuesta</p>
          <p class="text-2xl font-light text-text-default tabular-nums mt-1">
            <span v-if="responseRate !== null">{{ responseRate }}%</span>
            <span v-else class="text-text-subtle">—</span>
          </p>
          <p class="text-2xs text-text-subtle mt-0.5">de los diagnósticos enviados</p>
        </div>

        <div
          class="rounded-xl border px-4 py-3 shadow-card"
          :class="attentionCount > 0
            ? 'bg-warning-soft border-warning-strong/30'
            : 'bg-surface border-border-muted'"
        >
          <p
            class="text-2xs uppercase tracking-wider"
            :class="attentionCount > 0 ? 'text-warning-strong' : 'text-text-muted'"
          >Requieren atención</p>
          <p
            class="text-2xl font-light tabular-nums mt-1"
            :class="attentionCount > 0 ? 'text-warning-strong' : 'text-text-default'"
            data-testid="dashboard-attention"
          >
            {{ animatedAttention }}
          </p>
          <p class="text-2xs mt-0.5" :class="attentionCount > 0 ? 'text-warning-strong/80' : 'text-text-subtle'">
            enviados sin respuesta del cliente
          </p>
        </div>
      </div>
    </BaseCollapse>
  </section>
</template>
