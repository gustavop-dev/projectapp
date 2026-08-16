<template>
  <div :class="PAGE_MAX_WIDTH">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Ingresos</h1>
        <p class="text-sm text-text-subtle mt-1">
          Ingresos esperados y líquidos del negocio, con su reparto entre socios.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <BaseButton
          variant="secondary"
          size="md"
          data-testid="incomes-client-totals-button"
          @click="openTotalsModal"
        >
          Totales por cliente
        </BaseButton>
        <BaseButton
          variant="primary"
          size="md"
          data-testid="incomes-new-button"
          @click="openCreateModal"
        >
          <PlusIcon class="w-4 h-4" />
          <span>Nuevo ingreso</span>
        </BaseButton>
      </div>
    </div>

    <AccountingSubnav active="incomes" />

    <!-- KPI cards (year scope, server-computed) -->
    <div class="grid grid-cols-2 lg:grid-cols-7 gap-3 mb-6">
      <AccountingStatCard
        label="Total esperado (año)"
        :value="money(incomesMeta.expected_total)"
      />
      <AccountingStatCard
        label="Total líquido (año)"
        :value="money(incomesMeta.liquid_total)"
        :sub="incomesMeta.received_pct != null ? `${incomesMeta.received_pct}% recibido` : ''"
        tone="success"
      />
      <AccountingStatCard
        label="Mes actual (líquido)"
        :value="money(incomesMeta.current_month_liquid)"
      />
      <AccountingStatCard
        label="Mayor ingreso del año"
        :value="incomesMeta.top_income ? money(incomesMeta.top_income.amount) : '—'"
        :sub="incomesMeta.top_income?.concept || ''"
        tone="brand"
      />
      <AccountingStatCard
        label="Perdido (año)"
        :value="money(incomesMeta.lost_total)"
        :tone="Number(incomesMeta.lost_total) > 0 ? 'danger' : 'default'"
      />
      <AccountingStatCard
        label="Sin cliente"
        :value="String(incomesMeta.without_client_count ?? 0)"
        :tone="(incomesMeta.without_client_count ?? 0) > 0 ? 'warning' : 'default'"
        sub="Pendientes de vincular"
      />
      <!-- Válido pero visible: un vacío legítimo que igual se muestra como
           pendiente. Cuenta sólo filas con cliente (sin cliente no hay
           proyecto que proponer). -->
      <AccountingStatCard
        label="Sin proyecto"
        :value="String(incomesMeta.without_project_count ?? 0)"
        :tone="(incomesMeta.without_project_count ?? 0) > 0 ? 'warning' : 'default'"
        sub="Con cliente, pendientes de proyecto"
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

    <!-- Search + Filter toggle -->
    <div class="flex items-center gap-2 mb-5">
      <BaseInput
        v-model="searchInput"
        type="text"
        placeholder="Buscar por concepto, notas o cliente..."
        data-testid="incomes-search-input"
        class="w-full sm:max-w-xs"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <AccountingExportButton section="income" :params="exportParams" />
      <BaseSegmented
        v-model="viewMode"
        :options="viewModeOptions"
        size="sm"
        class="ml-auto"
        data-testid="incomes-view-mode"
      />
    </div>

    <!-- Filter panel -->
    <AccountingFilterPanel
      :fields="filterFields"
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :results-count="filteredRecords.length"
      :search-value="currentFilters.search"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
      @clear-search="searchInput = ''"
    />

    <!-- Summary chips (filtered rows) -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <span
        class="text-xs px-2.5 py-1 rounded-full bg-surface-raised text-text-muted font-medium tabular-nums"
        data-testid="incomes-total-expected"
      >
        Total esperado: {{ formatMoney(totalExpected) }}
      </span>
      <span
        class="text-xs px-2.5 py-1 rounded-full bg-success-soft text-success-strong font-medium tabular-nums"
        data-testid="incomes-total-liquid"
      >
        Total líquido: {{ formatMoney(totalLiquid) }}
      </span>
      <span
        v-if="totalLost > 0"
        class="text-xs px-2.5 py-1 rounded-full bg-danger-soft text-danger-strong font-medium tabular-nums"
        data-testid="incomes-total-lost"
      >
        Total perdido: {{ formatMoney(totalLost) }}
      </span>
    </div>

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'fetch_failed'"
      title="No se pudieron cargar los ingresos"
      :retrying="store.isLoading"
      @retry="loadRecords"
    />

    <!-- Empty -->
    <BaseEmptyState
      v-else-if="!store.isLoading && filteredRecords.length === 0"
      :title="hasActiveFilters ? 'Sin resultados con esos filtros' : 'No hay ingresos aún'"
      :description="hasActiveFilters
        ? 'Ajusta o limpia los filtros para ver más registros.'
        : 'Registra el primer ingreso esperado o líquido del negocio.'"
    >
      <template #actions>
        <BaseButton
          v-if="hasActiveFilters"
          variant="secondary"
          size="sm"
          @click="handleResetFilters"
        >
          Limpiar filtros
        </BaseButton>
        <BaseButton v-else variant="primary" size="sm" @click="openCreateModal">
          <PlusIcon class="w-4 h-4" />
          <span>Nuevo ingreso</span>
        </BaseButton>
      </template>
    </BaseEmptyState>

    <!-- Table: grouped by client (landing mode set in Configuración) or classic -->
    <template v-else>
      <IncomeGroupedTable
        v-if="isGrouped"
        v-model:selected="selectedIds"
        selectable
        :loading="store.isLoading"
        :highlight-id="lastMutatedId"
        :columns="groupedColumns"
        :groups="clientGroups"
        :highlight-query="currentFilters.search"
        :collapsed-ids="collapsedGroupIds"
        :show-actions="false"
        @edit="openEditModal"
        @delete="confirmDeleteRecord"
        @toggle-group="toggleGroup"
      >
        <template #cell-row_actions="{ row }">
          <IncomeRowActionsButton
            :row="row"
            :busy="duplicatingId === row.id"
            @open="openActions"
          />
        </template>
        <!-- Sin `stretch`: la celda de la grilla trunca (overflow hidden) y
             recortaría el área estirada. El enlace cubre el texto. -->
        <template #cell-concept="{ row }">
          <BaseRowLink
            :to="incomeDetailTo(row.id)"
            :data-testid="`income-open-${row.id}`"
            class="hover:text-text-brand transition-colors"
          >
            <HighlightText :text="row.concept" :query="currentFilters.search" />
          </BaseRowLink>
        </template>
        <template #cell-kind_label="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="KIND_BADGE_CLASSES[row.kind] || KIND_BADGE_CLASSES.expected"
          >
            {{ row.kind_label }}
          </span>
        </template>
        <template #cell-payment_status="{ row }">
          <IncomePaymentStateCell :row="row" />
        </template>
        <template #cell-project_name="{ row }">
          <span v-if="row.project_name" class="inline-flex items-center gap-1">
            <HighlightText
              :text="row.project_name"
              :query="currentFilters.search"
            />
            <ProjectSpaceLink
              :project-id="row.project"
              :data-testid="`income-project-space-${row.id}`"
            />
          </span>
          <span v-else class="text-text-subtle">—</span>
        </template>
      </IncomeGroupedTable>

      <!-- Column sort and pagination stay classic-only affordances; the
           grouped view always renders the whole filtered set, and its own
           checkboxes feed the same selection (and the same bulk bar). -->
      <template v-else>
        <AccountingTable
          v-model:selected="selectedIds"
          selectable
          :loading="store.isLoading"
          :highlight-id="lastMutatedId"
          :columns="columns"
          :rows="pagedRecords"
          :highlight-query="currentFilters.search"
          :sort-key="sortKey"
          :sort-dir="sortDir"
          :row-tone="incomeRowTone"
          :show-actions="false"
          @edit="openEditModal"
          @delete="confirmDeleteRecord"
          @sort="toggleSort"
        >
          <template #cell-row_actions="{ row }">
            <IncomeRowActionsButton
              :row="row"
              :busy="duplicatingId === row.id"
              @open="openActions"
            />
          </template>
          <!-- El concepto es la dirección del detalle: un enlace de verdad, no
               sólo el ojo del kebab. -->
          <template #cell-concept="{ row }">
            <BaseRowLink
              :to="incomeDetailTo(row.id)"
              stretch
              :data-testid="`income-open-${row.id}`"
              class="block truncate hover:text-text-brand transition-colors"
            >
              <HighlightText :text="row.concept" :query="currentFilters.search" />
            </BaseRowLink>
          </template>
          <template #cell-kind_label="{ row }">
            <span
              class="text-xs px-2.5 py-1 rounded-full font-medium"
              :class="KIND_BADGE_CLASSES[row.kind] || KIND_BADGE_CLASSES.expected"
            >
              {{ row.kind_label }}
            </span>
          </template>
          <!-- An empty client cell hides the completion debt; the pill makes
               it actionable, same as the hostings table. Grouped view needs
               none: its "Sin cliente" bucket already carries the flag. -->
          <template #cell-client_name="{ row }">
            <HighlightText
              v-if="row.client_name"
              :text="row.client_name"
              :query="currentFilters.search"
            />
            <span
              v-else
              class="text-[10px] px-1.5 py-0.5 rounded-full bg-warning-soft text-warning-strong font-semibold uppercase tracking-wider whitespace-nowrap"
              title="Sin cliente vinculado — los totales por cliente no lo cuentan"
              :data-testid="`income-unlinked-${row.id}`"
            >
              sin vincular
            </span>
          </template>
          <!-- Collection state gets its own column: sharing the Tipo cell with
               the kind badge wrapped the pills and doubled the row height. -->
          <template #cell-payment_status="{ row }">
            <IncomePaymentStateCell :row="row" />
          </template>
          <template #cell-project_name="{ row }">
            <span v-if="row.project_name" class="inline-flex items-center gap-1">
              <HighlightText
                :text="row.project_name"
                :query="currentFilters.search"
              />
              <ProjectSpaceLink
                :project-id="row.project"
                :data-testid="`income-project-space-${row.id}`"
              />
            </span>
            <span v-else class="text-text-subtle">—</span>
          </template>
        </AccountingTable>

        <BasePagination
          v-if="!store.isLoading"
          :current-page="currentPage"
          :total-pages="totalPages"
          :total-items="totalItems"
          :range-from="rangeFrom"
          :range-to="rangeTo"
          class="mt-4"
          @prev="prevPage"
          @next="nextPage"
          @go="goToPage"
        />
      </template>
    </template>

    <!--
      Bulk client assignment: the completion path for rows without client.
      Below the table and sticky, so it stays reachable after selecting at the
      bottom of the grouped view; outside the error/empty/table chain, because
      a selection whose rows the filter just hid still needs its actions.
    -->
    <BulkAssignBar
      v-model:selected="selectedIds"
      :rows="store.incomes"
      :filtered-ids="filteredIds"
      :entity="INCOME_ENTITY"
      testid-prefix="incomes"
      :record-label="incomeLabel"
      :busy="store.isUpdating"
      project-enabled
      @submit="applyClientToSelection"
      @submit-project="applyProjectToSelection"
    />

    <!-- Create/edit modal (also the duplicate form, seeded and creating) -->
    <IncomeFormModal
      :open="isModalOpen"
      :record="editingRecord"
      :seed="seedRecord"
      :saving="store.isUpdating"
      @close="closeModal"
      @submit="handleSubmit"
      @project-created="onProjectCreated"
    />

    <!-- Post-create offer: a project created inline may have a backlog of
         the client's older records; the same PA-51 modal closes it here. -->
    <ProjectAssignUnlinkedModal
      :open="assignOfferOpen"
      :project="pendingAssignProject"
      @close="dismissAssignOffer"
      @assigned="onUnlinkedAssigned"
    />

    <!-- Row actions: one list for both view modes, opened from the kebab -->
    <IncomeActionsModal
      :open="actionsOpen"
      :record="actionsRow"
      @close="actionsOpen = false"
      @detail="openIncomeDetail"
      @edit="openEditModal"
      @duplicate="duplicateIncome"
      @liquidate="openLiquidateModal"
      @generate-collection="openCollectionModal"
      @view-collection="goToCollectionAccount"
      @view-emails="goToIncomeEmails"
      @toggle-mute="toggleMute"
      @write-off="confirmWriteOff"
      @delete="confirmDeleteRecord"
    />

    <!-- Detalle del ingreso, reutilizando el modal de cuentas de cobro -->
    <IncomeDetailModal
      :open="detailOpen"
      :income-id="detailIncomeId"
      @close="closeIncomeDetail"
      @duplicate="duplicateIncome"
    />

    <!-- Liquidate modal: settles an expected income into a linked liquid one -->
    <IncomeLiquidateModal
      :open="isLiquidateModalOpen"
      :record="liquidatingRecord"
      :saving="store.isUpdating"
      @close="closeLiquidateModal"
      @submit="handleLiquidateSubmit"
    />

    <IncomeMuteModal
      :open="muteModalOpen"
      :record="mutingRecord"
      :saving="store.isUpdating"
      @close="muteModalOpen = false"
      @submit="submitMute"
    />

    <!-- Totales por cliente sobre las filas filtradas -->
    <IncomeClientTotalsModal
      :open="totalsModalOpen"
      :rows="filteredRecords"
      :hosting-rows="store.hostings"
      @close="totalsModalOpen = false"
    />

    <!-- Generar cuenta de cobro desde el ingreso (preseleccionado) -->
    <CollectionAccountFormModal
      :open="collectionModalOpen"
      :income="collectionIncome"
      @close="collectionModalOpen = false"
      @created="onCollectionCreated"
    />

    <!-- Confirm modal for delete / write-off -->
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      :require-type-text="confirmState.requireTypeText"
      :hide-cancel="confirmState.hideCancel"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { PlusIcon } from '@heroicons/vue/24/outline';
import IncomeActionsModal from '~/components/accounting/IncomeActionsModal.vue';
import IncomeRowActionsButton from '~/components/accounting/IncomeRowActionsButton.vue';
import IncomeDetailModal from '~/components/accounting/IncomeDetailModal.vue';
import IncomeMuteModal from '~/components/accounting/IncomeMuteModal.vue';
import IncomePaymentStateCell from '~/components/accounting/IncomePaymentStateCell.vue';
import HighlightText from '~/components/ui/HighlightText.vue';
import CollectionAccountFormModal from '~/components/accounting/CollectionAccountFormModal.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import AccountingExportButton from '~/components/accounting/AccountingExportButton.vue';
import IncomeFormModal from '~/components/accounting/IncomeFormModal.vue';
import IncomeClientTotalsModal from '~/components/accounting/IncomeClientTotalsModal.vue';
import IncomeGroupedTable from '~/components/accounting/IncomeGroupedTable.vue';
import BulkAssignBar from '~/components/accounting/BulkAssignBar.vue';
import IncomeLiquidateModal from '~/components/accounting/IncomeLiquidateModal.vue';
import ProjectAssignUnlinkedModal from '~/components/panel/projects/ProjectAssignUnlinkedModal.vue';
import ProjectSpaceLink from '~/components/panel/projects/ProjectSpaceLink.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useIncomeViewMode } from '~/composables/useIncomeViewMode';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import { useRowSelection } from '~/composables/useRowSelection';
import { useDetailQueryParam } from '~/composables/useDetailQueryParam';
import {
  useAccountingFilters,
  matchDateRange,
  matchNumberRange,
  matchEquals,
  matchBoolean,
} from '~/composables/useAccountingFilters';
import { useAccountingStore } from '~/stores/accounting';
import { usePanelProjectsStore } from '~/stores/panel_projects';
import { buildExportParams } from '~/utils/accountingExportParams';
import { describeAssignmentResult } from '~/utils/clientAssignment';
import { describeProjectAssignmentResult } from '~/utils/projectAssignment';
import { formatDate } from '~/utils/formatDate';
import { formatMoney } from '~/utils/formatMoney';
import { historySendsLink } from '~/utils/historyDeepLink';
import {
  clientLabelOf,
  groupByClient,
  withClientWeights,
} from '~/utils/incomeClients';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();
const projectsStore = usePanelProjectsStore();

/** Noun the bulk client bar uses in its confirmation and result copy. */
const INCOME_ENTITY = { singular: 'ingreso', plural: 'ingresos' };

const incomesMeta = computed(() => store.metaFor('incomes'));

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

// -------------------------------------------------------------------
// Filters
// -------------------------------------------------------------------

// Sentinels shared with the backend filters: 'none' means "not set".
const NO_CLIENT_KEY = 'none';
const NO_CLIENT_LABEL = 'Sin cliente';
const NO_ORIGIN_KEY = 'none';

const matchClients = (record, value) => {
  if (!Array.isArray(value) || value.length === 0) return true;
  if (record.client == null) return value.includes(NO_CLIENT_KEY);
  return value.includes(record.client);
};
matchClients.keys = ['clients'];

const NO_PROJECT_KEY = 'none';
const NO_PROJECT_LABEL = 'Sin proyecto';

const matchProjects = (record, value) => {
  if (!Array.isArray(value) || value.length === 0) return true;
  if (record.project == null) return value.includes(NO_PROJECT_KEY);
  return value.includes(record.project);
};
matchProjects.keys = ['projects'];

const matchOrigin = (record, value) => {
  if (!Array.isArray(value) || value.length === 0) return true;
  if (!record.origin) return value.includes(NO_ORIGIN_KEY);
  return value.includes(record.origin);
};
matchOrigin.keys = ['origin'];

const matchPartner = (record, value) => {
  if (!value) return true;
  if (value === 'gustavo') return Number(record.gustavo_amount) > 0;
  if (value === 'carlos') return Number(record.carlos_amount) > 0;
  if (value === 'projectapp') {
    return record.destination === 'pocket' || Number(record.company_amount) > 0;
  }
  return true;
};
matchPartner.keys = ['partner'];

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
  viewName: 'accounting_income',
  // `project` siembra un filtro y acompaña a la vista mientras siga puesto;
  // `focus` sólo destaca una fila una vez y sale de la URL al montar.
  ephemeralParams: [{ name: 'project', boundTo: 'projects' }, 'focus'],
  // Fixed presets: unlike the seeded saved tabs, editing a filter here never
  // rewrites the tab, which is what the landing tab needs.
  builtinTabs: [
    {
      id: 'expected-pending',
      name: 'Solo esperados',
      filters: { kind: 'expected', paymentStatus: 'pending' },
    },
    {
      id: 'hosting-expected',
      name: 'Hosting esperados',
      filters: { kind: 'expected', paymentStatus: 'pending', search: 'hosting' },
    },
    { id: 'lost', name: 'Perdidos', filters: { kind: 'lost' } },
    {
      id: 'no-client',
      name: 'Sin cliente',
      filters: { clients: [NO_CLIENT_KEY] },
    },
    {
      id: 'no-project',
      name: 'Sin proyecto',
      filters: { projects: [NO_PROJECT_KEY] },
    },
  ],
  // The day-to-day question is what is still uncollected, not the full ledger.
  defaultTabId: 'expected-pending',
  defaults: {
    periodAfter: '',
    periodBefore: '',
    amountMin: '',
    amountMax: '',
    kind: '',
    paymentStatus: '',
    partner: '',
    ledger: '',
    clients: [],
    projects: [],
    origin: [],
    muted: '',
  },
  matchers: {
    period: matchDateRange('period_date', 'periodAfter', 'periodBefore'),
    amount: matchNumberRange('total_amount', 'amountMin', 'amountMax'),
    kind: matchEquals('kind', 'kind'),
    // Liquid and lost rows carry `payment_status: null`, so any active
    // value here already narrows the list down to expected records.
    paymentStatus: matchEquals('payment_status', 'paymentStatus'),
    partner: matchPartner,
    ledger: matchEquals('ledger', 'ledger'),
    clients: matchClients,
    projects: matchProjects,
    origin: matchOrigin,
    muted: matchBoolean('reminders_muted', 'muted'),
  },
  // client_name mirrors the server-side q filter, which also reaches the
  // linked client's name — see the income entity's search_fields.
  searchFields: ['concept', 'notes', 'client_name', 'project_name'],
});

const clientFilterOptions = computed(() => {
  // Derived from the loaded rows, not the full client catalog: the dropdown
  // is a flat checkbox list, so bounding it by what is actually on screen
  // keeps it usable however many clients exist.
  const seen = new Map();
  store.incomes.forEach((row) => {
    if (row.client != null && !seen.has(row.client)) {
      seen.set(row.client, clientLabelOf(row));
    }
  });
  const options = [...seen.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => a.label.localeCompare(b.label));
  return [{ value: NO_CLIENT_KEY, label: NO_CLIENT_LABEL }, ...options];
});

/**
 * Full catalog first (history.vue pattern): a project with zero linked rows
 * must still be selectable — that gap is exactly what the filter reveals.
 * Row-derived entries survive as a defensive union for projects the catalog
 * no longer lists. Numeric ids: `matchProjects` compares `record.project`.
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
  store.incomes.forEach((row) => {
    if (row.project != null && !seen.has(row.project)) {
      seen.set(row.project, row.project_name || `Proyecto #${row.project}`);
    }
  });
  const options = [...seen.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => a.label.localeCompare(b.label));
  return [{ value: NO_PROJECT_KEY, label: NO_PROJECT_LABEL }, ...options];
});

const filterFields = computed(() => [
  { kind: 'daterange', label: 'Mes', minKey: 'periodAfter', maxKey: 'periodBefore' },
  { kind: 'range', label: 'Total', minKey: 'amountMin', maxKey: 'amountMax', type: 'money' },
  {
    kind: 'segmented',
    key: 'kind',
    label: 'Tipo',
    options: [
      { value: '', label: 'Todos' },
      { value: 'expected', label: 'Esperado' },
      { value: 'liquid', label: 'Líquido' },
      { value: 'lost', label: 'Pérdidas' },
    ],
  },
  {
    kind: 'segmented',
    key: 'paymentStatus',
    label: 'Cobro',
    options: [
      { value: '', label: 'Todos' },
      { value: 'pending', label: 'Sin pagos' },
      { value: 'partial', label: 'Parcial' },
      { value: 'paid', label: 'Pagado' },
    ],
  },
  {
    kind: 'segmented',
    key: 'muted',
    label: 'Avisos',
    options: [
      { value: '', label: 'Todos' },
      { value: 'true', label: 'Silenciados' },
      { value: 'false', label: 'Con aviso' },
    ],
  },
  {
    kind: 'segmented',
    key: 'partner',
    label: 'Socio',
    options: [
      { value: '', label: 'Todos' },
      { value: 'gustavo', label: 'Gustavo' },
      { value: 'carlos', label: 'Carlos' },
      { value: 'projectapp', label: 'ProjectApp' },
    ],
  },
  {
    kind: 'segmented',
    key: 'ledger',
    label: 'Contabilidad',
    options: [
      { value: '', label: 'Todas' },
      { value: 'company', label: 'Empresa' },
      { value: 'gustavo', label: 'Personal Gustavo' },
      { value: 'carlos', label: 'Personal Carlos' },
    ],
  },
  {
    kind: 'multi',
    key: 'clients',
    label: 'Cliente',
    options: clientFilterOptions.value,
  },
  {
    kind: 'multi',
    key: 'projects',
    label: 'Proyecto',
    options: projectFilterOptions.value,
  },
  {
    kind: 'multi',
    key: 'origin',
    label: 'Origen',
    options: [
      { value: 'development', label: 'Desarrollo' },
      { value: 'hosting', label: 'Hosting' },
      { value: 'diagnostic', label: 'Diagnóstico' },
      { value: 'other', label: 'Otro' },
      { value: NO_ORIGIN_KEY, label: 'Sin clasificar' },
    ],
  },
]);

const EXPORT_MAPPING = {
  periodAfter: 'date_from',
  periodBefore: 'date_to',
  amountMin: 'amount_min',
  amountMax: 'amount_max',
  kind: 'kind',
  paymentStatus: 'payment_status',
  partner: 'partner',
  ledger: 'ledger',
  clients: 'client',
  origin: 'origin',
  search: 'q',
};

const exportParams = computed(() =>
  buildExportParams(currentFilters, EXPORT_MAPPING),
);

// -------------------------------------------------------------------
// Data + CRUD controller (modal, delete confirm, pagination)
// -------------------------------------------------------------------

const filteredRecords = computed(() => applyFilters(store.incomes));

const {
  isModalOpen,
  editingRecord,
  seedRecord,
  openCreateModal,
  lastMutatedId,
  openEditModal,
  openSeededModal,
  closeModal,
  handleSubmit,
  confirmDeleteRecord,
  confirmState,
  handleConfirmed,
  handleCancelled,
  currentPage,
  sortedRecords,
  pageSize: PAGE_SIZE,
  totalPages,
  totalItems,
  rangeFrom,
  rangeTo,
  pagedRecords,
  prevPage,
  nextPage,
  goToPage,
  handleCreateFilterTab,
  handleResetFilters,
  sortKey,
  sortDir,
  toggleSort,
  requestConfirm,
  runMutation,
} = useAccountingCrudPage({
  entity: 'incomes',
  // Narrowing the working set sends the reader back to page 1; deleting or
  // editing a row must leave them where they were.
  resetPageOn: currentFilters,
  // A liquidation creates a CHILD row, so the parent expected row's
  // payment state is computed server-side from data the response doesn't
  // carry. Without a refetch its badge and tint stay stale. A settlement can
  // also book deductions, so the cached expenses list is dropped too.
  onAfterMutation: () => {
    store.expenses = [];
    return store.fetchRecords('incomes');
  },
  // The month column shows the localized label but sorts by the ISO date.
  sortAccessors: { period_label: 'period_date' },
  sortDefaults: {
    period_label: 'desc',
    total_amount: 'desc',
    gustavo_amount: 'desc',
    carlos_amount: 'desc',
  },
  store,
  filteredRecords,
  saveTab,
  resetFilters,
  isFilterPanelOpen,
  labels: {
    entityName: 'ingreso',
    created: 'Ingreso creado',
    duplicated: 'Ingreso duplicado',
    updated: 'Ingreso actualizado',
    deleted: 'Ingreso eliminado',
    saveErrorTitle: 'No se pudo guardar',
    deleteErrorTitle: 'No se pudo eliminar',
    deleteTitle: 'Eliminar ingreso',
    deleteMessage: (record) =>
      `Esto eliminará el ingreso "${record.concept}" de forma permanente. Esta acción no se puede deshacer.`,
  },
});

const totalExpected = computed(() =>
  filteredRecords.value
    .filter((r) => r.kind === 'expected')
    .reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0),
);

const totalLiquid = computed(() =>
  filteredRecords.value
    .filter((r) => r.kind === 'liquid')
    .reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0),
);

const totalLost = computed(() =>
  filteredRecords.value
    .filter((r) => r.kind === 'lost')
    .reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0),
);

const KIND_BADGE_CLASSES = {
  liquid: 'bg-success-soft text-success-strong',
  lost: 'bg-danger-soft text-danger-strong',
  expected: 'bg-surface-raised text-text-muted',
};

// A soft fill would vanish: `incomeRowTone` already paints the whole row in
// that same tint. The chip sits on the plain surface with a colored outline so
// it reads on the tinted row and on the untinted one alike.
const PAYMENT_BADGE_CLASSES = {
  paid: 'bg-surface text-success-strong ring-1 ring-inset ring-success-strong/30',
  partial: 'bg-surface text-warning-strong ring-1 ring-inset ring-warning-strong/30',
};

/** Green once collected, amber while partially collected. */
const incomeRowTone = (row) => {
  if (row.kind !== 'expected') return null;
  if (row.payment_status === 'paid') return 'success';
  if (row.payment_status === 'partial') return 'warning';
  return null;
};

// -------------------------------------------------------------------
// Row actions: liquidate an expected income / write it off
// -------------------------------------------------------------------

const isLiquidateModalOpen = ref(false);
const liquidatingRecord = ref(null);

function openLiquidateModal(record) {
  liquidatingRecord.value = record;
  isLiquidateModalOpen.value = true;
}

function closeLiquidateModal() {
  isLiquidateModalOpen.value = false;
  liquidatingRecord.value = null;
}

async function handleLiquidateSubmit(payload) {
  const incomeId = liquidatingRecord.value?.id;
  const result = await runMutation(
    () => store.settleIncome(incomeId, payload),
    {
      successTitle: 'Ingreso liquidado',
      errorTitle: 'No se pudo liquidar',
      // Flash the expected row: it is the one whose state just changed.
      flashId: incomeId,
    },
  );
  if (result.success) closeLiquidateModal();
}

function confirmWriteOff(record) {
  requestConfirm({
    title: 'Marcar como perdido',
    message:
      `"${record.concept}" (${formatMoney(Number(record.total_amount))}) se `
      + 'contará como pérdida: sale del total esperado y deja de aparecer '
      + 'en la lista salvo que filtres por Pérdidas. No afecta la utilidad.',
    variant: 'danger',
    confirmText: 'Marcar como perdido',
    cancelText: 'Cancelar',
    onConfirm: () => runMutation(
      () => store.updateRecord('incomes', record.id, {
        kind: 'lost',
        destination: 'partners',
      }),
      {
        successTitle: 'Ingreso marcado como perdido',
        errorTitle: 'No se pudo marcar como perdido',
      },
    ),
  });
}

const muteModalOpen = ref(false);
const mutingRecord = ref(null);

function openMuteModal(record) {
  mutingRecord.value = record;
  muteModalOpen.value = true;
}

function submitMute(payload) {
  const record = mutingRecord.value;
  if (!record) return;
  const detail = payload.until
    ? `Los avisos de "${record.concept}" se reanudan el ${formatDate(payload.until)}.`
    : `No se enviarán avisos de "${record.concept}" hasta que los reactives.`;
  runMutation(
    () => store.muteIncomeReminders(record.id, payload),
    {
      successTitle: 'Avisos silenciados',
      successDetail: detail,
      errorTitle: 'No se pudieron silenciar los avisos',
      flashId: record.id,
    },
  ).then((result) => {
    if (result?.success) {
      muteModalOpen.value = false;
      mutingRecord.value = null;
    }
  });
}

// No confirmation: reactivating is non-destructive and instantly reversible.
function unmuteIncome(record) {
  runMutation(
    () => store.muteIncomeReminders(record.id, { muted: false }),
    {
      successTitle: 'Avisos reactivados',
      successDetail: `"${record.concept}" vuelve al correo diario.`,
      errorTitle: 'No se pudieron reactivar los avisos',
      flashId: record.id,
    },
  );
}

// Concepto gets the widest floor; Concepto, Total, Tipo and Cobro survive
// every width and the period collapses first. The ledger is filter-only: it
// earned no column of its own next to what the row is actually about.
// The partner splits left the table — with six to eight actions per row the
// grid had no room left for what the operator actually scans by. The whole
// split (Gustavo, Carlos and la empresa) lives in the income detail modal.
const columns = [
  // `link: true`: acá va el enlace al detalle, y la celda se vuelve `relative`
  // para que se estire a todo su ancho.
  { key: 'concept', label: 'Concepto', size: 'name', sortable: true, link: true },
  { key: 'client_name', label: 'Cliente', size: 'name', sortable: true, hideBelow: 'md' },
  { key: 'project_name', label: 'Proyecto', size: 'name', sortable: true, hideBelow: 'lg' },
  { key: 'kind_label', label: 'Tipo', size: 'badge' },
  { key: 'payment_status', label: 'Cobro', size: 'text' },
  { key: 'period_label', label: 'Mes', sortable: true, hideBelow: 'lg' },
  { key: 'total_amount', label: 'Total', format: 'money', sortable: true },
  { key: 'row_actions', label: '', align: 'right' },
];

// ── Vista agrupada por cliente ──

const { viewMode, isGrouped, initFromSettings } = useIncomeViewMode(store);

const viewModeOptions = [
  { value: 'grouped', label: 'Agrupado' },
  { value: 'classic', label: 'Clásico' },
];

const collapsedGroupIds = ref([]);

function toggleGroup(id) {
  collapsedGroupIds.value = collapsedGroupIds.value.includes(id)
    ? collapsedGroupIds.value.filter((groupId) => groupId !== id)
    : [...collapsedGroupIds.value, id];
}

/** Grouped over the WHOLE filtered set (no pagination), like the totals modal. */
const clientGroups = computed(() =>
  withClientWeights(groupByClient(filteredRecords.value)),
);

// The group header already names the client, and column sort belongs to the
// classic table — inside a group the rows keep the ledger order. Proyecto
// stays: inside one client's group it is exactly what tells rows apart.
const groupedColumns = columns
  .filter((col) => col.key !== 'client_name')
  .map(({ sortable, ...col }) => col);

// ── Selección múltiple + asignación masiva de cliente ──

// Fed the FULL store list, not the filtered rows: the selection is meant to
// survive a filter change, so only "this income no longer exists" may drop an
// id from it.
const { selectedIds, clearSelection, dropIds } = useRowSelection(() => store.incomes);
const totalsModalOpen = ref(false);

const filteredIds = computed(() => filteredRecords.value.map((row) => row.id));

/** What identifies an income in the bulk confirmation list. */
const incomeLabel = (row) => row.concept || `Ingreso #${row.id}`;

async function applyClientToSelection({ ids, client, mode, plan }) {
  const result = await runMutation(
    () => store.bulkAssignIncomeClient(ids, client),
    {
      successTitle: mode === 'unlink'
        ? 'Cliente desvinculado de los ingresos'
        : 'Cliente asignado a los ingresos',
      // The server skips rows already on the target, so the count it returns
      // is what actually changed — not what was selected.
      successDetail: (r) => describeAssignmentResult(
        plan, r.data?.updated ?? 0, { entity: INCOME_ENTITY },
      ),
      errorTitle: mode === 'unlink'
        ? 'No se pudo desvincular el cliente'
        : 'No se pudo asignar el cliente',
    },
  );
  if (result.success) {
    clearSelection();
    return;
  }
  // The server refused the batch because some of it no longer exists. Drop
  // those ids first — that holds even if the reload below fails — then rebuild
  // the list so the counters, the groups and the KPI meta agree with it.
  if (result.missingIds?.length) {
    dropIds(result.missingIds);
    await loadRecords();
  }
}

async function applyProjectToSelection({ ids, project, mode, plan }) {
  const result = await runMutation(
    () => store.bulkAssignIncomeProject(ids, project),
    {
      successTitle: mode === 'unlink'
        ? 'Proyecto quitado de los ingresos'
        : 'Proyecto asignado a los ingresos',
      successDetail: (r) => describeProjectAssignmentResult(
        plan, r.data?.updated ?? 0, { entity: INCOME_ENTITY },
      ),
      errorTitle: mode === 'unlink'
        ? 'No se pudo quitar el proyecto'
        : 'No se pudo asignar el proyecto',
    },
  );
  if (result.success) {
    clearSelection();
    // Cross-module courtesy: the projects page reads per-project counts; if
    // its store already holds data, refresh it so a later visit agrees.
    if (projectsStore.records.length) projectsStore.fetchProjects();
    return;
  }
  // `records_not_found` and `client_mismatch` both name exact ids: drop
  // them, keep the rest of the selection, and rebuild the view.
  if (result.missingIds?.length) {
    dropIds(result.missingIds);
    await loadRecords();
  }
}

// ── Cuenta de cobro desde el ingreso ──

const collectionModalOpen = ref(false);
const collectionIncome = ref(null);

function openCollectionModal(row) {
  collectionIncome.value = row;
  collectionModalOpen.value = true;
}

async function openTotalsModal() {
  totalsModalOpen.value = true;
  // Hostings live in another tab: fetch them once so the per-client view
  // can show both halves of what a client costs and pays.
  if (!store.hostings.length) await store.fetchRecords('hostings');
}

function onCollectionCreated() {
  collectionModalOpen.value = false;
  collectionIncome.value = null;
  // Reload so the row swaps to the "Ver cuenta de cobro" action.
  loadRecords();
}

function goToCollectionAccount(row) {
  navigateTo({
    path: '/panel/accounting/collections',
    query: { focus: row.collection_account_id },
  });
}

function goToIncomeEmails(row) {
  navigateTo(historySendsLink('income', row.id));
}

// ── Acciones de fila: un solo menú para las dos vistas ──
//
// The two view modes each carried their own copy of the action block and had
// already drifted: the classic table had silently lost silenciar avisos. One
// component makes that impossible.

const actionsOpen = ref(false);
const actionsRow = ref(null);

function openActions(row) {
  actionsRow.value = row;
  actionsOpen.value = true;
}

// El detalle del ingreso tiene dirección propia (`?income=`): así la fila puede
// publicarla en un enlace, y recargar o compartir la URL reabre la capa.
// Deliberadamente NO es un ephemeralParam — esos se borran en el setup, que es
// por qué `?focus=` no sobrevive a una recarga.
const {
  openId: detailIncomeId,
  isOpen: detailOpen,
  toFor: incomeDetailTo,
  open: openDetailById,
  close: closeIncomeDetail,
} = useDetailQueryParam('income');

function openIncomeDetail(row) {
  openDetailById(row.id);
}

/** Row whose duplicate prefill is being fetched, so its kebab can say so. */
const duplicatingId = ref(null);

/**
 * Open the next period of a recurring income: the server builds the prefill
 * (always expected, with the hosting cycle's date when it can work it out)
 * and the form opens on it. Nothing is written until Guardar, which is the
 * point — the date almost always needs a look first.
 */
async function duplicateIncome(row) {
  // One at a time. The action menu closes on click, so nothing on screen
  // would otherwise say the first request is still running, and a second
  // click would race a second draft into the same form.
  if (duplicatingId.value) return;
  duplicatingId.value = row.id;
  let result;
  try {
    result = await store.fetchIncomeDuplicateDraft(row.id);
  } finally {
    duplicatingId.value = null;
  }
  if (!result.success) {
    notify.error({
      title: 'No se pudo preparar el duplicado',
      detail: result.message || '',
    });
    return;
  }
  closeIncomeDetail();
  openSeededModal(result.data);
}

function toggleMute(row) {
  if (row.reminders_muted) unmuteIncome(row);
  else openMuteModal(row);
}

async function loadRecords() {
  await store.fetchRecords('incomes');
}

// -------------------------------------------------------------------
// Post-create assign offer (the Vástago gap)
// -------------------------------------------------------------------

const pendingAssignProject = ref(null);
const assignOfferOpen = ref(false);

function onProjectCreated(project) {
  const backlog = (project.unlinked_hostings_count ?? 0)
    + (project.unlinked_incomes_count ?? 0);
  pendingAssignProject.value = backlog > 0 ? project : null;
}

// The offer waits for the form to close: the preview it loads is
// server-fresh, so a record just saved by that form is already (correctly)
// absent from it — and the project outlives a cancelled form on purpose.
watch(isModalOpen, (open) => {
  if (!open && pendingAssignProject.value) {
    assignOfferOpen.value = true;
  }
});

function dismissAssignOffer() {
  assignOfferOpen.value = false;
  pendingAssignProject.value = null;
}

async function onUnlinkedAssigned() {
  dismissAssignOffer();
  await loadRecords();
}

onMounted(async () => {
  // ?project=<id> — deep link from the /panel/projects counts; the URL pins
  // accounting_incomeTab=all because the landing tab hides settled rows.
  const projectParam = Number(consumeParam('project'));
  if (Number.isInteger(projectParam) && projectParam > 0) {
    currentFilters.projects = [projectParam];
  }
  // Project filter options come from the full catalog (history.vue
  // pattern); the store swallows failures, so an error just means a
  // smaller dropdown, never a blocked page.
  projectsStore.fetchProjects();
  // Sequential on purpose: the landing mode must be known before rows render
  // (no mode flash), and fetchSettings shares store.isLoading with the rows
  // fetch — in parallel, whichever finishes first would flash the empty state.
  await initFromSettings();
  await loadRecords();
  // ?focus=<id> reveals the row (navigation back from Cuentas de cobro).
  // Flashing alone was not enough: with PAGE_SIZE rows per page the target
  // is often not rendered at all, and even when it is the operator has no
  // idea where on the page it landed.
  await revealFocusedRow(Number(consumeParam('focus')));
});

/**
 * Bring the deep-linked row into view: jump to the page holding it, scroll
 * to it, then flash it.
 */
async function revealFocusedRow(focusId) {
  if (!focusId) return;
  const index = sortedRecords.value.findIndex((row) => row.id === focusId);
  if (index === -1) return;
  // The grouped view renders the whole filtered set, so it never paginates.
  if (!isGrouped.value) {
    currentPage.value = Math.floor(index / PAGE_SIZE) + 1;
  }
  lastMutatedId.value = focusId;
  await nextTick();
  if (typeof document === 'undefined') return;
  const element = document.querySelector(`[data-testid="accounting-row-${focusId}"]`);
  if (element && typeof element.scrollIntoView === 'function') {
    element.scrollIntoView({ block: 'center' });
  }
  setTimeout(() => {
    if (lastMutatedId.value === focusId) lastMutatedId.value = null;
  }, 2500);
}
usePanelRefresh(loadRecords);
</script>
