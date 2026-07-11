<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">Historial</h1>
      <p class="text-sm text-text-subtle mt-1">
        Registro de auditoría de todos los cambios del módulo contable. Solo lectura.
      </p>
    </div>

    <AccountingSubnav active="history" />

    <!-- Filters -->
    <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-4 mb-5">
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

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'changelog_failed'"
      title="No se pudo cargar el historial"
      :retrying="store.isLoading"
      @retry="load(store.changelog.page)"
    />

    <!-- Loading -->
    <div v-else-if="store.isLoading" class="text-center py-16 text-text-subtle text-sm">
      Cargando historial...
    </div>

    <template v-else>
      <ChangelogTable :entries="store.changelog.results" />

      <!-- Server-side pagination -->
      <div
        v-if="store.changelog.count > 0"
        class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mt-4"
      >
        <p class="text-xs text-text-muted text-center sm:text-left" data-testid="history-page-info">
          Página {{ store.changelog.page }} de {{ store.changelog.numPages }} —
          {{ store.changelog.count }} cambio{{ store.changelog.count === 1 ? '' : 's' }}
        </p>
        <BasePagination
          :current-page="store.changelog.page"
          :total-pages="store.changelog.numPages"
          @prev="goToPage(store.changelog.page - 1)"
          @next="goToPage(store.changelog.page + 1)"
          @go="goToPage"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, watch } from 'vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import ChangelogTable from '~/components/accounting/ChangelogTable.vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseSelect from '~/components/base/BaseSelect.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingStore } from '~/stores/accounting';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();

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

const filters = reactive({
  entity_type: '',
  action: '',
  actor: '',
  date_from: '',
  date_to: '',
});

function activeParams() {
  const params = {};
  Object.entries(filters).forEach(([key, value]) => {
    const trimmed = String(value || '').trim();
    if (trimmed) params[key] = trimmed;
  });
  return params;
}

async function load(page = 1) {
  const result = await store.fetchChangelog({ page, ...activeParams() });
  if (!result.success) {
    notify.error({ title: 'No se pudo cargar el historial', detail: result.message });
  }
}

function goToPage(page) {
  const target = Math.min(Math.max(1, page), store.changelog.numPages || 1);
  if (target === store.changelog.page) return;
  load(target);
}

// Selects and dates refetch immediately; the actor text input is debounced.
watch(
  () => [filters.entity_type, filters.action, filters.date_from, filters.date_to],
  () => load(1),
);

let actorTimer = null;
watch(
  () => filters.actor,
  () => {
    if (actorTimer) clearTimeout(actorTimer);
    actorTimer = setTimeout(() => load(1), 300);
  },
);

onMounted(() => load(1));
usePanelRefresh(() => load(store.changelog.page));
onBeforeUnmount(() => {
  if (actorTimer) clearTimeout(actorTimer);
});
</script>
