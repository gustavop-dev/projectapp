<template>
  <div>
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />

    <header class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <div>
        <h1 class="text-2xl font-light text-text-default">Diagnósticos de aplicaciones</h1>
        <p class="text-sm text-text-subtle mt-0.5">Seguimiento de diagnósticos técnicos por cliente</p>
      </div>
      <div class="flex items-center gap-3">
        <BaseButton
          as="NuxtLink"
          variant="secondary"
          size="md"
          :to="localePath('/panel/defaults?mode=diagnostic')"
          title="Configurar valores por defecto de los diagnósticos"
          data-testid="diagnostics-defaults-link"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Valores por Defecto
        </BaseButton>
        <BaseButton
          as="NuxtLink"
          variant="primary"
          size="md"
          :to="localePath('/panel/diagnostics/create')"
          class="shrink-0"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo diagnóstico
        </BaseButton>
      </div>
    </header>

    <!-- KPI strip -->
    <DiagnosticDashboard v-if="store.diagnostics.length" :diagnostics="store.diagnostics" />

    <!-- Saved filter tabs -->
    <ProposalFilterTabs
      :tabs="savedTabs"
      :active-tab-id="filterTabId"
      :is-tab-limit-reached="isTabLimitReached"
      @select="selectFilterTab"
      @create="handleCreateFilterTab"
      @rename="renameFilterTab"
      @delete="deleteFilterTab"
    />

    <!-- Search + Filter toggle -->
    <div class="flex flex-col sm:flex-row gap-3 mb-4">
      <div class="relative flex-1 max-w-sm">
        <svg
          class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle pointer-events-none z-10"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <BaseInput
          v-model="searchQuery"
          type="text"
          placeholder="Buscar por título o cliente..."
          data-testid="diagnostics-search-input"
          class="!pl-10"
        />
      </div>
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
    </div>

    <!-- Filter panel -->
    <DiagnosticFilterPanel
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :filter-count="activeFilterCount"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
    />

    <!-- Batch actions bar -->
    <div
      v-if="selectedIds.length"
      class="flex flex-wrap items-center gap-3 mb-3 px-4 py-2.5 bg-primary-soft border border-primary/20 rounded-xl"
      data-testid="diagnostics-batch-bar"
    >
      <span class="text-sm font-medium text-text-brand">
        {{ selectedIds.length }} seleccionado{{ selectedIds.length !== 1 ? 's' : '' }}
      </span>
      <div class="ml-auto flex items-center gap-2">
        <BaseButton variant="secondary" size="sm" :loading="store.isUpdating" @click="handleBulk('finish')">
          Finalizar aceptados
        </BaseButton>
        <BaseButton variant="danger" size="sm" :loading="store.isUpdating" @click="handleBulk('delete')">
          Eliminar
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="clearSelection">Cancelar</BaseButton>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div
      v-if="store.isLoading"
      class="bg-surface rounded-xl shadow-card border border-border-muted p-6 space-y-4"
      data-testid="diagnostics-loading"
      aria-busy="true"
    >
      <BaseSkeleton variant="line" class="w-1/3" />
      <BaseSkeleton v-for="n in 5" :key="n" variant="line" class="w-full" />
    </div>

    <!-- Load error (distinct from the empty state) -->
    <BaseEmptyState
      v-else-if="store.error && !store.diagnostics.length"
      data-testid="diagnostics-error-state"
      :description="store.error"
    >
      <template #icon>
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      </template>
      <template #actions>
        <BaseButton variant="secondary" size="md" @click="loadDiagnostics">
          Reintentar
        </BaseButton>
      </template>
    </BaseEmptyState>

    <!-- Empty state -->
    <BaseEmptyState
      v-else-if="!sortedDiagnostics.length"
      :description="activeFilterCount || searchQuery ? 'No hay diagnósticos que coincidan con los filtros.' : 'Aún no has creado diagnósticos.'"
    >
      <template #icon>
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </template>
      <template v-if="!store.diagnostics.length" #actions>
        <BaseButton as="NuxtLink" variant="primary" size="md" :to="localePath('/panel/diagnostics/create')">
          Crear el primero
        </BaseButton>
      </template>
    </BaseEmptyState>

    <!-- Table -->
    <div
      v-else
      class="bg-surface rounded-xl shadow-card border border-border-muted overflow-x-auto"
    >
      <table class="w-full min-w-[900px]">
        <thead class="sticky top-0 z-10 bg-surface">
          <tr class="border-b border-border-muted text-left">
            <th scope="col" class="pl-4 pr-1 py-3 w-10">
              <BaseCheckbox
                :model-value="pageAllSelected"
                aria-label="Seleccionar los diagnósticos de esta página"
                @update:model-value="toggleSelectPage"
              />
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-xs font-medium uppercase tracking-wider"
              :class="sortKey === 'client_name' ? 'text-text-brand' : 'text-text-muted'"
              :aria-sort="ariaSortFor('client_name')"
            >
              <button
                type="button"
                class="inline-flex items-center gap-1 uppercase tracking-wider hover:text-text-brand rounded focus:outline-none focus:ring-2 focus:ring-focus-ring/40 motion-safe:transition-colors motion-safe:duration-fast"
                @click="toggleSort('client_name')"
              >
                Cliente
                <SortIcon :active="sortKey === 'client_name'" :asc="sortDir === 'asc'" />
              </button>
            </th>
            <th scope="col" class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Título</th>
            <th scope="col" class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Estado</th>
            <th
              scope="col"
              class="px-6 py-3 text-xs font-medium uppercase tracking-wider"
              :class="sortKey === 'investment_amount' ? 'text-text-brand' : 'text-text-muted'"
              :aria-sort="ariaSortFor('investment_amount')"
            >
              <button
                type="button"
                class="inline-flex items-center gap-1 uppercase tracking-wider hover:text-text-brand rounded focus:outline-none focus:ring-2 focus:ring-focus-ring/40 motion-safe:transition-colors motion-safe:duration-fast"
                @click="toggleSort('investment_amount')"
              >
                Inversión
                <SortIcon :active="sortKey === 'investment_amount'" :asc="sortDir === 'asc'" />
              </button>
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-xs font-medium uppercase tracking-wider hidden sm:table-cell"
              :class="sortKey === 'created_at' ? 'text-text-brand' : 'text-text-muted'"
              :aria-sort="ariaSortFor('created_at')"
            >
              <button
                type="button"
                class="inline-flex items-center gap-1 uppercase tracking-wider hover:text-text-brand rounded focus:outline-none focus:ring-2 focus:ring-focus-ring/40 motion-safe:transition-colors motion-safe:duration-fast"
                @click="toggleSort('created_at')"
              >
                Creado
                <SortIcon :active="sortKey === 'created_at'" :asc="sortDir === 'asc'" />
              </button>
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-xs font-medium uppercase tracking-wider"
              :class="sortKey === 'last_viewed_at' ? 'text-text-brand' : 'text-text-muted'"
              :aria-sort="ariaSortFor('last_viewed_at')"
            >
              <button
                type="button"
                class="inline-flex items-center gap-1 uppercase tracking-wider hover:text-text-brand rounded focus:outline-none focus:ring-2 focus:ring-focus-ring/40 motion-safe:transition-colors motion-safe:duration-fast"
                @click="toggleSort('last_viewed_at')"
              >
                Última vista
                <SortIcon :active="sortKey === 'last_viewed_at'" :asc="sortDir === 'asc'" />
              </button>
            </th>
            <th scope="col" class="px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider w-14 hidden lg:table-cell">ID</th>
            <th scope="col" class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border-muted">
          <tr
            v-for="d in paginatedDiagnostics"
            :key="d.id"
            class="transition-colors cursor-pointer hover:bg-surface-muted"
            :data-testid="`diagnostic-row-${d.id}`"
            @click="navigateToDiagnostic(d.id, $event)"
          >
            <td class="pl-4 pr-1 py-4" @click.stop>
              <BaseCheckbox
                v-model="selectedIds"
                :value="d.id"
                :aria-label="`Seleccionar ${d.title}`"
              />
            </td>
            <td class="px-6 py-4">
              <div class="text-sm font-medium text-text-default">{{ d.client?.name || '—' }}</div>
              <div v-if="d.client?.email" class="text-xs text-text-muted mt-0.5">{{ d.client.email }}</div>
            </td>
            <td class="px-6 py-4 text-sm text-text-default">
              <div class="truncate max-w-[22rem]" :title="d.title">{{ d.title }}</div>
            </td>
            <td class="px-6 py-4">
              <div class="flex flex-col items-start gap-1">
                <DiagnosticStatusBadge :status="d.status" />
                <span
                  v-if="attentionById[d.id]"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-medium"
                  :class="ATTENTION_TONE_CLASSES[attentionById[d.id].tone]"
                  :data-testid="`diagnostic-attention-${d.id}`"
                >{{ attentionById[d.id].label }}</span>
                <DiagnosticExpirationChip
                  :expires-at="d.expires_at"
                  :is-expired="d.is_expired"
                  :days-remaining="d.days_remaining"
                />
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-text-muted tabular-nums">
              <span v-if="d.investment_amount">{{ formatMoney(d.investment_amount) }} {{ d.currency }}</span>
              <span v-else class="text-text-subtle">—</span>
            </td>
            <td class="px-6 py-4 text-xs text-text-muted hidden sm:table-cell">
              <span v-if="d.created_at">{{ formatDate(d.created_at) }}</span>
              <span v-else class="text-text-subtle">—</span>
            </td>
            <td class="px-6 py-4 text-xs text-text-muted">
              <span v-if="d.last_viewed_at">
                {{ formatDate(d.last_viewed_at) }}
                <span class="text-2xs text-text-subtle ml-1">({{ d.view_count }} vistas)</span>
              </span>
              <span v-else class="text-text-subtle">—</span>
            </td>
            <td class="px-4 py-4 text-xs text-text-subtle tabular-nums hidden lg:table-cell">#{{ d.id }}</td>
            <td class="px-6 py-4" @click.stop>
              <button
                type="button"
                class="p-3 -m-1.5 rounded-lg hover:bg-surface-raised motion-safe:transition-colors motion-safe:duration-fast text-text-subtle hover:text-text-default focus:outline-none focus:ring-2 focus:ring-focus-ring/40"
                :aria-label="`Acciones de ${d.title}`"
                @click.stop="actionsModalDiagnostic = d"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <BasePagination
        v-if="sortedDiagnostics.length"
        :always-show="true"
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-items="sortedDiagnostics.length"
        :range-from="paginationStart"
        :range-to="paginationEnd"
        aria-label="Paginación de diagnósticos"
        class="px-6 border-t border-border-muted"
        @prev="goToPage(currentPage - 1)"
        @next="goToPage(currentPage + 1)"
        @go="goToPage"
      />
    </div>

    <!-- Actions modal -->
    <BaseModal v-model="actionsModalOpen" size="md">
      <template v-if="actionsModalDiagnostic">
        <div class="px-6 py-4 border-b border-border-muted flex items-center justify-between">
          <div class="min-w-0">
            <h3 class="text-base font-bold text-text-default truncate">
              {{ actionsModalDiagnostic.title }}
            </h3>
            <p class="text-xs text-text-muted mt-0.5">
              {{ actionsModalDiagnostic.client?.name || '—' }}
              <span v-if="actionsModalDiagnostic.created_at" class="ml-1 text-text-subtle">
                · {{ formatDate(actionsModalDiagnostic.created_at) }}
              </span>
            </p>
          </div>
          <button
            type="button"
            class="w-11 h-11 rounded-lg flex items-center justify-center text-text-subtle hover:bg-surface-raised motion-safe:transition-colors motion-safe:duration-fast focus:outline-none focus:ring-2 focus:ring-focus-ring/40"
            aria-label="Cerrar"
            @click="actionsModalDiagnostic = null"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-3 space-y-1 max-h-[60vh] overflow-y-auto">
              <NuxtLink
                :to="localePath(`/panel/diagnostics/${actionsModalDiagnostic.id}/edit`)"
                class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors hover:bg-surface-raised"
                @click="actionsModalDiagnostic = null"
              >
                <span class="w-9 h-9 rounded-lg flex items-center justify-center text-lg bg-surface-raised">✏️</span>
                <span class="text-sm font-medium text-text-default">Abrir editor</span>
              </NuxtLink>

              <a
                v-if="actionsModalDiagnostic.public_url"
                :href="actionsModalDiagnostic.public_url"
                target="_blank"
                rel="noopener noreferrer"
                class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors hover:bg-surface-raised"
              >
                <span class="w-9 h-9 rounded-lg flex items-center justify-center text-lg bg-primary-soft text-text-brand">👁️</span>
                <span class="text-sm font-medium text-text-brand">Ver vista pública</span>
              </a>

              <button
                v-if="actionsModalDiagnostic.public_url"
                type="button"
                class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors hover:bg-surface-raised"
                @click="handleCopyLink(actionsModalDiagnostic)"
              >
                <span class="w-9 h-9 rounded-lg flex items-center justify-center text-lg"
                  :class="copiedId === actionsModalDiagnostic.id
                    ? 'bg-primary-soft text-text-brand'
                    : 'bg-surface-raised'"
                >{{ copiedId === actionsModalDiagnostic.id ? '✅' : '🔗' }}</span>
                <span class="text-sm font-medium"
                  :class="copiedId === actionsModalDiagnostic.id
                    ? 'text-text-brand'
                    : 'text-text-default'"
                >{{ copiedId === actionsModalDiagnostic.id ? '¡Enlace copiado!' : 'Copiar enlace' }}</span>
              </button>

              <button
                type="button"
                class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors hover:bg-danger-soft"
                @click="handleDelete(actionsModalDiagnostic)"
              >
                <span class="w-9 h-9 rounded-lg flex items-center justify-center text-lg bg-danger-soft text-danger-strong">🗑️</span>
                <span class="text-sm font-medium text-danger-strong">Eliminar</span>
              </button>
        </div>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import DiagnosticStatusBadge from '~/components/WebAppDiagnostic/DiagnosticStatusBadge.vue';
import DiagnosticExpirationChip from '~/components/WebAppDiagnostic/DiagnosticExpirationChip.vue';
import DiagnosticDashboard from '~/components/WebAppDiagnostic/admin/DiagnosticDashboard.vue';
import DiagnosticFilterPanel from '~/components/WebAppDiagnostic/DiagnosticFilterPanel.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { getDiagnosticAttention, ATTENTION_TONE_CLASSES } from '~/utils/diagnosticAttention';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useDiagnosticFilters } from '~/composables/useDiagnosticFilters';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

/** Inline sort icon — chevron up/down SVG */
const SortIcon = {
  props: { active: Boolean, asc: Boolean },
  template: `
    <svg class="w-3 h-3 shrink-0 transition-opacity" :class="active ? 'opacity-100' : 'opacity-30'"
         fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path v-if="!active || asc" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 15l7-7 7 7"/>
      <path v-if="active && !asc" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/>
    </svg>
  `,
};

const moneyFormatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
const dateTimeFormatter = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

const localePath = useLocalePath();
const router = useRouter();
const store = useDiagnosticsStore();
const notify = usePanelNotify();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const searchQuery = ref('');
const actionsModalDiagnostic = ref(null);
const copiedId = ref(null);
const sortKey = ref('created_at');
const sortDir = ref('desc');
const currentPage = ref(1);
const pageSize = 15;
const selectedIds = ref([]);

const actionsModalOpen = computed({
  get: () => actionsModalDiagnostic.value !== null,
  set: (open) => { if (!open) actionsModalDiagnostic.value = null; },
});

function ariaSortFor(key) {
  if (sortKey.value !== key) return undefined;
  return sortDir.value === 'asc' ? 'ascending' : 'descending';
}

const {
  currentFilters,
  savedTabs,
  activeTabId: filterTabId,
  isFilterPanelOpen,
  activeFilterCount,
  isTabLimitReached,
  applyFilters,
  resetFilters,
  selectTab: selectFilterTab,
  saveTab,
  deleteTab: deleteFilterTab,
  renameTab: renameFilterTab,
} = useDiagnosticFilters();

function handleCreateFilterTab(name) {
  saveTab(name);
  isFilterPanelOpen.value = true;
}

function handleResetFilters() {
  resetFilters();
}

const filteredDiagnostics = computed(() => {
  const needle = searchQuery.value.trim().toLowerCase();
  const base = needle
    ? store.diagnostics.filter((d) => {
      const haystack = [
        d.title || '',
        d.client?.name || '',
        d.client?.email || '',
      ].join(' ').toLowerCase();
      return haystack.includes(needle);
    })
    : store.diagnostics;
  return applyFilters(base);
});

const sortedDiagnostics = computed(() => {
  const list = [...filteredDiagnostics.value];
  const sk = sortKey.value;
  const asc = sortDir.value === 'asc';

  list.sort((a, b) => {
    let va;
    let vb;
    if (sk === 'investment_amount') {
      va = Number(a.investment_amount || 0);
      vb = Number(b.investment_amount || 0);
    } else if (sk === 'client_name') {
      va = (a.client?.name || '').toLowerCase();
      vb = (b.client?.name || '').toLowerCase();
    } else if (sk === 'last_viewed_at') {
      va = a.last_viewed_at ? new Date(a.last_viewed_at).getTime() : 0;
      vb = b.last_viewed_at ? new Date(b.last_viewed_at).getTime() : 0;
    } else if (sk === 'created_at') {
      va = a.created_at ? new Date(a.created_at).getTime() : 0;
      vb = b.created_at ? new Date(b.created_at).getTime() : 0;
    } else {
      va = a[sk] || '';
      vb = b[sk] || '';
    }
    if (va < vb) return asc ? -1 : 1;
    if (va > vb) return asc ? 1 : -1;
    return 0;
  });
  return list;
});

const totalPages = computed(() => Math.ceil(sortedDiagnostics.value.length / pageSize));
const paginatedDiagnostics = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return sortedDiagnostics.value.slice(start, start + pageSize);
});
const paginationStart = computed(() => (currentPage.value - 1) * pageSize + 1);
const paginationEnd = computed(() =>
  Math.min(currentPage.value * pageSize, sortedDiagnostics.value.length),
);

function goToPage(page) {
  currentPage.value = Math.min(Math.max(1, page), totalPages.value);
}

const attentionById = computed(() => {
  const map = {};
  for (const d of paginatedDiagnostics.value) {
    const signal = getDiagnosticAttention(d);
    if (signal) map[d.id] = signal;
  }
  return map;
});

// ── Bulk selection ────────────────────────────────────────────────────
const pageAllSelected = computed(() =>
  paginatedDiagnostics.value.length > 0 &&
  paginatedDiagnostics.value.every((d) => selectedIds.value.includes(d.id)),
);

function toggleSelectPage(checked) {
  const pageIds = paginatedDiagnostics.value.map((d) => d.id);
  if (checked) {
    selectedIds.value = [...new Set([...selectedIds.value, ...pageIds])];
  } else {
    const pageSet = new Set(pageIds);
    selectedIds.value = selectedIds.value.filter((id) => !pageSet.has(id));
  }
}

function clearSelection() {
  selectedIds.value = [];
}

const BULK_CONFIRM = {
  delete: {
    title: 'Eliminar diagnósticos',
    message: (n) => `¿Eliminar ${n} diagnóstico${n !== 1 ? 's' : ''}? Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    success: (affected) => `${affected} diagnóstico${affected !== 1 ? 's' : ''} eliminado${affected !== 1 ? 's' : ''}.`,
  },
  finish: {
    title: 'Finalizar diagnósticos',
    message: (n) => `¿Marcar como finalizados los aceptados entre los ${n} seleccionados?`,
    variant: 'info',
    confirmText: 'Finalizar',
    success: (affected) => affected > 0
      ? `${affected} diagnóstico${affected !== 1 ? 's' : ''} finalizado${affected !== 1 ? 's' : ''}.`
      : 'Ninguno de los seleccionados estaba aceptado.',
  },
};

function handleBulk(action) {
  const ids = [...selectedIds.value];
  const copy = BULK_CONFIRM[action];
  if (!ids.length || !copy) return;
  requestConfirm({
    title: copy.title,
    message: copy.message(ids.length),
    variant: copy.variant,
    confirmText: copy.confirmText,
    onConfirm: async () => {
      const r = await store.bulkAction(ids, action);
      if (r?.success) {
        clearSelection();
        notify.success(copy.success(r.data?.affected ?? 0));
        if (action === 'finish') await loadDiagnostics();
      } else {
        notify.error({ title: r?.message || 'No se pudo aplicar la acción.', detail: r?.hint || '' });
      }
    },
  });
}

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortDir.value = 'desc';
  }
  currentPage.value = 1;
}

watch([searchQuery, currentFilters], () => { currentPage.value = 1; }, { deep: true });

function navigateToDiagnostic(id, event) {
  const path = localePath(`/panel/diagnostics/${id}/edit`);
  if (event?.ctrlKey || event?.metaKey) {
    window.open(path, '_blank');
  } else {
    router.push(path);
  }
}

function handleCopyLink(d) {
  if (!d?.public_url) return;
  navigator.clipboard.writeText(d.public_url).then(() => {
    copiedId.value = d.id;
    setTimeout(() => { copiedId.value = null; }, 1500);
  });
}

function handleDelete(d) {
  const target = d;
  actionsModalDiagnostic.value = null;
  requestConfirm({
    title: 'Eliminar diagnóstico',
    message: `¿Eliminar el diagnóstico "${target.title}"? Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const r = await store.remove(target.id);
      if (r?.success) {
        notify.success('Diagnóstico eliminado.');
      } else {
        notify.error({ title: r?.message || 'No se pudo eliminar el diagnóstico.', detail: r?.hint || '' });
      }
    },
  });
}

function formatMoney(amount) {
  const n = Number(amount);
  if (Number.isNaN(n)) return amount;
  return moneyFormatter.format(n);
}

function formatDate(iso) {
  if (!iso) return '';
  return dateTimeFormatter.format(new Date(iso));
}

async function loadDiagnostics() {
  const r = await store.fetchAll();
  if (!r?.success) {
    notify.error({ title: r?.message || 'No se pudieron cargar los diagnósticos.', detail: r?.hint || '' });
  }
}

onMounted(loadDiagnostics);
usePanelRefresh(loadDiagnostics);
</script>
