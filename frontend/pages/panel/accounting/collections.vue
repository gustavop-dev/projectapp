<template>
  <div :class="PAGE_MAX_WIDTH">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Cuentas de cobro</h1>
        <p class="text-sm text-text-subtle mt-1">
          Crea, envía y da seguimiento a las cuentas de cobro: desde aquí, desde un ingreso o desde Hostings.
        </p>
      </div>
      <BaseButton
        variant="primary"
        data-testid="collection-create-button"
        @click="openCreateModal"
      >
        Nueva cuenta de cobro
      </BaseButton>
    </div>

    <AccountingSubnav active="collections" />

    <!-- Status counters -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
      <AccountingStatCard
        label="Emitidas"
        :value="String(meta.issued_count ?? 0)"
        :sub="`Por cobrar: ${money(meta.issued_total)}`"
        tone="brand"
      />
      <AccountingStatCard
        label="Pagadas"
        :value="String(meta.paid_count ?? 0)"
        :sub="`Recaudado: ${money(meta.paid_total)}`"
        tone="success"
      />
      <AccountingStatCard
        label="Vencidas"
        :value="String(overdueCount)"
        :tone="overdueCount > 0 ? 'warning' : 'default'"
        sub="Emitidas con fecha límite pasada"
      />
      <AccountingStatCard
        label="Anuladas"
        :value="String(meta.cancelled_count ?? 0)"
      />
    </div>

    <!-- Status filter -->
    <div class="mb-5">
      <BaseSegmented v-model="statusFilter" :options="statusOptions" />
    </div>

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'fetch_failed'"
      title="No se pudieron cargar las cuentas de cobro"
      :retrying="store.isLoading"
      @retry="loadRecords"
    />

    <!-- Empty -->
    <BaseEmptyState
      v-else-if="!store.isLoading && filteredRows.length === 0"
      title="Sin cuentas de cobro"
      description="Crea la primera con 'Nueva cuenta de cobro', desde un ingreso en el tab Ingresos, o desde Hostings con 'Enviar cuenta de cobro'."
    >
      <BaseButton variant="primary" data-testid="collection-empty-create" @click="openCreateModal">
        Nueva cuenta de cobro
      </BaseButton>
    </BaseEmptyState>

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :loading="store.isLoading"
        :columns="columns"
        :rows="sortedRows"
        :show-actions="false"
        :sort-key="sortKey"
        :sort-dir="sortDir"
        :highlight-id="highlightId"
        @sort="toggleSort"
      >
        <template #cell-public_number="{ row }">
          <span class="font-medium text-text-default">{{ row.public_number || `#${row.id}` }}</span>
        </template>
        <template #cell-commercial_status="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="statusBadgeClass(row)"
          >
            {{ row.is_overdue ? 'Vencida' : row.commercial_status_label }}
          </span>
        </template>
        <template #cell-row_actions="{ row }">
          <div class="flex items-center justify-end gap-1">
            <BaseButton
              v-if="row.income_record_id"
              variant="ghost"
              icon-only
              size="sm"
              aria-label="Ver ingreso"
              title="Ver ingreso vinculado"
              :data-testid="`collection-view-income-${row.id}`"
              @click="goToIncome(row)"
            >
              <ArrowTopRightOnSquareIcon class="w-5 h-5" />
            </BaseButton>
            <button
              type="button"
              aria-label="Ver PDF"
              title="Ver PDF"
              class="p-2 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors"
              @click="downloadPdf(row)"
            >
              <DocumentArrowDownIcon class="w-5 h-5" />
            </button>
            <button
              v-if="row.commercial_status === 'issued' || row.commercial_status === 'paid'"
              type="button"
              aria-label="Reenviar al cliente"
              title="Reenviar al cliente"
              :disabled="busyId === row.id"
              class="p-2 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors disabled:opacity-50"
              @click="resend(row)"
            >
              <PaperAirplaneIcon class="w-5 h-5" />
            </button>
            <button
              v-if="row.commercial_status === 'issued'"
              type="button"
              aria-label="Marcar pagada"
              title="Marcar pagada"
              :disabled="busyId === row.id"
              class="p-2 rounded-lg text-text-subtle hover:text-success-strong hover:bg-success-soft transition-colors disabled:opacity-50"
              @click="askMarkPaid(row)"
            >
              <CheckCircleIcon class="w-5 h-5" />
            </button>
            <BaseButton variant="danger-ghost" icon-only size="sm" v-if="row.commercial_status === 'draft' || row.commercial_status === 'issued'" aria-label="Anular" title="Anular" :disabled="busyId === row.id" @click="askCancel(row)">
              <NoSymbolIcon class="w-5 h-5" />
            </BaseButton>
          </div>
        </template>
      </AccountingTable>
    </template>

    <ConfirmModal
      v-model="confirmOpen"
      :title="confirmTitle"
      :message="confirmMessage"
      :confirm-text="confirmText"
      cancel-text="Cancelar"
      :variant="confirmVariant"
      @confirm="handleConfirmed"
      @cancel="pendingAction = null"
    />

    <!-- Create modal: form → preview del correo/PDF → confirmar y enviar -->
    <CollectionAccountFormModal
      :open="createOpen"
      @close="createOpen = false"
      @created="onCreated"
    />

    <!-- Marking an expected-linked cuenta as paid routes through Liquidar:
         settling the income is what flips the cuenta (backend sync). -->
    <IncomeLiquidateModal
      :open="liquidateOpen"
      :record="liquidatingIncome"
      :saving="store.isUpdating"
      @close="closeLiquidate"
      @submit="handleLiquidateSubmit"
    />
  </div>
</template>

<script setup>
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';
import { computed, onMounted, ref } from 'vue';
import {
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  DocumentArrowDownIcon,
  NoSymbolIcon,
  PaperAirplaneIcon,
} from '@heroicons/vue/24/outline';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import CollectionAccountFormModal from '~/components/accounting/CollectionAccountFormModal.vue';
import IncomeLiquidateModal from '~/components/accounting/IncomeLiquidateModal.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useTableSort } from '~/composables/useTableSort';
import { useAccountingStore } from '~/stores/accounting';
import { get_request } from '~/stores/services/request_http';
import { downloadBlob, filenameFromDisposition } from '~/utils/downloadFile';
import { formatMoney } from '~/utils/formatMoney';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();
const route = useRoute();

// ?focus=<id> flashes a row (bidirectional navigation from Ingresos).
const highlightId = ref(route.query.focus ? Number(route.query.focus) : null);

const meta = computed(() => store.collectionAccountsMeta || {});

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

const statusFilter = ref('');
const statusOptions = [
  { value: '', label: 'Todas' },
  { value: 'issued', label: 'Emitidas' },
  { value: 'overdue', label: 'Vencidas' },
  { value: 'paid', label: 'Pagadas' },
  { value: 'cancelled', label: 'Anuladas' },
];

const filteredRows = computed(() => {
  const rows = store.collectionAccounts;
  if (!statusFilter.value) return rows;
  if (statusFilter.value === 'overdue') return rows.filter((row) => row.is_overdue);
  return rows.filter((row) => row.commercial_status === statusFilter.value);
});

const overdueCount = computed(
  () => store.collectionAccounts.filter((row) => row.is_overdue).length,
);

const columns = [
  { key: 'public_number', label: 'Número' },
  { key: 'origin_label', label: 'Origen' },
  { key: 'customer_name', label: 'Cliente' },
  { key: 'total', label: 'Total', format: 'money', sortable: true },
  { key: 'issue_date', label: 'Emisión', format: 'date', sortable: true },
  { key: 'due_date', label: 'Vence', format: 'date', sortable: true },
  { key: 'commercial_status', label: 'Estado' },
  { key: 'row_actions', label: '', align: 'right' },
];

const { sortKey, sortDir, toggleSort, sortedRecords: sortedRows } = useTableSort(
  filteredRows,
  { sortDefaults: { total: 'desc', issue_date: 'desc', due_date: 'desc' } },
);

function statusBadgeClass(row) {
  if (row.is_overdue) return 'bg-warning-soft text-warning-strong';
  return {
    draft: 'bg-surface-raised text-text-muted',
    issued: 'bg-info-soft text-info-strong',
    paid: 'bg-success-soft text-success-strong',
    cancelled: 'bg-danger-soft text-danger-strong',
  }[row.commercial_status] || 'bg-surface-raised text-text-muted';
}

async function loadRecords() {
  await store.fetchCollectionAccounts();
}

// ── Row actions ──

const busyId = ref(null);

async function downloadPdf(row) {
  try {
    const response = await get_request(
      `accounting/collection-accounts/${row.id}/pdf/`,
      { responseType: 'blob' },
    );
    const filename =
      filenameFromDisposition(response.headers?.['content-disposition'])
      || `${row.public_number || row.id}.pdf`;
    downloadBlob(response.data, filename);
  } catch (error) {
    notify.error({ title: 'No se pudo descargar el PDF' });
    console.error('Error downloading collection account PDF:', error);
  }
}

async function resend(row) {
  busyId.value = row.id;
  const result = await store.resendCollectionAccount(row.id);
  busyId.value = null;
  if (result.success) {
    notify.success({ title: 'Cuenta de cobro reenviada al cliente' });
  } else {
    notify.error({ title: 'No se pudo reenviar', detail: result.message });
  }
}

const confirmOpen = ref(false);
const pendingAction = ref(null);

const confirmTitle = computed(() =>
  pendingAction.value?.kind === 'paid' ? 'Marcar como pagada' : 'Anular cuenta de cobro',
);
const confirmText = computed(() =>
  pendingAction.value?.kind === 'paid' ? 'Marcar pagada' : 'Anular',
);
const confirmVariant = computed(() =>
  pendingAction.value?.kind === 'paid' ? 'primary' : 'danger',
);
const confirmMessage = computed(() => {
  const row = pendingAction.value?.row;
  if (!row) return '';
  const number = row.public_number || `#${row.id}`;
  return pendingAction.value.kind === 'paid'
    ? `Se marcará la cuenta ${number} como pagada.`
    : `Se anulará la cuenta ${number}. Si viene de un hosting, los avisos de vencimiento se reactivan.`;
});

// ── Create modal ──

const createOpen = ref(false);

function openCreateModal() {
  createOpen.value = true;
}

function onCreated() {
  createOpen.value = false;
  loadRecords();
}

// ── Bidirectional navigation ──

function goToIncome(row) {
  navigateTo({
    path: '/panel/accounting/incomes',
    query: { focus: row.income_record_id },
  });
}

// ── Mark paid: expected-linked cuentas route through Liquidar ──

const liquidateOpen = ref(false);
const liquidatingIncome = ref(null);

function closeLiquidate() {
  liquidateOpen.value = false;
  liquidatingIncome.value = null;
}

async function handleLiquidateSubmit(payload) {
  const incomeId = liquidatingIncome.value?.id;
  const result = await store.settleIncome(incomeId, payload);
  if (result.success) {
    closeLiquidate();
    notify.success({
      title: 'Ingreso liquidado',
      detail: 'Si el ingreso quedó pagado al 100%, la cuenta pasó a Pagada.',
    });
    loadRecords();
  } else {
    notify.error({ title: 'No se pudo liquidar', detail: result.message });
  }
}

async function askMarkPaid(row) {
  // Never settle silently: an expected income with pending balance goes
  // through the Liquidar modal; the backend sync marks the cuenta paid.
  if (row.income_record_id) {
    try {
      const response = await get_request(
        `accounting/incomes/${row.income_record_id}/`,
      );
      const income = response.data;
      if (income?.kind === 'expected' && income?.payment_status !== 'paid') {
        liquidatingIncome.value = income;
        liquidateOpen.value = true;
        return;
      }
    } catch (error) {
      console.error('Error fetching linked income:', error);
    }
  }
  pendingAction.value = { kind: 'paid', row };
  confirmOpen.value = true;
}

function askCancel(row) {
  pendingAction.value = { kind: 'cancel', row };
  confirmOpen.value = true;
}

async function handleConfirmed() {
  const action = pendingAction.value;
  pendingAction.value = null;
  if (!action) return;
  busyId.value = action.row.id;
  const result = action.kind === 'paid'
    ? await store.markCollectionAccountPaid(action.row.id)
    : await store.cancelCollectionAccount(action.row.id);
  busyId.value = null;
  if (result.success) {
    notify.success({
      title: action.kind === 'paid' ? 'Cuenta marcada como pagada' : 'Cuenta anulada',
    });
    loadRecords();
  } else {
    notify.error({ title: 'No se pudo completar la acción', detail: result.message });
  }
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
