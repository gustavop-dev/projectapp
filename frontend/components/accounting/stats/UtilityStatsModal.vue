<template>
  <StatsModal
    :open="open"
    :title="`Estadísticas de utilidad ${summary?.year || ''}`"
    subtitle="Utilidad esperada vs líquida, márgenes y reparto entre socios."
    :tabs="TABS"
    v-model="activeTab"
    @close="emit('close')"
  >
    <template #default="{ activeTab: tab }">
      <div v-if="tab === 'evolution'" class="space-y-5">
        <StatsSummaryStrip :items="evolutionStrip" />
        <StatsLineChart
          :series="evolutionSeries"
          :categories="monthCategories"
          :colors="[palette.measures[0], palette.measures[1]]"
        />
      </div>

      <div v-else-if="tab === 'margin'" class="space-y-5">
        <StatsSummaryStrip :items="marginStrip" />
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 items-center">
          <StatsRadialChart
            :value="yearMarginPct"
            label="Margen líquido del año"
            :tone="yearMarginPct !== null && yearMarginPct >= 0 ? 'success' : 'danger'"
          />
          <div class="lg:col-span-2">
            <p class="text-xs text-text-muted mb-2">
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

      <div v-else-if="tab === 'partners'" class="space-y-5">
        <StatsSummaryStrip :items="partnersStrip" />
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
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
              class="bg-surface-raised rounded-xl p-4"
            >
              <p class="text-xs text-text-muted uppercase tracking-wider mb-2">
                {{ partner.label }}
              </p>
              <dl class="space-y-1 text-sm">
                <div class="flex items-center justify-between">
                  <dt class="text-text-muted">Esperado</dt>
                  <dd class="tabular-nums">{{ money(partner.data.expected) }}</dd>
                </div>
                <div class="flex items-center justify-between">
                  <dt class="text-text-muted">Líquido</dt>
                  <dd class="tabular-nums">{{ money(partner.data.liquid) }}</dd>
                </div>
                <div class="flex items-center justify-between">
                  <dt class="text-text-muted">Gastos</dt>
                  <dd class="tabular-nums">{{ money(partner.data.expenses) }}</dd>
                </div>
                <div
                  class="flex items-center justify-between pt-1 border-t border-border-muted"
                >
                  <dt class="font-medium">Neto</dt>
                  <dd
                    class="tabular-nums font-semibold"
                    :class="
                      Number(partner.data.net) < 0
                        ? 'text-danger-strong'
                        : 'text-success-strong'
                    "
                  >
                    {{ money(partner.data.net) }}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </template>
  </StatsModal>
</template>

<script setup>
import { computed, ref } from 'vue';
import StatsModal from '~/components/stats/StatsModal.vue';
import StatsSummaryStrip from '~/components/stats/StatsSummaryStrip.vue';
import StatsLineChart from '~/components/stats/charts/StatsLineChart.vue';
import StatsBarChart from '~/components/stats/charts/StatsBarChart.vue';
import StatsDonutChart from '~/components/stats/charts/StatsDonutChart.vue';
import StatsRadialChart from '~/components/stats/charts/StatsRadialChart.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { shortMonthLabels } from '~/utils/accountingCharts';
import { formatMoney } from '~/utils/formatMoney';

/** Utility analytics computed client-side from the dashboard summary. */
const props = defineProps({
  open: { type: Boolean, default: false },
  monthly: { type: Array, default: () => [] },
  summary: { type: Object, default: null },
  partners: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['close']);

const TABS = [
  { id: 'evolution', label: 'Evolución' },
  { id: 'margin', label: 'Márgenes' },
  { id: 'partners', label: 'Socios' },
];

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
