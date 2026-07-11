<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Cobros</h1>
        <p class="text-sm text-text-subtle mt-1">
          Cuentas de cobro enviadas a clientes: hosting hoy, otros orígenes a futuro.
        </p>
      </div>
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
      description="Envía la primera desde el tab Hostings con la acción 'Enviar cuenta de cobro'."
    />

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :loading="store.isLoading"
        :columns="columns"
        :rows="sortedRows"
        :show-actions="false"
        :sort-key="sortKey"
        :sort-dir="sortDir"
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
            <button
              v-if="row.commercial_status === 'draft' || row.commercial_status === 'issued'"
              type="button"
              aria-label="Anular"
              title="Anular"
              :disabled="busyId === row.id"
              class="p-2 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors disabled:opacity-50"
              @click="askCancel(row)"
            >
              <NoSymbolIcon class="w-5 h-5" />
            </button>
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
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import {
  CheckCircleIcon,
  DocumentArrowDownIcon,
  NoSymbolIcon,
  PaperAirplaneIcon,
} from '@heroicons/vue/24/outline';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
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

function askMarkPaid(row) {
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
