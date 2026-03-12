<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-light text-gray-900">Blog Posts</h1>
      <div class="flex items-center gap-3">
        <NuxtLink
          :to="localePath('/panel/blog/calendar')"
          class="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-xl
                 font-medium text-sm hover:bg-gray-50 transition-colors"
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
      <div v-if="posts.length === 0" class="bg-white rounded-xl shadow-sm border border-gray-100 px-6 py-12 text-center text-gray-400 text-sm">
        No hay posts aún. Crea el primero.
      </div>

      <!-- Mobile cards -->
      <div v-else class="sm:hidden space-y-3">
        <div
          v-for="post in posts"
          :key="post.id"
          class="bg-white rounded-xl shadow-sm border border-gray-100 p-4"
        >
          <div class="flex items-start justify-between gap-3 mb-2">
            <NuxtLink
              :to="localePath(`/panel/blog/${post.id}/edit`)"
              class="text-sm font-medium text-gray-900 hover:text-emerald-600 transition-colors leading-tight"
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
          <p class="text-xs text-gray-400 mb-3">{{ post.slug }} · {{ formatDate(post.published_at || post.created_at) }}</p>
          <div class="flex items-center gap-3">
            <NuxtLink
              :to="localePath(`/panel/blog/${post.id}/edit`)"
              class="text-xs text-emerald-600 font-medium"
            >
              Editar
            </NuxtLink>
            <button
              class="text-xs text-gray-500 hover:text-emerald-600 transition-colors"
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
      <div class="hidden sm:block bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 text-left">
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Título</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="post in posts" :key="post.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4">
                  <NuxtLink
                    :to="localePath(`/panel/blog/${post.id}/edit`)"
                    class="text-sm font-medium text-gray-900 hover:text-emerald-600 transition-colors"
                  >
                    {{ post.title_es }}
                  </NuxtLink>
                  <p class="text-xs text-gray-400 mt-0.5">{{ post.title_en }} · {{ post.slug }}</p>
                </td>
                <td class="px-6 py-4">
                  <span
                    class="text-xs px-2.5 py-1 rounded-full font-medium"
                    :class="statusBadgeClass(post)"
                  >
                    {{ statusLabel(post) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                  {{ formatDate(post.published_at || post.created_at) }}
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <NuxtLink
                      :to="localePath(`/panel/blog/${post.id}/edit`)"
                      class="text-xs text-gray-500 hover:text-emerald-600 transition-colors"
                    >
                      Editar
                    </NuxtLink>
                    <button
                      class="text-xs text-gray-500 hover:text-emerald-600 transition-colors"
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
      <div v-if="blogStore.adminPagination.totalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100 bg-white rounded-b-xl">
        <span class="text-xs text-gray-400">{{ blogStore.adminPagination.count }} posts · Página {{ blogStore.adminPagination.page }} de {{ blogStore.adminPagination.totalPages }}</span>
        <div class="flex gap-1">
          <button
            :disabled="blogStore.adminPagination.page <= 1"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border border-gray-200 hover:bg-gray-50 disabled:opacity-40"
            @click="goToPage(blogStore.adminPagination.page - 1)"
          >
            ← Anterior
          </button>
          <button
            v-for="page in visiblePages"
            :key="page"
            class="w-8 h-8 rounded-lg text-xs font-medium transition-colors"
            :class="blogStore.adminPagination.page === page ? 'bg-emerald-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
          <button
            :disabled="blogStore.adminPagination.page >= blogStore.adminPagination.totalPages"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border border-gray-200 hover:bg-gray-50 disabled:opacity-40"
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

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const blogStore = useBlogStore();
const posts = computed(() => blogStore.posts);

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
  if (post.is_published) return 'bg-emerald-50 text-emerald-700';
  if (isScheduled(post)) return 'bg-blue-50 text-blue-700';
  return 'bg-gray-100 text-gray-600';
}

async function handleDuplicate(post) {
  if (!confirm(`¿Duplicar "${post.title_es}"?`)) return;
  await blogStore.duplicatePost(post.id);
}

async function handleDelete(post) {
  if (!confirm(`¿Eliminar "${post.title_es}"?`)) return;
  await blogStore.deletePost(post.id);
  blogStore.fetchAdminPosts(blogStore.adminPagination.page);
}
</script>
