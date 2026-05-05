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
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <h1 class="text-2xl font-light text-text-default">Blog Posts</h1>
      <div class="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
        <BaseButton
          as="NuxtLink"
          variant="secondary"
          size="md"
          :to="localePath('/panel/blog/calendar')"
          class="flex-1 sm:flex-initial justify-center"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Calendario
        </BaseButton>
        <BaseButton
          as="NuxtLink"
          variant="primary"
          size="md"
          :to="localePath('/panel/blog/create')"
          class="flex-1 sm:flex-initial justify-center"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Post
        </BaseButton>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-focus-ring/30 border-t-focus-ring rounded-full animate-spin" />
    </div>

    <!-- Table (desktop) / Cards (mobile) -->
    <div v-else>
      <div v-if="posts.length === 0" class="bg-surface rounded-xl shadow-sm border border-border-muted px-6 py-12 text-center text-text-subtle text-sm">
        No hay posts aún. Crea el primero.
      </div>

      <!-- Mobile cards -->
      <div v-else class="sm:hidden space-y-3">
        <div
          v-for="post in posts"
          :key="post.id"
          class="bg-surface rounded-xl shadow-sm border border-border-muted p-4"
        >
          <div class="flex items-start justify-between gap-3 mb-2">
            <NuxtLink
              :to="localePath(`/panel/blog/${post.id}/edit`)"
              class="text-sm font-medium text-text-default hover:text-text-brand transition-colors leading-tight"
            >
              {{ post.title_es }}
            </NuxtLink>
            <span
              class="text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0"
              :class="statusBadgeClass(post)"
            >
              {{ statusLabel(post) }}
            </span>
          </div>
          <p class="text-xs text-text-subtle mb-3">{{ post.slug }} · {{ formatDate(post.published_at || post.created_at) }}</p>
          <div class="flex items-center gap-3">
            <NuxtLink
              :to="localePath(`/panel/blog/${post.id}/edit`)"
              class="text-xs text-text-brand font-medium"
            >
              Editar
            </NuxtLink>
            <button
              class="text-xs text-text-muted hover:text-text-brand transition-colors"
              @click="handleDuplicate(post)"
            >
              Duplicar
            </button>
            <button
              class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors"
              @click="handleDelete(post)"
            >
              Eliminar
            </button>
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
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Fecha</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border-muted">
              <tr v-for="post in posts" :key="post.id" class="hover:bg-surface-raised transition-colors">
                <td class="px-6 py-4">
                  <NuxtLink
                    :to="localePath(`/panel/blog/${post.id}/edit`)"
                    class="text-sm font-medium text-text-default hover:text-text-brand transition-colors"
                  >
                    {{ post.title_es }}
                  </NuxtLink>
                  <p class="text-xs text-text-subtle mt-0.5">{{ post.title_en }} · {{ post.slug }}</p>
                </td>
                <td class="px-6 py-4">
                  <span
                    class="text-xs px-2.5 py-1 rounded-full font-medium"
                    :class="statusBadgeClass(post)"
                  >
                    {{ statusLabel(post) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-text-muted">
                  {{ formatDate(post.published_at || post.created_at) }}
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <NuxtLink
                      :to="localePath(`/panel/blog/${post.id}/edit`)"
                      class="text-xs text-text-muted hover:text-text-brand transition-colors"
                    >
                      Editar
                    </NuxtLink>
                    <button
                      class="text-xs text-text-muted hover:text-text-brand transition-colors"
                      @click="handleDuplicate(post)"
                    >
                      Duplicar
                    </button>
                    <button
                      class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors"
                      @click="handleDelete(post)"
                    >
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination controls -->
      <BasePagination
        v-if="blogStore.adminPagination.totalPages > 1"
        :current-page="blogStore.adminPagination.page"
        :total-pages="blogStore.adminPagination.totalPages"
        :total-items="blogStore.adminPagination.count"
        :range-from="blogRangeFrom"
        :range-to="blogRangeTo"
        class="px-4 sm:px-6"
        @prev="goToPage(blogStore.adminPagination.page - 1)"
        @next="goToPage(blogStore.adminPagination.page + 1)"
        @go="goToPage"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useBlogStore } from '~/stores/blog';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import BasePagination from '~/components/base/BasePagination.vue';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const blogStore = useBlogStore();
const posts = computed(() => blogStore.posts);
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const blogRangeFrom = computed(() => {
  const p = blogStore.adminPagination;
  if (!p.count) return 0;
  return (p.page - 1) * (p.pageSize || 20) + 1;
});
const blogRangeTo = computed(() => {
  const p = blogStore.adminPagination;
  return Math.min(p.page * (p.pageSize || 20), p.count || 0);
});

const visiblePages = computed(() => {
  const total = blogStore.adminPagination.totalPages;
  const current = blogStore.adminPagination.page;
  const pages = [];
  const start = Math.max(1, current - 2);
  const end = Math.min(total, current + 2);
  for (let i = start; i <= end; i++) pages.push(i);
  return pages;
});

function goToPage(page) {
  if (page < 1 || page > blogStore.adminPagination.totalPages) return;
  blogStore.fetchAdminPosts(page);
}

function refreshAdminPosts() {
  return blogStore.fetchAdminPosts(blogStore.adminPagination.page || 1);
}

onMounted(() => {
  blogStore.fetchAdminPosts();
});

usePanelRefresh(refreshAdminPosts);

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function isScheduled(post) {
  return !post.is_published && post.published_at && new Date(post.published_at) > new Date();
}

function statusLabel(post) {
  if (post.is_published) return 'Publicado';
  if (isScheduled(post)) return `Programado: ${formatDate(post.published_at)}`;
  return 'Borrador';
}

function statusBadgeClass(post) {
  if (post.is_published) return 'bg-primary-soft text-text-brand';
  if (isScheduled(post)) return 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300';
  return 'bg-surface-raised text-text-muted';
}

function handleDuplicate(post) {
  requestConfirm({
    title: 'Duplicar post',
    message: `¿Duplicar "${post.title_es}"?`,
    variant: 'info',
    confirmText: 'Duplicar',
    onConfirm: () => blogStore.duplicatePost(post.id),
  });
}

function handleDelete(post) {
  requestConfirm({
    title: 'Eliminar post',
    message: `¿Eliminar "${post.title_es}"?`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      await blogStore.deletePost(post.id);
      blogStore.fetchAdminPosts(blogStore.adminPagination.page);
    },
  });
}
</script>
