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
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-light text-text-default">Portfolio Works</h1>
      <BaseButton
        as="NuxtLink"
        variant="primary"
        size="md"
        :to="localePath('/panel/portfolio/create')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Proyecto
      </BaseButton>
    </div>

    <!-- Loading -->
    <div v-if="portfolioStore.isLoading" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-focus-ring/30 border-t-focus-ring rounded-full animate-spin" />
    </div>

    <div v-else>
      <div v-if="works.length === 0" class="bg-surface rounded-xl shadow-sm border border-border-muted px-6 py-12 text-center text-text-subtle text-sm">
        No hay proyectos aún. Crea el primero.
      </div>

      <!-- Mobile cards -->
      <div v-else class="sm:hidden space-y-3">
        <div v-for="work in pagedWorks" :key="work.id" class="bg-surface rounded-xl shadow-sm border border-border-muted p-4">
          <div class="flex items-start justify-between gap-3 mb-2">
            <NuxtLink :to="localePath(`/panel/portfolio/${work.id}/edit`)" class="text-sm font-medium text-text-default hover:text-text-brand transition-colors leading-tight">
              {{ work.title_es }}
            </NuxtLink>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0" :class="statusBadgeClass(work)">
              {{ statusLabel(work) }}
            </span>
          </div>
          <p class="text-xs text-text-subtle mb-3">{{ work.slug }} · {{ formatDate(work.published_at || work.created_at) }}</p>
          <div class="flex items-center gap-3">
            <NuxtLink :to="localePath(`/panel/portfolio/${work.id}/edit`)" class="text-xs text-text-brand font-medium">Editar</NuxtLink>
            <button class="text-xs text-text-muted hover:text-text-brand dark:hover:text-white transition-colors" @click="handleDuplicate(work)">Duplicar</button>
            <button class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors" @click="handleDelete(work)">Eliminar</button>
          </div>
        </div>
      </div>

      <!-- Desktop table -->
      <div class="hidden sm:block bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-border-muted text-left">
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Título</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Estado</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Orden</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Fecha</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border-muted">
              <tr v-for="work in pagedWorks" :key="work.id" class="hover:bg-surface-raised transition-colors">
                <td class="px-6 py-4">
                  <NuxtLink :to="localePath(`/panel/portfolio/${work.id}/edit`)" class="text-sm font-medium text-text-default hover:text-text-brand transition-colors">
                    {{ work.title_es }}
                  </NuxtLink>
                  <p class="text-xs text-text-subtle mt-0.5">{{ work.title_en }} · {{ work.slug }}</p>
                </td>
                <td class="px-6 py-4">
                  <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusBadgeClass(work)">
                    {{ statusLabel(work) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-text-muted">{{ work.order }}</td>
                <td class="px-6 py-4 text-sm text-text-muted">{{ formatDate(work.published_at || work.created_at) }}</td>
                <td class="px-6 py-4 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <NuxtLink :to="localePath(`/panel/portfolio/${work.id}/edit`)" class="text-xs text-text-muted hover:text-text-brand dark:hover:text-white transition-colors">Editar</NuxtLink>
                    <button class="text-xs text-text-muted hover:text-text-brand dark:hover:text-white transition-colors" @click="handleDuplicate(work)">Duplicar</button>
                    <button class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors" @click="handleDelete(work)">Eliminar</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <BasePagination
        v-if="works.length > 0"
        :current-page="worksPage"
        :total-pages="worksTotalPages"
        :total-items="worksTotalItems"
        :range-from="worksRangeFrom"
        :range-to="worksRangeTo"
        class="mt-4"
        @prev="worksPrev"
        @next="worksNext"
        @go="worksGoTo"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { usePortfolioWorksStore } from '~/stores/portfolio_works';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import BasePagination from '~/components/base/BasePagination.vue';
import { usePagination } from '~/composables/usePagination';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const portfolioStore = usePortfolioWorksStore();
const works = computed(() => portfolioStore.works);
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const {
  currentPage: worksPage,
  totalPages: worksTotalPages,
  totalItems: worksTotalItems,
  rangeFrom: worksRangeFrom,
  rangeTo: worksRangeTo,
  paginatedItems: pagedWorks,
  goTo: worksGoTo,
  next: worksNext,
  prev: worksPrev,
} = usePagination(works, { pageSize: 10 });

onMounted(() => { portfolioStore.fetchAdminWorks(); });
usePanelRefresh(() => portfolioStore.fetchAdminWorks());

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' });
}

function statusLabel(work) {
  return work.is_published ? 'Publicado' : 'Borrador';
}

function statusBadgeClass(work) {
  return work.is_published
    ? 'bg-primary-soft text-text-brand'
    : 'bg-surface-raised text-text-muted';
}

function handleDuplicate(work) {
  requestConfirm({
    title: 'Duplicar trabajo',
    message: `¿Duplicar "${work.title_es}"?`,
    variant: 'info',
    confirmText: 'Duplicar',
    onConfirm: () => portfolioStore.duplicateWork(work.id),
  });
}

function handleDelete(work) {
  requestConfirm({
    title: 'Eliminar trabajo',
    message: `¿Eliminar "${work.title_es}"?`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: () => portfolioStore.deleteWork(work.id),
  });
}
</script>
