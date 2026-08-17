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

    <!-- Quick + saved filter tabs -->
    <ProposalFilterTabs
      :tabs="displayTabs"
      :active-tab-id="filterTabId"
      :is-tab-limit-reached="isTabLimitReached"
      @select="selectFilterTab"
      @create="handleCreateFilterTab"
      @rename="renameFilterTab"
      @delete="deleteFilterTab"
      @restore="restoreFilterTab"
      @rebase="rebaseFilterTab"
    />

    <!-- Search + filter toggle -->
    <div class="flex items-center gap-2 mb-5">
      <BaseInput
        v-model="searchInput"
        type="text"
        placeholder="Buscar por número, cliente, proyecto o concepto..."
        data-testid="collections-search-input"
        class="w-full sm:max-w-xs"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <!-- The status bar stays out of the panel: it is the day-to-day
           control and the panel is collapsed by default. -->
      <BaseSegmented
        v-model="currentFilters.status"
        :options="statusOptions"
        size="sm"
        class="ml-auto"
      />
    </div>

    <!-- Filter panel -->
    <AccountingFilterPanel
      :fields="filterFields"
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :results-count="filteredRows.length"
      :search-value="currentFilters.search"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
      @clear-search="searchInput = ''"
    />

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
      :title="hasActiveFilters ? 'Sin resultados con esos filtros' : 'Sin cuentas de cobro'"
      :description="hasActiveFilters
        ? 'Ajusta o limpia los filtros para ver más registros.'
        : `Crea la primera con 'Nueva cuenta de cobro', desde un ingreso en el tab Ingresos, o desde Hostings con 'Enviar cuenta de cobro'.`"
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
        <!-- El número es la dirección del detalle: un enlace de verdad, no sólo
             el ojo de la columna de acciones. -->
        <template #cell-public_number="{ row }">
          <BaseRowLink
            :to="accountDetailTo(row.id)"
            stretch
            :data-testid="`collection-open-${row.id}`"
            class="block font-medium text-text-default hover:text-text-brand transition-colors"
            :title="row.billing_concept"
          >
            {{ row.public_number || `#${row.id}` }}
          </BaseRowLink>
        </template>
        <template #cell-origin="{ row }">
          <span
            class="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase tracking-wider"
            :class="originTone(row.origin)"
          >
            {{ originLabel(row.origin) }}
          </span>
        </template>
        <template #cell-client_display_name="{ row }">
          <span class="inline-flex items-center gap-1.5">
            <span class="text-text-default">
              {{ row.client_display_name || row.customer_name || '—' }}
            </span>
            <span
              v-if="!row.client"
              class="text-[10px] px-1.5 py-0.5 rounded-full bg-warning-soft text-warning-strong"
              title="Sin cliente vinculado — el nombre viene del documento emitido"
              :data-testid="`collection-unlinked-${row.id}`"
            >
              sin vincular
            </span>
          </span>
        </template>
        <template #cell-project_name="{ row }">
          <span v-if="row.project_name" class="inline-flex items-center gap-1 text-text-default">
            {{ row.project_name }}
            <!-- Only documents whose live FK survives get the jump; older
                 rows keep the frozen snapshot text with no link (by design). -->
            <ProjectSpaceLink
              :project-id="row.project_id"
              :data-testid="`collection-project-space-${row.id}`"
            />
          </span>
          <!-- Empty is a legitimate state here (a cobro por diagnóstico has
               no project yet), so it gets no debt pill — unlike the client. -->
          <span
            v-else
            class="text-text-subtle"
            title="Sin proyecto — típico de un cobro por diagnóstico"
            :data-testid="`collection-no-project-${row.id}`"
          >—</span>
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
              variant="ghost"
              icon-only
              size="sm"
              aria-label="Ver detalle"
              title="Ver detalle"
              :data-testid="`collection-view-detail-${row.id}`"
              @click="openDetail(row)"
            >
              <EyeIcon class="w-5 h-5" />
            </BaseButton>
            <BaseButton
              v-if="row.notes"
              variant="ghost"
              icon-only
              size="sm"
              aria-label="Ver notas internas"
              title="Notas internas"
              :data-testid="`collection-notes-${row.id}`"
              @click="notesRow = row"
            >
              <ChatBubbleBottomCenterTextIcon class="w-5 h-5" />
            </BaseButton>
            <BaseButton
              variant="ghost"
              icon-only
              size="sm"
              aria-label="Descargar PDF"
              title="Descargar PDF"
              :disabled="busyId === row.id"
              :data-testid="`collection-download-pdf-${row.id}`"
              @click="downloadPdf(row)"
            >
              <DocumentArrowDownIcon class="w-5 h-5" />
            </BaseButton>
            <BaseButton
              variant="ghost"
              icon-only
              size="sm"
              aria-label="Ver correos de esta cuenta"
              title="Ver qué correos salieron por esta cuenta de cobro"
              :data-testid="`collection-emails-${row.id}`"
              @click="goToCollectionEmails(row)"
            >
              <EnvelopeIcon class="w-5 h-5" />
            </BaseButton>
            <BaseButton
              v-if="row.commercial_status === 'issued' || row.commercial_status === 'paid'"
              variant="ghost"
              icon-only
              size="sm"
              aria-label="Reenviar al cliente"
              title="Reenviar al cliente"
              :disabled="busyId === row.id"
              @click="askResend(row)"
            >
              <PaperAirplaneIcon class="w-5 h-5" />
            </BaseButton>
            <BaseButton
              v-if="row.commercial_status === 'issued'"
              variant="ghost"
              icon-only
              size="sm"
              aria-label="Marcar pagada"
              :title="row.income_kind === 'expected' ? 'Registrar pago (liquidar)' : 'Marcar pagada'"
              :disabled="busyId === row.id"
              @click="askMarkPaid(row)"
            >
              <CheckCircleIcon class="w-5 h-5" />
            </BaseButton>
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

    <!-- Internal notes, read-only: written in the create form, never sent. -->
    <BaseModal v-model="notesOpen" size="lg" @close="notesRow = null">
      <div class="p-6 space-y-3">
        <h3 class="text-lg font-bold text-text-default">
          Notas internas · {{ notesRow?.public_number || `#${notesRow?.id}` }}
        </h3>
        <p class="text-xs text-text-subtle">
          Sólo para ti: no se muestran al cliente ni viajan en el PDF o el correo.
        </p>
        <p
          class="text-sm text-text-default whitespace-pre-line"
          data-testid="collection-notes-body"
        >
          {{ notesRow?.notes }}
        </p>
        <div class="flex justify-end pt-2">
          <BaseButton variant="secondary" @click="notesRow = null">Cerrar</BaseButton>
        </div>
      </div>
    </BaseModal>

    <!-- Create modal: form → preview del correo/PDF → confirmar y enviar -->
    <CollectionAccountFormModal
      :open="createOpen"
      @close="createOpen = false"
      @created="onCreated"
    />

    <!-- Detalle: el ingreso vinculado y el documento, sin salir del tab -->
    <CollectionAccountDetailModal
      :open="detailOpen"
      :record="detailRow"
      @close="closeDetail"
      @download="downloadPdf"
      @go-to-income="goToIncome"
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
  ChatBubbleBottomCenterTextIcon,
  CheckCircleIcon,
  DocumentArrowDownIcon,
  EnvelopeIcon,
  EyeIcon,
  NoSymbolIcon,
  PaperAirplaneIcon,
} from '@heroicons/vue/24/outline';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import CollectionAccountFormModal from '~/components/accounting/CollectionAccountFormModal.vue';
import CollectionAccountDetailModal from '~/components/accounting/CollectionAccountDetailModal.vue';
import IncomeLiquidateModal from '~/components/accounting/IncomeLiquidateModal.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import ProjectSpaceLink from '~/components/panel/projects/ProjectSpaceLink.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import {
  useAccountingFilters,
  matchDateRange,
  matchNumberRange,
} from '~/composables/useAccountingFilters';
import { useTableSort } from '~/composables/useTableSort';
import { useDetailQueryParam } from '~/composables/useDetailQueryParam';
import { useAccountingStore } from '~/stores/accounting';
import { usePanelProjectsStore } from '~/stores/panel_projects';
import { get_request } from '~/stores/services/request_http';
import { downloadBlob, filenameFromDisposition } from '~/utils/downloadFile';
import { formatMoney } from '~/utils/formatMoney';
import { historySendsLink } from '~/utils/historyDeepLink';
import { originLabel, originTone, statusBadgeClass } from '~/utils/collectionStatus';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const projectsStore = usePanelProjectsStore();
const notify = usePanelNotify();

const meta = computed(() => store.collectionAccountsMeta || {});

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

const statusOptions = [
  { value: '', label: 'Todas' },
  { value: 'issued', label: 'Emitidas' },
  { value: 'overdue', label: 'Vencidas' },
  { value: 'paid', label: 'Pagadas' },
  { value: 'cancelled', label: 'Anuladas' },
];

const NO_CLIENT_KEY = 'none';
const NO_PROJECT_KEY = 'none';

const matchClients = (record, value) => {
  if (!Array.isArray(value) || value.length === 0) return true;
  if (record.client == null) return value.includes(NO_CLIENT_KEY);
  return value.includes(record.client);
};
matchClients.keys = ['clients'];

// The live FK is the filter key — same contract as hostings/incomes, so one
// project id selects the same work everywhere. The frozen snapshot name only
// answers for legacy rows whose project was deleted (SET_NULL); a row with
// neither never had a project. The CELL follows the same rule since F7:
// `project_name` arrives live from the FK (snapshot only as FK-null
// fallback), so cell and filter can no longer contradict each other. The
// frozen snapshot stays the PDF's truth, untouched.
const matchProjects = (record, value) => {
  if (!Array.isArray(value) || value.length === 0) return true;
  if (record.project_id != null) return value.includes(record.project_id);
  if (record.project_name) return value.includes(record.project_name);
  return value.includes(NO_PROJECT_KEY);
};
matchProjects.keys = ['projects'];

// `overdue` is a computed serializer field, not a commercial_status value,
// so matchEquals cannot express it.
const matchCommercialStatus = (record, value) => {
  if (!value) return true;
  if (value === 'overdue') return Boolean(record.is_overdue);
  return record.commercial_status === value;
};
matchCommercialStatus.keys = ['status'];

const {
  currentFilters,
  searchInput,
  displayTabs,
  activeTabId: filterTabId,
  isFilterPanelOpen,
  hasActiveFilters,
  activeFilterCount,
  isTabLimitReached,
  applyFilters,
  resetFilters,
  selectTab: selectFilterTab,
  saveTab,
  deleteTab: deleteFilterTab,
  renameTab: renameFilterTab,
  restoreTab: restoreFilterTab,
  rebaseTab: rebaseFilterTab,
  consumeParam,
} = useAccountingFilters({
  viewName: 'accounting_collections',
  ephemeralParams: ['focus'],
  builtinTabs: [
    { id: 'open', name: 'Por cobrar', filters: { status: 'issued' } },
    { id: 'overdue', name: 'Vencidas', filters: { status: 'overdue' } },
    { id: 'no-project', name: 'Sin proyecto', filters: { projects: [NO_PROJECT_KEY] } },
  ],
  // 'all', never a narrowing builtin: this is the page other tabs deep-link
  // INTO, and Ingresos landing on its own builtin is exactly what made a
  // focused row arrive filtered out of its own list.
  defaultTabId: 'all',
  defaults: {
    clients: [],
    projects: [],
    status: '',
    issueAfter: '',
    issueBefore: '',
    totalMin: '',
    totalMax: '',
  },
  matchers: {
    clients: matchClients,
    projects: matchProjects,
    status: matchCommercialStatus,
    issue: matchDateRange('issue_date', 'issueAfter', 'issueBefore'),
    total: matchNumberRange('total', 'totalMin', 'totalMax'),
  },
  searchFields: [
    'public_number', 'client_display_name', 'project_name',
    'billing_concept', 'customer_name',
  ],
});

// ?focus=<id> flashes a row (bidirectional navigation from Ingresos). Se lee
// por `consumeParam` y no por `route.query`: el param siembra la vista una vez
// y sale de la URL, en vez de quedarse re-encendiendo el destello en cada F5.
const focusParam = consumeParam('focus');
const highlightId = ref(focusParam ? Number(focusParam) : null);

const filteredRows = computed(() => applyFilters(store.collectionAccounts));

/** Derived from the loaded rows, like every other accounting tab. */
const clientFilterOptions = computed(() => {
  const seen = new Map();
  store.collectionAccounts.forEach((row) => {
    if (row.client != null && !seen.has(row.client)) {
      seen.set(row.client, row.client_display_name || `Cliente #${row.client}`);
    }
  });
  const options = [...seen.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => a.label.localeCompare(b.label));
  return [{ value: NO_CLIENT_KEY, label: 'Sin cliente' }, ...options];
});

/**
 * Catalog ids first (history.vue pattern) so a project with zero cuentas is
 * still selectable, defensively unioned with row-derived ids the catalog no
 * longer lists. Legacy snapshot-only rows (FK lost) keep their name entries,
 * marked "(histórico)" — they no longer bucket under "Sin proyecto", because
 * they never lacked one.
 */
const projectFilterOptions = computed(() => {
  const catalog = projectsStore.records ?? [];
  const nameCounts = new Map();
  catalog.forEach((project) => {
    nameCounts.set(project.name, (nameCounts.get(project.name) ?? 0) + 1);
  });
  const seen = new Map();
  catalog.forEach((project) => {
    const ambiguous = (nameCounts.get(project.name) ?? 0) > 1
      && project.client?.name;
    seen.set(
      project.id,
      ambiguous ? `${project.name} — ${project.client.name}` : project.name,
    );
  });
  const legacyNames = new Set();
  store.collectionAccounts.forEach((row) => {
    if (row.project_id != null) {
      if (!seen.has(row.project_id)) {
        seen.set(row.project_id, row.project_name || `Proyecto #${row.project_id}`);
      }
    } else if (row.project_name) {
      legacyNames.add(row.project_name);
    }
  });
  const options = [...seen.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => a.label.localeCompare(b.label));
  const legacy = [...legacyNames]
    .map((name) => ({ value: name, label: `${name} (histórico)` }))
    .sort((a, b) => a.label.localeCompare(b.label));
  return [{ value: NO_PROJECT_KEY, label: 'Sin proyecto' }, ...options, ...legacy];
});

const filterFields = computed(() => [
  {
    kind: 'multi', key: 'clients', label: 'Cliente',
    options: clientFilterOptions.value,
  },
  {
    kind: 'multi', key: 'projects', label: 'Proyecto',
    options: projectFilterOptions.value,
  },
  {
    kind: 'daterange', label: 'Emisión',
    minKey: 'issueAfter', maxKey: 'issueBefore',
  },
  {
    kind: 'range', label: 'Total',
    minKey: 'totalMin', maxKey: 'totalMax', type: 'money',
  },
]);

function handleCreateFilterTab(name) {
  return saveTab(name);
}

function handleResetFilters() {
  resetFilters();
}

const overdueCount = computed(
  () => store.collectionAccounts.filter((row) => row.is_overdue).length,
);

// Cliente and Proyecto are two facts, so they get two columns. `Origen`
// shrinks to a badge: it used to smuggle the hosting's client / the income's
// concept into its label, and both now have a column of their own.
const columns = [
  { key: 'public_number', label: 'Número', size: 'text', sortable: true, link: true },
  { key: 'origin', label: 'Origen', size: 'badge', hideBelow: 'lg' },
  { key: 'client_display_name', label: 'Cliente', size: 'name', sortable: true },
  { key: 'project_name', label: 'Proyecto', size: 'name', sortable: true, hideBelow: 'md' },
  { key: 'total', label: 'Total', format: 'money', sortable: true },
  { key: 'issue_date', label: 'Emisión', format: 'date', sortable: true, hideBelow: 'md' },
  { key: 'due_date', label: 'Vence', format: 'date', sortable: true },
  { key: 'commercial_status', label: 'Estado' },
  { key: 'row_actions', label: '', align: 'right' },
];

const { sortKey, sortDir, toggleSort, sortedRecords: sortedRows } = useTableSort(
  filteredRows,
  {
    sortDefaults: {
      total: 'desc',
      issue_date: 'desc',
      due_date: 'desc',
      public_number: 'desc',
      client_display_name: 'asc',
      // An empty project sorts first ascending, which clusters the
      // diagnóstico cobros together on purpose.
      project_name: 'asc',
    },
  },
);

async function loadRecords() {
  await store.fetchCollectionAccounts();
}

// ── Internal notes ──
//
// They never reach the client (not in the PDF, not in the email), so the panel
// is the only place they can be read back — a note you write and can never
// reopen is the same as no note. A modal and not a tooltip: the table wrapper
// is `overflow-x-auto`, which clips anything positioned absolutely inside a row.

const notesRow = ref(null);
const notesOpen = computed({
  get: () => notesRow.value !== null,
  set: (open) => { if (!open) notesRow.value = null; },
});

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

// Sending mail to a client is not undoable, so it asks first — the same
// treatment anular and marcar pagada already had, and that Hostings already
// gives its equivalent send action.
function askResend(row) {
  pendingAction.value = { kind: 'resend', row };
  confirmOpen.value = true;
}

const confirmOpen = ref(false);
const pendingAction = ref(null);

const CONFIRM_COPY = {
  paid: { title: 'Marcar como pagada', text: 'Marcar pagada', variant: 'info' },
  resend: { title: 'Reenviar cuenta de cobro', text: 'Reenviar', variant: 'info' },
  cancel: { title: 'Anular cuenta de cobro', text: 'Anular', variant: 'danger' },
};

const confirmTitle = computed(
  () => CONFIRM_COPY[pendingAction.value?.kind]?.title ?? '',
);
const confirmText = computed(
  () => CONFIRM_COPY[pendingAction.value?.kind]?.text ?? '',
);
// 'primary' is not in ConfirmModal's variant validator (warning|danger|info),
// so it warned in dev and silently fell back to warning styling.
const confirmVariant = computed(
  () => CONFIRM_COPY[pendingAction.value?.kind]?.variant ?? 'warning',
);
const confirmMessage = computed(() => {
  const action = pendingAction.value;
  if (!action?.row) return '';
  const number = action.row.public_number || `#${action.row.id}`;
  if (action.kind === 'paid') return `Se marcará la cuenta ${number} como pagada.`;
  if (action.kind === 'resend') {
    return `Se reenviará ${number} con el PDF adjunto a ${action.row.customer_email || 'el cliente'}.`;
  }
  return `Se anulará la cuenta ${number}. Si viene de un hosting, los avisos de vencimiento se reactivan.`;
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

// ── Detalle de la cuenta (reemplaza el salto al tab de Ingresos) ──

// La cuenta de cobro tiene dirección propia (`?account=`): así el número de la
// fila puede publicarla en un enlace, y recargar o compartir la URL reabre el
// detalle. No es un ephemeralParam a propósito — esos se borran en el setup.
const {
  openRow: detailRow,
  isOpen: detailOpen,
  toFor: accountDetailTo,
  open: openDetailById,
  close: closeDetail,
} = useDetailQueryParam('account', { rows: sortedRows });

function openDetail(row) {
  openDetailById(row.id);
}

// ── Bidirectional navigation ──

/**
 * The modal's optional exit. Ingresos lands on its builtin "Solo esperados"
 * tab unless `accounting_incomeTab` says otherwise, so without it a cuenta
 * linked to a liquid — or to an already-paid expected — arrived at a list
 * that had filtered its own target out.
 */
function goToIncome(incomeId) {
  navigateTo({
    path: '/panel/accounting/incomes',
    query: { focus: incomeId, accounting_incomeTab: 'all' },
  });
}

function goToCollectionEmails(row) {
  navigateTo(historySendsLink('collection_account', row.id));
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
      // Falling through here used to settle the cuenta as a plain mark-paid,
      // silently skipping the Liquidar routing this guard exists to enforce.
      console.error('Error fetching linked income:', error);
      notify.error({
        title: 'No se pudo verificar el ingreso vinculado',
        detail: 'Intenta de nuevo antes de marcar la cuenta como pagada.',
      });
      return;
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
  if (action.kind === 'resend') {
    await resend(action.row);
    return;
  }
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

onMounted(() => {
  // Project filter options come from the full catalog (history.vue
  // pattern); the store swallows failures, so an error just means a
  // smaller dropdown, never a blocked page.
  projectsStore.fetchProjects();
  return loadRecords();
});
usePanelRefresh(loadRecords);
</script>
