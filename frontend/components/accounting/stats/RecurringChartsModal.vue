<template>
  <StatsModal
    :open="open"
    title="Gráficos de pagos recurrentes"
    subtitle="Distribución del gasto recurrente, siempre en equivalente COP mensual."
    :tabs="TABS"
    :model-value="activeTab"
    size="full"
    @update:model-value="activeTab = $event"
    @close="emit('close')"
  >
    <template #default="{ activeTab: tab }">
      <div data-testid="recurring-charts-modal">
        <!-- One filter row above everything it scopes: every tab re-renders
             against the same slice, so the numbers always agree. -->
        <div
          class="flex flex-wrap items-center gap-2 pb-4 mb-4 border-b border-border-muted"
          data-testid="recurring-charts-filters"
        >
          <template v-if="inheritedChips.length">
            <span class="text-xs text-text-muted">Filtros de la tabla:</span>
            <span
              v-for="chip in inheritedChips"
              :key="chip"
              class="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-surface-raised text-xs text-text-default"
              data-testid="recurring-charts-chip"
            >{{ chip }}</span>
            <BaseButton
              variant="ghost"
              size="sm"
              data-testid="recurring-charts-clear-filters"
              @click="emit('clear-filters')"
            >
              Ver todo
            </BaseButton>
            <span class="w-px h-5 bg-border-muted mx-1" aria-hidden="true" />
          </template>

          <label class="flex items-center gap-2 text-xs text-text-muted">
            <span>Categoría</span>
            <BaseSelect
              :model-value="categoryFilter"
              :options="categoryOptions"
              size="sm"
              data-testid="recurring-charts-category"
              @update:model-value="categoryFilter = $event"
            />
          </label>

          <label class="flex items-center gap-2 text-xs text-text-muted ml-auto">
            <BaseToggle
              v-model="includeInactive"
              size="sm"
              aria-label="Incluir inactivos"
            />
            <span>Incluir inactivos</span>
          </label>

          <BaseButton
            variant="secondary"
            size="sm"
            :disabled="!activeChartId"
            data-testid="recurring-charts-download"
            @click="downloadActiveChart"
          >
            <ArrowDownTrayIcon class="w-4 h-4" />
            <span>PNG</span>
          </BaseButton>
        </div>

        <BaseEmptyState
          v-if="!chartRows.length"
          :title="emptyTitle"
          :description="emptyDescription"
        />

        <!-- Panels use v-if, never v-show: ApexCharts mounted inside a hidden
             panel measures width 0 and renders as a sliver. -->
        <template v-else>
          <div v-if="tab === 'category'" class="space-y-5">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
              <StatsDonutChart
                :labels="donutBuckets.map((bucket) => bucket.name)"
                :values="donutBuckets.map((bucket) => bucket.total)"
                :colors="donutBuckets.map((bucket) => colorFor(bucket.key))"
                :tooltip-value-formatter="categoryTooltip"
                :height="320"
                :show-legend="false"
                chart-id="recurring-chart-category"
                empty-title="Sin pagos que distribuir"
                @select="drillToDonutSlice"
              />
              <RecurringChartLegend
                :items="categoryLegend"
                :active-key="categoryFilter || null"
                clickable
                @select="toggleCategory"
              />
            </div>
            <p class="text-xs text-text-muted">
              Clic en una porción o en una fila para ver sólo esa categoría.
            </p>
          </div>

          <div v-else-if="tab === 'items'" class="space-y-4">
            <StatsBarChart
              :series="[{ name: 'Equiv. COP mensual', data: items.map((item) => item.total) }]"
              :categories="items.map((item) => item.name)"
              :colors="items.map((item) => colorFor(item.categoryId))"
              :tooltip-value-formatter="itemTooltip"
              :height="itemsChartHeight"
              horizontal
              distributed
              chart-id="recurring-chart-items"
              empty-title="Sin pagos que ordenar"
            />
            <p class="text-xs text-text-muted">
              Cada barra toma el color de su categoría. Ordenadas de mayor a menor
              costo mensual.
            </p>
          </div>

          <div v-else-if="tab === 'composition'" class="space-y-5">
            <StatsSummaryStrip :items="compositionStrip" />
            <StatsBarChart
              :series="compositionSeries"
              :categories="COMPOSITION_ROWS.map((row) => row.label)"
              :colors="[palette.categorical[0], palette.categorical[1]]"
              :tooltip-value-formatter="compositionTooltip"
              :height="220"
              horizontal
              stacked
              :show-legend="false"
              chart-id="recurring-chart-composition"
              empty-title="Sin pagos que componer"
            />
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div v-for="row in compositionRows" :key="row.field">
                <p class="text-xs text-text-muted uppercase tracking-wider mb-1">
                  {{ row.label }}
                </p>
                <RecurringChartLegend :items="row.legend" />
              </div>
            </div>
          </div>

          <div v-else-if="tab === 'calendar'" class="space-y-4">
            <StatsBarChart
              :series="[{ name: 'Equiv. COP mensual', data: calendar.days.map((day) => day.total) }]"
              :categories="calendar.days.map((day) => String(day.day))"
              :colors="[palette.categorical[0]]"
              :tooltip-value-formatter="dayTooltip"
              :height="280"
              chart-id="recurring-chart-calendar"
              empty-title="Sin cobros con día definido"
            />

            <div
              v-if="calendar.withoutDay.total > 0"
              class="rounded-xl border border-warning-strong/30 bg-warning-soft px-4 py-3"
              data-testid="recurring-charts-no-day"
            >
              <p class="text-sm font-semibold text-text-default">
                Sin día definido: {{ formatMonthlyCop(calendar.withoutDay.total) }}
                ({{ formatPercent(calendar.withoutDay.pct) }} del total)
              </p>
              <p class="text-xs text-text-muted mt-1">
                {{ calendar.withoutDay.names.join(' · ') }} — no aparecen en el
                calendario porque no tienen día de cobro. Completá el campo Día
                para verlos aquí.
              </p>
            </div>

            <p class="text-xs text-text-muted">
              Los pagos que no son mensuales aparecen prorrateados: su cuota
              mensual, no el cobro real de ese día.
            </p>
          </div>
        </template>
      </div>
    </template>
  </StatsModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { ArrowDownTrayIcon } from '@heroicons/vue/24/outline';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import BaseSelect from '~/components/base/BaseSelect.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import StatsModal from '~/components/stats/StatsModal.vue';
import StatsSummaryStrip from '~/components/stats/StatsSummaryStrip.vue';
import StatsBarChart from '~/components/stats/charts/StatsBarChart.vue';
import StatsDonutChart from '~/components/stats/charts/StatsDonutChart.vue';
import RecurringChartLegend from '~/components/accounting/stats/RecurringChartLegend.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { formatMoney } from '~/utils/formatMoney';
import { formatPercent } from '~/utils/percent';
import { formatMonthlyCop, sumMonthlyCop } from '~/utils/recurring';
import {
  byBillingDay,
  categoryColorMap,
  foldChartBuckets,
  itemsByMonthlyCost,
  splitBy,
  totalsByCategory,
  visibleRows,
} from '~/utils/recurringCharts';

/**
 * The recurring spend, seen instead of read.
 *
 * Every figure is the monthly COP equivalent, so the four tabs always add up
 * to the same total and to the "Costo mensual (COP)" card on the page behind.
 * `rows` arrives already filtered by the table, which is why the inherited
 * filters are spelled out as chips: a donut opened from the USD tab is a
 * legitimate view, but only if the reader can see why it does not match the
 * monthly total they know.
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  /** Rows as the table has them filtered. */
  rows: { type: Array, default: () => [] },
  categories: { type: Array, default: () => [] },
  /** Reference COP-per-USD rate, shown as context in the composition tab. */
  usdExchangeRate: { type: [Number, String], default: null },
  /** Human labels of the filters the table is applying, e.g. ['Moneda: USD']. */
  inheritedChips: { type: Array, default: () => [] },
});

const emit = defineEmits(['close', 'clear-filters']);

const TABS = [
  { id: 'category', label: 'Categoría' },
  { id: 'items', label: 'Ítems' },
  { id: 'composition', label: 'Composición' },
  { id: 'calendar', label: 'Calendario' },
];

const CHART_IDS = {
  category: 'recurring-chart-category',
  items: 'recurring-chart-items',
  composition: 'recurring-chart-composition',
  calendar: 'recurring-chart-calendar',
};

const COMPOSITION_ROWS = [
  { field: 'currency', label: 'Moneda' },
  { field: 'payment_method', label: 'Método' },
  { field: 'cost_type', label: 'Tipo' },
];

const activeTab = ref('category');
const categoryFilter = ref('');
const includeInactive = ref(false);

const { palette } = useChartTheme();

// Reopening starts from the tab's own view again; a category drilled into
// three sessions ago is not a filter the reader remembers setting.
watch(() => props.open, (open) => {
  if (!open) return;
  activeTab.value = 'category';
  categoryFilter.value = '';
});

const colors = computed(() =>
  categoryColorMap(props.categories, palette.value.categorical, palette.value.text),
);

function colorFor(key) {
  return colors.value.get(key) || palette.value.text;
}

const activeRows = computed(() =>
  visibleRows(props.rows, { includeInactive: includeInactive.value }),
);

const chartRows = computed(() => {
  if (!categoryFilter.value) return activeRows.value;
  return activeRows.value.filter((row) => String(row.category) === categoryFilter.value);
});

const total = computed(() => sumMonthlyCop(chartRows.value));

// -------------------------------------------------------------------
// Filters
// -------------------------------------------------------------------

const categoryOptions = computed(() => [
  { value: '', label: 'Todas' },
  ...props.categories.map((category) => ({
    value: String(category.id),
    label: category.name,
  })),
]);

function toggleCategory(key) {
  const next = String(key);
  categoryFilter.value = categoryFilter.value === next ? '' : next;
}

function drillToDonutSlice(index) {
  const bucket = donutBuckets.value[index];
  // Only real categories drill: "Sin categoría" and the folded bucket are not
  // values the category filter can express.
  if (bucket && props.categories.some((category) => category.id === bucket.id)) {
    toggleCategory(bucket.id);
  }
}

const emptyTitle = computed(() =>
  props.rows.length ? 'Nada que graficar con estos filtros' : 'Sin pagos recurrentes',
);

const emptyDescription = computed(() => {
  if (!props.rows.length) return 'Creá un pago recurrente para ver su distribución.';
  if (!activeRows.value.length) {
    return 'Los pagos que quedan están inactivos. Activá "Incluir inactivos" para verlos.';
  }
  return 'Esa categoría no tiene pagos en el conjunto filtrado.';
});

// -------------------------------------------------------------------
// Tab: categoría
// -------------------------------------------------------------------

// The legend is built off the unfiltered-by-category set, so drilling into one
// slice never hides the others: the reader keeps the whole picture, with the
// current selection highlighted.
const categoryBuckets = computed(() => totalsByCategory(activeRows.value, props.categories));

const categoryLegend = computed(() =>
  categoryBuckets.value.map((bucket) => ({
    key: bucket.key,
    label: bucket.name,
    total: bucket.total,
    pct: bucket.pct,
    color: colorFor(bucket.key),
  })),
);

const donutBuckets = computed(() =>
  foldChartBuckets(
    totalsByCategory(chartRows.value, props.categories),
    palette.value.categorical.length,
  ),
);

function categoryTooltip(value, { seriesIndex } = {}) {
  const bucket = donutBuckets.value[seriesIndex];
  if (!bucket) return formatMonthlyCop(value);
  return `${formatMonthlyCop(bucket.total)}/mes · ${formatPercent(bucket.pct)} del total`;
}

// -------------------------------------------------------------------
// Tab: ítems
// -------------------------------------------------------------------

const items = computed(() => itemsByMonthlyCost(chartRows.value));

// A fixed height would give a lone item a 100px-thick bar. Growing with the
// count keeps every bar in the same band whether there is one or twenty.
const itemsChartHeight = computed(() => Math.max(120, items.value.length * 44 + 60));

function itemTooltip(value, { dataPointIndex } = {}) {
  const item = items.value[dataPointIndex];
  if (!item) return formatMonthlyCop(value);
  const original = formatMoney(item.price, item.currency, {
    decimals: item.currency === 'COP' ? 0 : 2,
  });
  const periodicity = item.frequencyLabel ? ` ${item.frequencyLabel.toLowerCase()}` : '';
  return `${formatMonthlyCop(item.total)}/mes · ${original}${periodicity} · ${formatPercent(item.pct)} del total`;
}

// -------------------------------------------------------------------
// Tab: composición
// -------------------------------------------------------------------

const compositionRows = computed(() =>
  COMPOSITION_ROWS.map((row) => {
    const buckets = splitBy(chartRows.value, row.field);
    return {
      ...row,
      buckets,
      legend: buckets.map((bucket, index) => ({
        key: `${row.field}-${bucket.key}`,
        label: bucket.label,
        total: bucket.total,
        pct: bucket.pct,
        color: palette.value.categorical[index] || palette.value.text,
      })),
    };
  }),
);

// One stacked bar per row, two layers deep. The series carry no meaning of
// their own — "first value / second value" — which is why the chart's own
// legend is off and the three legends below name the actual buckets.
const compositionSeries = computed(() => {
  const depth = Math.max(1, ...compositionRows.value.map((row) => row.buckets.length));
  return Array.from({ length: depth }, (_, layer) => ({
    name: `Parte ${layer + 1}`,
    data: compositionRows.value.map((row) => row.buckets[layer]?.total || 0),
  }));
});

function compositionTooltip(value, { seriesIndex, dataPointIndex } = {}) {
  const bucket = compositionRows.value[dataPointIndex]?.buckets[seriesIndex];
  if (!bucket) return formatMonthlyCop(value);
  return `${bucket.label}: ${formatMonthlyCop(bucket.total)}/mes · ${formatPercent(bucket.pct)}`;
}

const usdRows = computed(() => chartRows.value.filter((row) => row.currency === 'USD'));

const compositionStrip = computed(() => {
  const usdMonthlyCop = sumMonthlyCop(usdRows.value);
  const nativeUsd = usdRows.value.reduce(
    (sum, row) => sum + (Number(row.monthly_price) || 0),
    0,
  );
  const stats = [
    { label: 'Total mensual', value: formatMonthlyCop(total.value) },
    {
      label: 'Expuesto al dólar',
      value: formatMonthlyCop(usdMonthlyCop),
      sub: `${formatPercent(percentOfTotal(usdMonthlyCop))} del gasto`,
      tone: 'brand',
    },
    // Monthly, not the sum of raw prices the page's KPI shows: adding a $200
    // monthly subscription to a $10,98 yearly domain is the apples-to-oranges
    // total this whole modal exists to avoid.
    { label: 'Nativos USD / mes', value: formatMoney(nativeUsd, 'USD', { decimals: 2 }) },
  ];
  if (props.usdExchangeRate != null) {
    stats.push({
      label: 'Tasa de referencia',
      value: `${formatMoney(Number(props.usdExchangeRate), 'COP')}/USD`,
    });
  }
  return stats;
});

function percentOfTotal(value) {
  return total.value > 0 ? (value / total.value) * 100 : 0;
}

// -------------------------------------------------------------------
// Tab: calendario
// -------------------------------------------------------------------

const calendar = computed(() => byBillingDay(chartRows.value));

function dayTooltip(value, { dataPointIndex } = {}) {
  const day = calendar.value.days[dataPointIndex];
  if (!day || !day.total) return formatMonthlyCop(value);
  const suffix = day.prorated ? ' · incluye cuotas prorrateadas' : '';
  return `${formatMonthlyCop(day.total)}/mes · ${day.names.join(', ')}${suffix}`;
}

// -------------------------------------------------------------------
// Image export
// -------------------------------------------------------------------

const activeChartId = computed(() =>
  chartRows.value.length ? CHART_IDS[activeTab.value] : '',
);

async function downloadActiveChart() {
  const apex = typeof window !== 'undefined' ? window.ApexCharts : null;
  if (!apex || !activeChartId.value) return;
  const { imgURI } = await apex.exec(activeChartId.value, 'dataURI');
  const link = document.createElement('a');
  link.download = `recurrentes-${activeTab.value}.png`;
  link.href = imgURI;
  link.click();
}
</script>
