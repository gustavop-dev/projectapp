<template>
  <section
    class="rounded-xl bg-surface-raised"
    data-testid="utility-stats-panel"
  >
    <BaseButton
      type="button"
      variant="ghost"
      class="w-full justify-between rounded-xl px-3 py-3 text-left panel-portrait:px-4"
      :aria-expanded="open"
      aria-controls="utility-stats-content"
      data-testid="utility-stats-toggle"
      @click="open = !open"
    >
      <span class="min-w-0">
        <span class="block text-sm font-semibold text-text-default">
          Estadísticas de utilidad {{ summary?.year || '' }}
        </span>
        <span class="mt-0.5 block whitespace-normal text-xs font-normal text-text-muted">
          Evolución, márgenes y reparto entre socios.
        </span>
      </span>
      <ChevronDownIcon
        class="h-5 w-5 shrink-0 text-text-muted transition-transform motion-reduce:transition-none"
        :class="open ? 'rotate-180' : ''"
        aria-hidden="true"
      />
    </BaseButton>

    <BaseCollapse id="utility-stats-content" :open="open">
      <div class="border-t border-border-muted px-3 pb-4 pt-4 panel-portrait:px-4">
        <BaseTabs
          v-model="activeTab"
          :tabs="TABS"
          aria-label="Secciones de estadísticas de utilidad"
        />

        <div v-if="activeTab === 'evolution'" class="space-y-5">
          <StatsSummaryStrip :items="evolutionStrip" />
          <StatsLineChart
            :series="evolutionSeries"
            :categories="monthCategories"
            :colors="[palette.measures[0], palette.measures[1]]"
          />
        </div>

        <div v-else-if="activeTab === 'margin'" class="space-y-5">
          <StatsSummaryStrip :items="marginStrip" />
          <div class="grid grid-cols-1 items-center gap-4 lg:grid-cols-3">
            <StatsRadialChart
              :value="yearMarginPct"
              label="Margen líquido del año"
              :tone="yearMarginPct !== null && yearMarginPct >= 0 ? 'success' : 'danger'"
            />
            <div class="lg:col-span-2">
              <p class="mb-2 text-xs text-text-muted">
                Margen mensual (utilidad líquida sobre ingreso líquido; meses sin
                ingreso no puntúan).
              </p>
              <StatsBarChart
                :series="[{ name: 'Margen %', data: monthlyMarginPct }]"
                :categories="monthCategories"
                value-format="percent"
                :colors="[palette.measures[1]]"
                :height="230"
              />
            </div>
          </div>
        </div>

        <div v-else class="space-y-5">
          <StatsSummaryStrip :items="partnersStrip" />
          <div class="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
            <StatsDonutChart
              :labels="positiveNets.map((partner) => partner.label)"
              :values="positiveNets.map((partner) => partner.net)"
              :colors="palette.categorical"
              :height="260"
              empty-title="Sin netos positivos que repartir"
            />
            <div class="space-y-3">
              <div
                v-for="partner in partnerRows"
                :key="partner.key"
                class="rounded-xl border border-border-muted bg-surface p-4"
              >
                <p class="mb-2 text-xs uppercase tracking-wider text-text-muted">
                  {{ partner.label }}
                </p>
                <dl class="space-y-1 text-sm">
                  <div class="flex items-center justify-between gap-3">
                    <dt class="text-text-muted">Esperado</dt>
                    <dd class="tabular-nums text-text-default">{{ money(partner.data.expected) }}</dd>
                  </div>
                  <div class="flex items-center justify-between gap-3">
                    <dt class="text-text-muted">Líquido</dt>
                    <dd class="tabular-nums text-text-default">{{ money(partner.data.liquid) }}</dd>
                  </div>
                  <div class="flex items-center justify-between gap-3">
                    <dt class="text-text-muted">Gastos</dt>
                    <dd class="tabular-nums text-text-default">{{ money(partner.data.expenses) }}</dd>
                  </div>
                  <div class="flex items-center justify-between gap-3 border-t border-border-muted pt-1">
                    <dt class="font-medium text-text-default">Neto</dt>
                    <dd
                      class="tabular-nums font-semibold"
                      :class="Number(partner.data.net) < 0
                        ? 'text-danger-strong'
                        : 'text-success-strong'"
                    >
                      {{ money(partner.data.net) }}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>
    </BaseCollapse>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import { ChevronDownIcon } from '@heroicons/vue/24/outline';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseCollapse from '~/components/base/BaseCollapse.vue';
import BaseTabs from '~/components/base/BaseTabs.vue';
import StatsSummaryStrip from '~/components/stats/StatsSummaryStrip.vue';
import StatsLineChart from '~/components/stats/charts/StatsLineChart.vue';
import StatsBarChart from '~/components/stats/charts/StatsBarChart.vue';
import StatsDonutChart from '~/components/stats/charts/StatsDonutChart.vue';
import StatsRadialChart from '~/components/stats/charts/StatsRadialChart.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { shortMonthLabels } from '~/utils/accountingCharts';
import { formatMoney } from '~/utils/formatMoney';

/** Utility analytics embedded in the summary hero as a default-open accordion. */
const props = defineProps({
  monthly: { type: Array, default: () => [] },
  summary: { type: Object, default: null },
  partners: { type: Object, default: () => ({}) },
});

const TABS = [
  { id: 'evolution', label: 'Evolución' },
  { id: 'margin', label: 'Márgenes' },
  { id: 'partners', label: 'Socios' },
];

const open = ref(true);
const activeTab = ref('evolution');
const { palette } = useChartTheme();

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

function toneBySign(value) {
  return Number(value) < 0 ? 'danger' : 'success';
}

const monthCategories = computed(() => shortMonthLabels(props.monthly));
const evolutionSeries = computed(() => [
  {
    name: 'Utilidad esperada',
    data: props.monthly.map((row) => Number(row.expected_utility) || 0),
  },
  {
    name: 'Utilidad líquida',
    data: props.monthly.map((row) => Number(row.utility) || 0),
  },
]);

const evolutionStrip = computed(() => [
  {
    label: 'Utilidad esperada año',
    value: money(props.summary?.expected_utility),
    tone: toneBySign(props.summary?.expected_utility),
  },
  {
    label: 'Utilidad líquida año',
    value: money(props.summary?.liquid_utility),
    tone: toneBySign(props.summary?.liquid_utility),
  },
  {
    label: 'Diferencia líq − esp',
    value: money(props.summary?.difference),
    tone: toneBySign(props.summary?.difference),
  },
]);

const yearMarginPct = computed(() => {
  const liquid = Number(props.summary?.liquid_total);
  if (!liquid || liquid <= 0) return null;
  return Math.round((Number(props.summary?.liquid_utility) / liquid) * 1000) / 10;
});

const monthlyMarginPct = computed(() =>
  props.monthly.map((row) => {
    const liquid = Number(row.liquid) || 0;
    if (liquid <= 0) return null;
    return Math.round(((Number(row.utility) || 0) / liquid) * 1000) / 10;
  }),
);

const marginStrip = computed(() => [
  {
    label: 'Margen líquido año',
    value: yearMarginPct.value === null ? '—' : `${yearMarginPct.value}%`,
    tone: yearMarginPct.value !== null && yearMarginPct.value < 0 ? 'danger' : 'success',
  },
  { label: 'Ingreso líquido', value: money(props.summary?.liquid_total) },
  { label: 'Gastos', value: money(props.summary?.expenses_total), tone: 'danger' },
]);

const PARTNER_LABELS = [
  { key: 'gustavo', label: 'Gustavo' },
  { key: 'carlos', label: 'Carlos' },
  { key: 'company', label: 'ProjectApp (Empresa)' },
];

const partnerRows = computed(() => {
  const empty = { expected: 0, liquid: 0, expenses: 0, net: 0 };
  return PARTNER_LABELS.map(({ key, label }) => ({
    key,
    label,
    data: props.partners?.[key] || empty,
  }));
});

const positiveNets = computed(() =>
  partnerRows.value
    .map((partner) => ({ ...partner, net: Number(partner.data.net) || 0 }))
    .filter((partner) => partner.net > 0),
);

const partnersStrip = computed(() =>
  partnerRows.value.map((partner) => ({
    label: `Neto ${partner.label}`,
    value: money(partner.data.net),
    tone: toneBySign(partner.data.net),
  })),
);
</script>
