<template>
  <div :class="PAGE_MAX_WIDTH">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">Historial</h1>
      <p class="text-sm text-text-subtle mt-1">
        Qué se cambió en el módulo contable y a quién le salió cada correo automático.
        Solo lectura.
      </p>
    </div>

    <AccountingSubnav active="history" />

    <BaseSegmented
      v-model="tab"
      :options="TAB_OPTIONS"
      class="mb-5"
      data-testid="history-tab"
    />

    <!-- Filters — changes -->
    <div v-if="tab === 'changes'" class="bg-surface border border-border-muted rounded-xl shadow-sm p-4 mb-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <BaseFormField label="Entidad" size="sm">
          <BaseSelect
            v-model="filters.entity_type"
            size="sm"
            :options="entityTypeOptions"
            data-testid="history-filter-entity"
          />
        </BaseFormField>
        <BaseFormField label="Acción" size="sm">
          <BaseSelect
            v-model="filters.action"
            size="sm"
            :options="actionOptions"
            data-testid="history-filter-action"
          />
        </BaseFormField>
        <BaseFormField label="Usuario" size="sm">
          <BaseInput
            v-model="filters.actor"
            size="sm"
            placeholder="Buscar por usuario..."
            data-testid="history-filter-actor"
          />
        </BaseFormField>
        <BaseFormField label="Desde" size="sm">
          <BaseInput v-model="filters.date_from" size="sm" type="date" />
        </BaseFormField>
        <BaseFormField label="Hasta" size="sm">
          <BaseInput v-model="filters.date_to" size="sm" type="date" />
        </BaseFormField>
      </div>
    </div>

    <!-- Filters — sends -->
    <div v-else class="bg-surface border border-border-muted rounded-xl shadow-sm p-4 mb-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <BaseFormField label="Aviso" size="sm">
          <BaseSelect
            v-model="emailFilters.template_key"
            size="sm"
            :options="templateKeyOptions"
            data-testid="email-log-filter-template"
          />
        </BaseFormField>
        <BaseFormField label="Estado" size="sm">
          <BaseSelect
            v-model="emailFilters.status"
            size="sm"
            :options="statusOptions"
            data-testid="email-log-filter-status"
          />
        </BaseFormField>
        <BaseFormField label="Destinatario" size="sm">
          <BaseInput
            v-model="emailFilters.recipient"
            size="sm"
            placeholder="Buscar por correo..."
            data-testid="email-log-filter-recipient"
          />
        </BaseFormField>
        <BaseFormField label="Desde" size="sm">
          <BaseInput v-model="emailFilters.date_from" size="sm" type="date" />
        </BaseFormField>
        <BaseFormField label="Hasta" size="sm">
          <BaseInput v-model="emailFilters.date_to" size="sm" type="date" />
        </BaseFormField>
      </div>
    </div>

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === errorKey"
      :title="tab === 'changes' ? 'No se pudo cargar el historial' : 'No se pudo cargar el registro de envíos'"
      :retrying="store.isLoading"
      @retry="load(currentPage)"
    />

    <!-- Loading -->
    <div v-else-if="store.isLoading" class="text-center py-16 text-text-subtle text-sm">
      {{ tab === 'changes' ? 'Cargando historial...' : 'Cargando envíos...' }}
    </div>

    <template v-else>
      <ChangelogTable v-if="tab === 'changes'" :entries="store.changelog.results" />
      <EmailLogTable v-else :entries="store.emailLog.results" />

      <!-- Server-side pagination -->
      <div
        v-if="totalCount > 0"
        class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mt-4"
      >
        <p class="text-xs text-text-muted text-center sm:text-left" data-testid="history-page-info">
          Página {{ currentPage }} de {{ totalPages }} —
          {{ totalCount }} {{ countLabel }}
        </p>
        <BasePagination
          :current-page="currentPage"
          :total-pages="totalPages"
          @prev="goToPage(currentPage - 1)"
          @next="goToPage(currentPage + 1)"
          @go="goToPage"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import ChangelogTable from '~/components/accounting/ChangelogTable.vue';
import EmailLogTable from '~/components/accounting/EmailLogTable.vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import BaseSelect from '~/components/base/BaseSelect.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingStore } from '~/stores/accounting';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();

const TAB_OPTIONS = [
  { value: 'changes', label: 'Cambios', testId: 'history-tab-changes' },
  { value: 'sends', label: 'Envíos', testId: 'history-tab-sends' },
];

const tab = ref('changes');

const entityTypeOptions = [
  { value: '', label: 'Todas' },
  { value: 'income', label: 'Ingreso' },
  { value: 'expense', label: 'Gasto' },
  { value: 'hosting', label: 'Hosting' },
  { value: 'pocket', label: 'Bolsillo' },
  { value: 'recurring', label: 'Pago recurrente' },
  { value: 'ads', label: 'Ads' },
  { value: 'card_snapshot', label: 'Saldo tarjeta' },
  { value: 'credit_card', label: 'Tarjeta de crédito' },
  { value: 'statement', label: 'Extracto de tarjeta' },
  { value: 'statement_tx', label: 'Transacción de extracto' },
  { value: 'merchant_alias', label: 'Alias de comercio' },
  { value: 'settings', label: 'Configuración' },
];

const actionOptions = [
  { value: '', label: 'Todas' },
  { value: 'created', label: 'Creado' },
  { value: 'updated', label: 'Actualizado' },
  { value: 'deleted', label: 'Eliminado' },
];

// Mirrors EMAIL_TEMPLATE_LABELS in content/serializers/accounting.py.
const templateKeyOptions = [
  { value: '', label: 'Todos' },
  { value: 'accounting_change', label: 'Cambio contable' },
  { value: 'accounting_card_reminder', label: 'Recordatorio de deuda de tarjetas' },
  { value: 'accounting_statement_reminder', label: 'Recordatorio de extractos' },
  { value: 'accounting_payment_calendar', label: 'Calendario de cobros y pagos' },
  { value: 'collection_account_sent', label: 'Cuenta de cobro' },
  { value: 'payment_status_team', label: 'Pago de hosting' },
];

const statusOptions = [
  { value: '', label: 'Todos' },
  { value: 'sent', label: 'Enviado' },
  { value: 'delivered', label: 'Entregado' },
  { value: 'bounced', label: 'Rebotado' },
  { value: 'failed', label: 'Fallido' },
];

const filters = reactive({
  entity_type: '',
  action: '',
  actor: '',
  date_from: '',
  date_to: '',
});

const emailFilters = reactive({
  template_key: '',
  status: '',
  recipient: '',
  date_from: '',
  date_to: '',
});

const isChanges = computed(() => tab.value === 'changes');
const currentPage = computed(() =>
  isChanges.value ? store.changelog.page : store.emailLog.page,
);
const totalPages = computed(() =>
  isChanges.value ? store.changelog.numPages : store.emailLog.numPages,
);
const totalCount = computed(() =>
  isChanges.value ? store.changelog.count : store.emailLog.count,
);
const errorKey = computed(() => (isChanges.value ? 'changelog_failed' : 'email_log_failed'));
const countLabel = computed(() => {
  const plural = totalCount.value === 1 ? '' : 's';
  return isChanges.value ? `cambio${plural}` : `envío${plural}`;
});

function activeParams() {
  const source = isChanges.value ? filters : emailFilters;
  const params = {};
  Object.entries(source).forEach(([key, value]) => {
    const trimmed = String(value || '').trim();
    if (trimmed) params[key] = trimmed;
  });
  return params;
}

async function load(page = 1) {
  const params = { page, ...activeParams() };
  const result = isChanges.value
    ? await store.fetchChangelog(params)
    : await store.fetchEmailLog(params);
  if (!result.success) {
    notify.error({
      title: isChanges.value
        ? 'No se pudo cargar el historial'
        : 'No se pudo cargar el registro de envíos',
      detail: result.message,
    });
  }
}

function goToPage(page) {
  const target = Math.min(Math.max(1, page), totalPages.value || 1);
  if (target === currentPage.value) return;
  load(target);
}

// Selects and dates refetch immediately; the free-text inputs are debounced.
watch(
  () => [
    filters.entity_type, filters.action, filters.date_from, filters.date_to,
    emailFilters.template_key, emailFilters.status,
    emailFilters.date_from, emailFilters.date_to,
  ],
  () => load(1),
);

// Switching tabs loads the other list from page 1; the store keeps each
// side's results so coming back does not blank the table.
watch(tab, () => load(1));

let textTimer = null;
watch(
  () => [filters.actor, emailFilters.recipient],
  () => {
    if (textTimer) clearTimeout(textTimer);
    textTimer = setTimeout(() => load(1), 300);
  },
);

onMounted(() => load(1));
usePanelRefresh(() => load(currentPage.value));
onBeforeUnmount(() => {
  if (textTimer) clearTimeout(textTimer);
});
</script>
