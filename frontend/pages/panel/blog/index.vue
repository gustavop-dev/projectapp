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
      <h1 class="text-2xl font-light text-gray-900 dark:text-white">Blog Posts</h1>
      <div class="flex items-center gap-3">
        <NuxtLink
          :to="localePath('/panel/blog/calendar')"
          class="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-200 dark:border-white/[0.08] text-gray-700 dark:text-green-light rounded-xl
                 font-medium text-sm hover:bg-gray-50 dark:hover:bg-white/[0.06] transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Calendario
        </NuxtLink>
        <NuxtLink
          :to="localePath('/panel/blog/create')"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
                 font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Post
        </NuxtLink>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
    </div>

    <!-- Table (desktop) / Cards (mobile) -->
    <div v-else>
      <div v-if="posts.length === 0" class="bg-white dark:bg-esmerald rounded-xl shadow-sm border border-gray-100 dark:border-white/[0.06] px-6 py-12 text-center text-gray-400 dark:text-green-light/60 text-sm">
        No hay posts aún. Crea el primero.
      </div>

      <!-- Mobile cards -->
      <div v-else class="sm:hidden space-y-3">
        <div
          v-for="post in posts"
          :key="post.id"
          class="bg-white dark:bg-esmerald rounded-xl shadow-sm border border-gray-100 dark:border-white/[0.06] p-4"
        >
          <div class="flex items-start justify-between gap-3 mb-2">
            <NuxtLink
              :to="localePath(`/panel/blog/${post.id}/edit`)"
              class="text-sm font-medium text-gray-900 dark:text-white hover:text-emerald-600 transition-colors leading-tight"
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
          <p class="text-xs text-gray-400 dark:text-green-light/60 mb-3">{{ post.slug }} · {{ formatDate(post.published_at || post.created_at) }}</p>
          <div class="flex items-center gap-3">
            <NuxtLink
              :to="localePath(`/panel/blog/${post.id}/edit`)"
              class="text-xs text-emerald-600 font-medium"
            >
              Editar
            </NuxtLink>
            <button
              class="text-xs text-gray-500 dark:text-green-light/60 hover:text-emerald-600 dark:hover:text-white transition-colors"
              @click="handleDuplicate(post)"
            >
              Duplicar
            </button>
            <button
              class="text-xs text-red-400 hover:text-red-600 transition-colors"
              @click="handleDelete(post)"
            >
              Eliminar
            </button>
          </div>
        </div>
      </div>

      <!-- Desktop table -->
      <div class="hidden sm:block bg-white dark:bg-esmerald rounded-xl shadow-sm border border-gray-100 dark:border-white/[0.06] overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 dark:border-white/[0.06] text-left">
                <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-green-light/60 uppercase tracking-wider">Título</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-green-light/60 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-green-light/60 uppercase tracking-wider">Fecha</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-green-light/60 uppercase tracking-wider text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50 dark:divide-white/[0.04]">
              <tr v-for="post in posts" :key="post.id" class="hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors">
                <td class="px-6 py-4">
                  <NuxtLink
                    :to="localePath(`/panel/blog/${post.id}/edit`)"
                    class="text-sm font-medium text-gray-900 dark:text-white hover:text-emerald-600 transition-colors"
                  >
                    {{ post.title_es }}
                  </NuxtLink>
                  <p class="text-xs text-gray-400 dark:text-green-light/60 mt-0.5">{{ post.title_en }} · {{ post.slug }}</p>
                </td>
                <td class="px-6 py-4">
                  <span
                    class="text-xs px-2.5 py-1 rounded-full font-medium"
                    :class="statusBadgeClass(post)"
                  >
                    {{ statusLabel(post) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500 dark:text-green-light/60">
                  {{ formatDate(post.published_at || post.created_at) }}
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <NuxtLink
                      :to="localePath(`/panel/blog/${post.id}/edit`)"
                      class="text-xs text-gray-500 dark:text-green-light/60 hover:text-emerald-600 dark:hover:text-white transition-colors"
                    >
                      Editar
                    </NuxtLink>
                    <button
                      class="text-xs text-gray-500 dark:text-green-light/60 hover:text-emerald-600 dark:hover:text-white transition-colors"
                      @click="handleDuplicate(post)"
                    >
                      Duplicar
                    </button>
                    <button
                      class="text-xs text-red-400 hover:text-red-600 transition-colors"
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
      <div v-if="blogStore.adminPagination.totalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100 dark:border-white/[0.06] bg-white dark:bg-esmerald rounded-b-xl">
        <span class="text-xs text-gray-400 dark:text-green-light/60">{{ blogStore.adminPagination.count }} posts · Página {{ blogStore.adminPagination.page }} de {{ blogStore.adminPagination.totalPages }}</span>
        <div class="flex gap-1">
          <button
            :disabled="blogStore.adminPagination.page <= 1"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border border-gray-200 dark:border-white/[0.08] dark:text-green-light/60 hover:bg-gray-50 dark:hover:bg-white/[0.06] disabled:opacity-40"
            @click="goToPage(blogStore.adminPagination.page - 1)"
          >
            ← Anterior
          </button>
          <button
            v-for="page in visiblePages"
            :key="page"
            class="w-8 h-8 rounded-lg text-xs font-medium transition-colors"
            :class="blogStore.adminPagination.page === page ? 'bg-emerald-600 text-white' : 'text-gray-500 dark:text-green-light/60 hover:bg-gray-100 dark:hover:bg-white/[0.06]'"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
          <button
            :disabled="blogStore.adminPagination.page >= blogStore.adminPagination.totalPages"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border border-gray-200 dark:border-white/[0.08] dark:text-green-light/60 hover:bg-gray-50 dark:hover:bg-white/[0.06] disabled:opacity-40"
            @click="goToPage(blogStore.adminPagination.page + 1)"
          >
            Siguiente →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useBlogStore } from '~/stores/blog';
import { useConfirmModal } from '~/composables/useConfirmModal';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const blogStore = useBlogStore();
const posts = computed(() => blogStore.posts);
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

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

onMounted(() => {
  blogStore.fetchAdminPosts();
});

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
  if (post.is_published) return 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400';
  if (isScheduled(post)) return 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300';
  return 'bg-gray-100 dark:bg-white/[0.06] text-gray-600 dark:text-green-light';
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
