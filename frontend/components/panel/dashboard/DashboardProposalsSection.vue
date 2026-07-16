<template>
  <section
    v-if="proposals"
    aria-labelledby="dashboard-proposals-title"
    data-testid="dashboard-proposals-section"
  >
    <div class="mb-3 flex items-center justify-between">
      <h2
        id="dashboard-proposals-title"
        class="text-xs font-semibold uppercase tracking-widest text-text-muted"
      >
        Propuestas
      </h2>
      <NuxtLink
        :to="localePath('/panel/proposals')"
        class="text-xs text-text-brand hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring rounded"
      >
        Ver análisis completo →
      </NuxtLink>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-4">
          <DashboardStatTile
            label="Tasa de cierre"
            :value="proposals.conversion_rate"
            format="percent"
            :tone="proposals.conversion_rate >= 50 ? 'brand' : 'default'"
            sub="de propuestas terminales"
          />
          <DashboardStatTile
            label="Total propuestas"
            :value="proposals.total_proposals"
            format="number"
          />
        </div>

        <div class="flex flex-wrap gap-2" data-testid="dashboard-status-pills">
          <span
            v-for="(count, st) in statusesWithCount"
            :key="st"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
            :class="pillClass(st)"
          >
            {{ statusLabel(st) }}: <strong>{{ count }}</strong>
          </span>
        </div>
      </div>

      <div class="bg-surface rounded-xl border border-border-muted shadow-card p-5">
        <h3 class="text-sm font-medium text-text-default mb-3">
          Tendencia últimos 6 meses
        </h3>
        <DashboardTrendChart :trend="proposals.monthly_trend || []" />
      </div>
    </div>

    <div class="mt-4 bg-surface rounded-xl shadow-card border border-border-muted">
      <div class="px-5 py-4 border-b border-border-muted flex items-center justify-between">
        <h3 class="text-sm font-medium text-text-default">Propuestas recientes</h3>
        <NuxtLink
          :to="localePath('/panel/proposals')"
          class="text-xs text-text-brand hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring rounded"
        >
          Ver todas →
        </NuxtLink>
      </div>
      <BaseEmptyState
        v-if="!recent.length"
        title="Aún no hay propuestas"
        description="Crea la primera propuesta para empezar a llenar el pipeline."
      />
      <ul v-else class="divide-y divide-border-muted">
        <li v-for="p in recent" :key="p.id">
          <NuxtLink
            :to="localePath(`/panel/proposals/${p.id}/edit`)"
            class="flex items-center justify-between px-5 py-3.5 hover:bg-surface-raised transition-colors motion-reduce:transition-none
                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-focus-ring"
          >
            <span class="min-w-0">
              <span class="block text-sm font-medium text-text-default truncate">
                {{ p.title }}
              </span>
              <span class="block text-xs text-text-subtle mt-0.5 truncate">
                {{ p.client_name }}
              </span>
            </span>
            <span
              class="ml-3 shrink-0 text-xs px-2.5 py-1 rounded-full font-medium"
              :class="pillClass(p.status)"
            >
              {{ statusLabel(p.status) }}
            </span>
          </NuxtLink>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import DashboardStatTile from '~/components/panel/dashboard/DashboardStatTile.vue';
import DashboardTrendChart from '~/components/panel/dashboard/DashboardTrendChart.vue';

/** Curated commercial summary; the deep-dive lives in /panel/proposals. */
const props = defineProps({
  proposals: { type: Object, default: null },
});

const localePath = useLocalePath();

const recent = computed(() => props.proposals?.recent || []);

const statusesWithCount = computed(() => {
  const byStatus = props.proposals?.by_status || {};
  return Object.fromEntries(
    Object.entries(byStatus).filter(([, count]) => count > 0),
  );
});

const STATUS_LABELS = {
  draft: 'Borrador',
  sent: 'Enviada',
  viewed: 'Vista',
  negotiating: 'Negociando',
  accepted: 'Aceptada',
  finished: 'Finalizada',
  rejected: 'Rechazada',
  expired: 'Expirada',
};

const PILL_CLASSES = {
  draft: 'bg-surface-raised text-text-muted',
  sent: 'bg-info-soft text-info-strong',
  viewed: 'bg-success-soft text-success-strong',
  negotiating: 'bg-warning-soft text-warning-strong',
  accepted: 'bg-primary-soft text-text-brand',
  finished: 'bg-primary-soft text-text-brand',
  rejected: 'bg-danger-soft text-danger-strong',
  expired: 'bg-warning-soft text-warning-strong',
};

function statusLabel(status) {
  return STATUS_LABELS[status] || status;
}

function pillClass(status) {
  return PILL_CLASSES[status] || 'bg-surface-raised text-text-muted';
}
</script>
