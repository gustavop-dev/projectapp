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

    <!-- Loading -->
    <div v-if="store.isLoading" class="text-center py-12 text-text-subtle text-sm">
      Cargando…
    </div>

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
      class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-x-auto"
    >
      <table class="w-full min-w-[900px]">
        <thead class="sticky top-0 z-10 bg-surface">
          <tr class="border-b border-border-muted text-left">
            <th class="px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider w-12">ID</th>
            <th
              class="px-6 py-3 text-xs font-medium uppercase tracking-wider cursor-pointer select-none transition-colors"
              :class="sortKey === 'client_name' ? 'text-text-brand' : 'text-text-muted hover:text-text-brand'"
              @click="toggleSort('client_name')"
            >
              <span class="inline-flex items-center gap-1">
                Cliente
                <SortIcon :active="sortKey === 'client_name'" :asc="sortDir === 'asc'" />
              </span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Título</th>
            <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Estado</th>
            <th
              class="px-6 py-3 text-xs font-medium uppercase tracking-wider cursor-pointer select-none transition-colors"
              :class="sortKey === 'investment_amount' ? 'text-text-brand' : 'text-text-muted hover:text-text-brand'"
              @click="toggleSort('investment_amount')"
            >
              <span class="inline-flex items-center gap-1">
                Inversión
                <SortIcon :active="sortKey === 'investment_amount'" :asc="sortDir === 'asc'" />
              </span>
            </th>
            <th
              class="px-6 py-3 text-xs font-medium uppercase tracking-wider cursor-pointer select-none transition-colors hidden sm:table-cell"
              :class="sortKey === 'created_at' ? 'text-text-brand' : 'text-text-muted hover:text-text-brand'"
              @click="toggleSort('created_at')"
            >
              <span class="inline-flex items-center gap-1">
                Creado
                <SortIcon :active="sortKey === 'created_at'" :asc="sortDir === 'asc'" />
              </span>
            </th>
            <th
              class="px-6 py-3 text-xs font-medium uppercase tracking-wider cursor-pointer select-none transition-colors"
              :class="sortKey === 'last_viewed_at' ? 'text-text-brand' : 'text-text-muted hover:text-text-brand'"
              @click="toggleSort('last_viewed_at')"
            >
              <span class="inline-flex items-center gap-1">
                Última vista
                <SortIcon :active="sortKey === 'last_viewed_at'" :asc="sortDir === 'asc'" />
              </span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
          <tr
            v-for="d in paginatedDiagnostics"
            :key="d.id"
            class="transition-colors cursor-pointer hover:bg-surface-muted dark:hover:bg-gray-700/50"
            :data-testid="`diagnostic-row-${d.id}`"
            @click="navigateToDiagnostic(d.id, $event)"
          >
            <td class="px-4 py-4 text-xs text-text-subtle tabular-nums">#{{ d.id }}</td>
            <td class="px-6 py-4">
              <div class="text-sm font-medium text-text-default">{{ d.client?.name || '—' }}</div>
              <div v-if="d.client?.email" class="text-xs text-text-muted mt-0.5">{{ d.client.email }}</div>
            </td>
            <td class="px-6 py-4 text-sm text-text-default">{{ d.title }}</td>
            <td class="px-6 py-4">
              <DiagnosticStatusBadge :status="d.status" />
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
                <span class="text-[10px] text-text-subtle ml-1">({{ d.view_count }} vistas)</span>
              </span>
              <span v-else class="text-text-subtle">—</span>
            </td>
            <td class="px-6 py-4" @click.stop>
              <button
                class="p-1.5 rounded-lg hover:bg-surface-raised transition-colors text-text-subtle hover:text-text-default"
                @click.stop="actionsModalDiagnostic = d"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="sortedDiagnostics.length" class="flex items-center justify-between px-6 py-3 border-t border-border-muted">
        <span class="text-xs text-text-subtle">
          Mostrando {{ paginationStart }}–{{ paginationEnd }} de {{ sortedDiagnostics.length }} diagnóstico{{ sortedDiagnostics.length !== 1 ? 's' : '' }}
        </span>
        <div v-if="totalPages > 1" class="flex gap-1">
          <button
            v-for="page in totalPages"
            :key="page"
            class="w-8 h-8 rounded-lg text-xs font-medium transition-colors"
            :class="currentPage === page
              ? 'bg-primary text-white'
              : 'text-text-muted hover:bg-surface-raised'"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
        </div>
      </div>
    </div>

    <!-- Actions modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="actionsModalDiagnostic"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="actionsModalDiagnostic = null"
        >
          <div class="bg-surface rounded-2xl shadow-2xl max-w-md w-full border border-border-muted">
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
                class="w-8 h-8 rounded-lg flex items-center justify-center text-text-subtle hover:bg-surface-raised transition-colors"
                @click="actionsModalDiagnostic = null"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                <span class="w-9 h-9 rounded-lg flex items-center justify-center text-lg bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400">👁️</span>
                <span class="text-sm font-medium text-purple-700 dark:text-purple-300">Ver vista pública</span>
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
                class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors hover:bg-red-50 dark:hover:bg-red-500/10"
                @click="handleDelete(actionsModalDiagnostic)"
              >
                <span class="w-9 h-9 rounded-lg flex items-center justify-center text-lg bg-red-50 text-red-500 dark:bg-red-500/10 dark:text-red-400">🗑️</span>
                <span class="text-sm font-medium text-red-600 dark:text-red-400">Eliminar</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import DiagnosticStatusBadge from '~/components/WebAppDiagnostic/DiagnosticStatusBadge.vue';
import DiagnosticFilterPanel from '~/components/WebAppDiagnostic/DiagnosticFilterPanel.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useDiagnosticFilters } from '~/composables/useDiagnosticFilters';
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
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const searchQuery = ref('');
const actionsModalDiagnostic = ref(null);
const copiedId = ref(null);
const sortKey = ref('created_at');
const sortDir = ref('desc');
const currentPage = ref(1);
const pageSize = 15;

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
    onConfirm: () => store.remove(target.id),
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

onMounted(() => store.fetchAll());
usePanelRefresh(() => store.fetchAll());
</script>

<style scoped>
.fade-modal-enter-active,
.fade-modal-leave-active {
  transition: opacity 0.2s ease;
}
.fade-modal-enter-from,
.fade-modal-leave-to {
  opacity: 0;
}
</style>
