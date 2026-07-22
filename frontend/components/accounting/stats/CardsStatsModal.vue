<template>
  <StatsModal
    :open="open"
    title="Estadísticas de tarjetas"
    subtitle="Evolución de la deuda, uso del cupo e histórico de cortes."
    :tabs="TABS"
    v-model="activeTab"
    :loading="loading"
    @close="emit('close')"
  >
    <template #default="{ activeTab: tab }">
      <div v-if="tab === 'evolution'" class="space-y-5">
        <StatsSummaryStrip :items="debtStrip" />
        <CardDebtChart :snapshots="snapshots" />
      </div>

      <div v-else-if="tab === 'usage'" class="space-y-5">
        <StatsSummaryStrip :items="debtStrip" />
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 items-center">
          <StatsRadialChart
            :value="utilizationPct"
            label="Cupo utilizado"
            :tone="usageTone"
            empty-title="Registra el cupo de las tarjetas para medir el uso"
          />
          <div class="lg:col-span-2">
            <p class="text-xs text-text-muted mb-2">
              % del cupo usado por tarjeta (último corte contra el cupo del catálogo).
            </p>
            <StatsBarChart
              :series="[{ name: '% del cupo', data: perCardUsage.map((card) => card.pct) }]"
              :categories="perCardUsage.map((card) => card.name)"
              horizontal
              value-format="percent"
              :colors="[palette.categorical[1]]"
              :height="Math.max(200, perCardUsage.length * 52)"
              empty-title="Sin tarjetas con cupo registrado"
            />
            <p v-if="cardsWithoutLimit.length" class="text-xs text-text-muted mt-2">
              Sin cupo registrado: {{ cardsWithoutLimit.join(', ') }}.
            </p>
          </div>
        </div>
      </div>

      <div v-else-if="tab === 'history'" class="space-y-4">
        <StatsSummaryStrip :items="debtStrip" />
        <p v-if="!sortedSnapshots.length" class="text-sm text-text-subtle py-4">
          Sin cortes registrados todavía.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-[480px] text-sm">
            <thead>
              <tr class="text-left text-xs text-text-subtle uppercase tracking-wider">
                <th class="px-3 py-2">Tarjeta</th>
                <th class="px-3 py-2">Fecha</th>
                <th class="px-3 py-2 text-right">Disponible</th>
                <th class="px-3 py-2 text-right">Deuda</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="snapshot in sortedSnapshots"
                :key="snapshot.id || `${snapshot.card_name}-${snapshot.snapshot_date}`"
                class="border-t border-border-muted"
              >
                <td class="px-3 py-2 text-text-default">{{ snapshot.card_name }}</td>
                <td class="px-3 py-2 text-text-muted text-xs whitespace-nowrap">
                  {{ snapshot.snapshot_date }}
                </td>
                <td class="px-3 py-2 text-right tabular-nums text-text-muted">
                  {{ money(snapshot.available_amount) }}
                </td>
                <td class="px-3 py-2 text-right tabular-nums font-semibold text-danger-strong">
                  {{ money(snapshot.debt_amount) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </StatsModal>
</template>

<script setup>
import { computed, ref } from 'vue';
import StatsModal from '~/components/stats/StatsModal.vue';
import StatsSummaryStrip from '~/components/stats/StatsSummaryStrip.vue';
import StatsBarChart from '~/components/stats/charts/StatsBarChart.vue';
import StatsRadialChart from '~/components/stats/charts/StatsRadialChart.vue';
import CardDebtChart from '~/components/accounting/charts/CardDebtChart.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { formatMoney } from '~/utils/formatMoney';

/** Card-debt analytics over snapshots + card_debt + the card catalog. */
const props = defineProps({
  open: { type: Boolean, default: false },
  snapshots: { type: Array, default: () => [] },
  cardDebt: { type: Object, default: null },
  creditCards: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(['close']);

const TABS = [
  { id: 'evolution', label: 'Evolución deuda' },
  { id: 'usage', label: 'Uso del cupo' },
  { id: 'history', label: 'Histórico' },
];

const activeTab = ref('evolution');

const { palette } = useChartTheme();

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

const utilizationPct = computed(() => {
  const pct = props.cardDebt?.utilization_pct;
  return pct === null || pct === undefined ? null : Number(pct);
});

const usageTone = computed(() => {
  if (utilizationPct.value === null) return 'brand';
  if (utilizationPct.value >= 85) return 'danger';
  if (utilizationPct.value >= 60) return 'warning';
  return 'success';
});

/** Latest snapshot per card name. */
const latestByCard = computed(() => {
  const byCard = new Map();
  for (const snapshot of props.snapshots) {
    const current = byCard.get(snapshot.card_name);
    if (!current || String(snapshot.snapshot_date) > String(current.snapshot_date)) {
      byCard.set(snapshot.card_name, snapshot);
    }
  }
  return byCard;
});

const perCardUsage = computed(() => {
  const rows = [];
  for (const [name, snapshot] of latestByCard.value.entries()) {
    const card = props.creditCards.find((entry) => entry.name === name);
    const limit = Number(card?.credit_limit) || 0;
    if (limit <= 0) continue;
    rows.push({
      name,
      pct: Math.round(((Number(snapshot.debt_amount) || 0) / limit) * 1000) / 10,
    });
  }
  return rows.sort((a, b) => b.pct - a.pct);
});

const cardsWithoutLimit = computed(() =>
  [...latestByCard.value.keys()].filter(
    (name) => !props.creditCards.some(
      (entry) => entry.name === name && Number(entry.credit_limit) > 0,
    ),
  ),
);

const sortedSnapshots = computed(() =>
  [...props.snapshots].sort((a, b) =>
    String(b.snapshot_date).localeCompare(String(a.snapshot_date)),
  ),
);

const debtStrip = computed(() => {
  const debt = props.cardDebt || {};
  const latestDate = sortedSnapshots.value[0]?.snapshot_date;
  return [
    { label: 'Deuda total', value: money(debt.total), tone: 'danger' },
    { label: 'Cupo total', value: money(debt.credit_limit_total) },
    {
      label: '% del cupo',
      value: utilizationPct.value === null ? '—' : `${utilizationPct.value}%`,
      tone: usageTone.value === 'brand' ? 'default' : usageTone.value,
    },
    {
      label: 'Tarjetas',
      value: String(debt.card_count ?? latestByCard.value.size),
    },
    { label: 'Último corte', value: latestDate || '—' },
  ];
});
</script>
