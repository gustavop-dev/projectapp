<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Contabilidad — Resumen</h1>
        <p class="text-sm text-text-subtle mt-1">
          Panorama financiero anual: ingresos, gastos, utilidades y saldos.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <BaseSelect
          :model-value="String(store.selectedYear)"
          :options="yearOptions"
          class="w-28"
          data-testid="accounting-year-select"
          @update:model-value="onYearChange"
        />
        <BaseButton
          variant="secondary"
          size="md"
          :disabled="isExportingWorkbook"
          data-testid="accounting-export-workbook-button"
          @click="exportWorkbook"
        >
          <ArrowDownTrayIcon class="w-4 h-4" />
          <span>{{ isExportingWorkbook ? 'Exportando...' : 'Exportar Excel' }}</span>
        </BaseButton>
        <BaseButton
          variant="primary"
          size="md"
          data-testid="accounting-new-income-button"
          @click="openIncomeModal"
        >
          <PlusIcon class="w-4 h-4" />
          <span>Nuevo ingreso</span>
        </BaseButton>
      </div>
    </div>

    <AccountingSubnav active="index" />

    <!-- Loading -->
    <div v-if="store.isLoading && !summary" class="text-center py-16 text-text-muted text-sm">
      Cargando resumen contable...
    </div>

    <template v-else-if="summary">
      <!-- Row 1: totals -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <AccountingStatCard
          label="Ingresos esperados"
          :value="money(summary.expected_total)"
        />
        <AccountingStatCard
          label="Ingresos líquidos"
          :value="money(summary.liquid_total)"
          :sub="receivedPct"
        />
        <AccountingStatCard label="Gastos" :value="money(summary.expenses_total)" />
        <AccountingStatCard
          label="Bolsillo ProjectApp"
          :value="money(summary.pocket_balance)"
          tone="brand"
        />
      </div>

      <!-- Row 2: utilities -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <AccountingStatCard
          label="Utilidad esperada"
          :value="money(summary.expected_utility)"
          :tone="toneBySign(summary.expected_utility)"
        />
        <AccountingStatCard
          label="Utilidad líquida"
          :value="money(summary.liquid_utility)"
          :tone="toneBySign(summary.liquid_utility)"
        />
      </div>

      <!-- Row 3: partners -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        <div
          v-for="partner in partnerCards"
          :key="partner.key"
          :data-testid="`accounting-partner-card-${partner.key}`"
          class="bg-surface rounded-xl border border-border-muted shadow-sm p-4 sm:p-5"
        >
          <p class="text-xs text-text-muted uppercase tracking-wider mb-3">{{ partner.label }}</p>
          <dl class="space-y-1.5 text-sm">
            <div class="flex items-center justify-between">
              <dt class="text-text-muted">Esperado</dt>
              <dd class="tabular-nums text-text-default">{{ money(partner.data.expected) }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="text-text-muted">Líquido</dt>
              <dd class="tabular-nums text-text-default">{{ money(partner.data.liquid) }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="text-text-muted">Gastos</dt>
              <dd class="tabular-nums text-text-default">{{ money(partner.data.expenses) }}</dd>
            </div>
            <div
              v-if="hasPersonalActivity(partner.data)"
              class="text-xs text-text-subtle pt-1"
            >
              Participación empresa: {{ money(partner.data.participation?.liquid) }} líquido ·
              Personal: {{ money(partner.data.personal?.liquid) }} líquido /
              {{ money(partner.data.personal?.expenses) }} gastos
            </div>
            <div class="flex items-center justify-between pt-1.5 border-t border-border-muted">
              <dt class="font-medium text-text-default">Neto</dt>
              <dd
                class="tabular-nums font-semibold"
                :class="Number(partner.data.net) < 0 ? 'text-danger-strong' : 'text-success-strong'"
              >
                {{ money(partner.data.net) }}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Row 4: monthly table -->
      <div class="mb-6">
        <h2 class="text-sm font-semibold text-text-subtle uppercase tracking-wider mb-2">
          Detalle mensual {{ summary.year }}
        </h2>
        <AccountingMonthlyTable :monthly="summary.monthly || []" />
      </div>

      <!-- Row 4.5: evolution charts -->
      <div class="mb-6">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-2">
          <h2 class="text-sm font-semibold text-text-subtle uppercase tracking-wider">
            Evolución {{ summary.year }}
          </h2>
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Meses</span>
            <BaseSelect
              :model-value="String(monthFrom)"
              :options="monthOptions"
              class="w-32"
              data-testid="accounting-month-from"
              @update:model-value="onMonthFromChange"
            />
            <span class="text-text-subtle text-xs">—</span>
            <BaseSelect
              :model-value="String(monthTo)"
              :options="monthOptions"
              class="w-32"
              data-testid="accounting-month-to"
              @update:model-value="onMonthToChange"
            />
          </div>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <AccountingMonthlyChart
            :monthly="summary.monthly || []"
            :month-from="monthFrom"
            :month-to="monthTo"
          />
          <CardDebtChart
            :snapshots="store.cardSnapshots"
            :month-from="monthFrom"
            :month-to="monthTo"
          />
        </div>
      </div>

      <!-- Row 5: operative cards -->
      <div class="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        <AccountingStatCard
          label="Costo operativo mensual"
          :value="money(summary.recurring_monthly_cost)"
          sub="Pagos recurrentes activos"
        />
        <AccountingStatCard
          label="Ads del año"
          :value="money(summary.ads?.year_total)"
          :sub="`Mes actual: ${money(summary.ads?.current_month_total)}`"
        />
        <AccountingStatCard
          label="Hostings activos"
          :value="String(Number(summary.hostings?.active_count ?? 0))"
          :sub="`Ingreso mensual: ${money(summary.hostings?.monthly_income)}`"
        />
      </div>

      <!-- Card snapshots -->
      <div v-if="(summary.latest_card_snapshots || []).length > 0" class="mb-6">
        <div class="flex items-center justify-between gap-3 mb-2">
          <h2 class="text-sm font-semibold text-text-subtle uppercase tracking-wider">
            Tarjetas
          </h2>
          <NuxtLink
            :to="localePath('/panel/accounting/cards')"
            class="text-xs text-text-brand hover:underline"
            data-testid="accounting-cards-link"
          >
            Ver historial de tarjetas →
          </NuxtLink>
        </div>
        <div class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm">
          <table class="w-full min-w-[500px] text-sm">
            <thead>
              <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                <th class="px-5 py-3">Tarjeta</th>
                <th class="px-4 py-3">Fecha</th>
                <th class="px-4 py-3 text-right">Disponible</th>
                <th class="px-4 py-3 text-right">Deuda</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border-muted">
              <tr
                v-for="snapshot in summary.latest_card_snapshots"
                :key="snapshot.card_name"
                class="hover:bg-surface-raised transition-colors bg-surface"
              >
                <td class="px-5 py-3 font-medium text-text-default">{{ snapshot.card_name }}</td>
                <td class="px-4 py-3 text-text-muted text-xs">{{ snapshot.snapshot_date }}</td>
                <td class="px-4 py-3 text-right tabular-nums text-text-muted">
                  {{ money(snapshot.available_amount) }}
                </td>
                <td class="px-4 py-3 text-right tabular-nums text-danger-strong">
                  {{ money(snapshot.debt_amount) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Empty / error -->
    <div v-else class="text-center py-16 text-text-subtle text-sm">
      No hay datos del resumen contable para mostrar.
    </div>

    <!-- New income modal -->
    <IncomeFormModal
      :open="showIncomeModal"
      :saving="store.isUpdating"
      @close="showIncomeModal = false"
      @submit="submitIncome"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { ArrowDownTrayIcon, PlusIcon } from '@heroicons/vue/24/outline';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import AccountingMonthlyTable from '~/components/accounting/AccountingMonthlyTable.vue';
import AccountingMonthlyChart from '~/components/accounting/charts/AccountingMonthlyChart.vue';
import CardDebtChart from '~/components/accounting/charts/CardDebtChart.vue';
import IncomeFormModal from '~/components/accounting/IncomeFormModal.vue';
import BaseSelect from '~/components/base/BaseSelect.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingStore } from '~/stores/accounting';
import { get_request } from '~/stores/services/request_http';
import { downloadBlob, filenameFromDisposition } from '~/utils/downloadFile';
import { formatMoney } from '~/utils/formatMoney';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const store = useAccountingStore();
const notify = usePanelNotify();

const summary = computed(() => store.summary);

const yearOptions = computed(() => {
  const maxYear = new Date().getFullYear() + 1;
  const options = [];
  for (let year = 2025; year <= maxYear; year++) {
    options.push({ value: String(year), label: String(year) });
  }
  return options;
});

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

function toneBySign(value) {
  return Number(value) < 0 ? 'danger' : 'success';
}

const receivedPct = computed(() => {
  const expected = Number(summary.value?.expected_total);
  const liquid = Number(summary.value?.liquid_total);
  if (!expected || expected <= 0) return '';
  return `${Math.round((liquid / expected) * 100)}% recibido`;
});

const partnerCards = computed(() => {
  const partners = summary.value?.partners || {};
  const empty = { expected: 0, liquid: 0, expenses: 0, net: 0 };
  return [
    { key: 'gustavo', label: 'Gustavo', data: partners.gustavo || empty },
    { key: 'carlos', label: 'Carlos', data: partners.carlos || empty },
    { key: 'company', label: 'ProjectApp (Empresa)', data: partners.company || empty },
  ];
});

function hasPersonalActivity(data) {
  const personal = data?.personal;
  if (!personal) return false;
  return Number(personal.liquid) !== 0 || Number(personal.expenses) !== 0
    || Number(personal.expected) !== 0;
}

async function loadSummary(year) {
  const result = await store.fetchSummary(year || store.selectedYear);
  if (!result.success) {
    notify.error({ title: 'No se pudo cargar el resumen contable', detail: result.message });
  }
}

async function loadCardSnapshots() {
  await store.fetchRecords('cards', { year: store.selectedYear });
}

function syncYearQueryParam() {
  const query = { ...route.query, year: String(store.selectedYear) };
  router.replace({ query });
}

function onYearChange(value) {
  loadSummary(Number(value)).then(() => {
    syncYearQueryParam();
    loadCardSnapshots();
  });
}

// -------------------------------------------------------------------
// Evolution charts: month range applied client-side to both charts
// -------------------------------------------------------------------

const MONTH_LABELS = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const monthOptions = MONTH_LABELS.map((label, index) => ({
  value: String(index + 1),
  label,
}));

const monthFrom = ref(1);
const monthTo = ref(12);

function onMonthFromChange(value) {
  monthFrom.value = Number(value);
  if (monthFrom.value > monthTo.value) monthTo.value = monthFrom.value;
}

function onMonthToChange(value) {
  monthTo.value = Number(value);
  if (monthTo.value < monthFrom.value) monthFrom.value = monthTo.value;
}

// -------------------------------------------------------------------
// Full workbook export (summary sheet + one sheet per section)
// -------------------------------------------------------------------

const isExportingWorkbook = ref(false);

async function exportWorkbook() {
  if (isExportingWorkbook.value) return;
  isExportingWorkbook.value = true;
  try {
    const response = await get_request(
      `accounting/export/workbook/?year=${store.selectedYear}`,
      { responseType: 'blob' },
    );
    const filename = filenameFromDisposition(
      response.headers?.['content-disposition'],
    ) || `contabilidad_projectapp_${store.selectedYear}.xlsx`;
    downloadBlob(response.data, filename);
  } catch (error) {
    notify.error({
      title: 'No se pudo exportar el Excel',
      detail: 'Intenta de nuevo en unos segundos.',
    });
  } finally {
    isExportingWorkbook.value = false;
  }
}

// -------------------------------------------------------------------
// New income modal
// -------------------------------------------------------------------

const showIncomeModal = ref(false);

function openIncomeModal() {
  showIncomeModal.value = true;
}

async function submitIncome(payload) {
  const result = await store.createRecord('incomes', payload);
  if (result.success) {
    showIncomeModal.value = false;
    notify.success('Ingreso creado');
    await loadSummary(store.selectedYear);
  } else {
    notify.error({ title: 'No se pudo crear el ingreso', detail: result.message });
  }
}

onMounted(() => {
  const queryYear = Number(route.query.year);
  if (Number.isInteger(queryYear) && queryYear >= 2000) {
    store.selectedYear = queryYear;
  }
  loadSummary();
  loadCardSnapshots();
});
usePanelRefresh(() => {
  loadSummary(store.selectedYear);
  loadCardSnapshots();
});
</script>
