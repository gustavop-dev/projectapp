<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-light text-gray-900">Blog Posts</h1>
      <NuxtLink
        to="/panel/blog/create"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
               font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Post
      </NuxtLink>
    </div>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
    </div>

    <!-- Table -->
    <div v-else class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div v-if="posts.length === 0" class="px-6 py-12 text-center text-gray-400 text-sm">
        No hay posts aún. Crea el primero.
      </div>
      <table v-else class="w-full">
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
                :to="`/panel/blog/${post.id}/edit`"
                class="text-sm font-medium text-gray-900 hover:text-emerald-600 transition-colors"
              >
                {{ post.title_es }}
              </NuxtLink>
              <p class="text-xs text-gray-400 mt-0.5">{{ post.title_en }} · {{ post.slug }}</p>
            </td>
            <td class="px-6 py-4">
              <span
                class="text-xs px-2.5 py-1 rounded-full font-medium"
                :class="post.is_published
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-gray-100 text-gray-600'"
              >
                {{ post.is_published ? 'Publicado' : 'Borrador' }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
              {{ formatDate(post.published_at || post.created_at) }}
            </td>
            <td class="px-6 py-4 text-right">
              <div class="flex items-center justify-end gap-2">
                <NuxtLink
                  :to="`/panel/blog/${post.id}/edit`"
                  class="text-xs text-gray-500 hover:text-emerald-600 transition-colors"
                >
                  Editar
                </NuxtLink>
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
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useBlogStore } from '~/stores/blog';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const blogStore = useBlogStore();
const posts = computed(() => blogStore.posts);

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

async function handleDelete(post) {
  if (!confirm(`¿Eliminar "${post.title_es}"?`)) return;
  await blogStore.deletePost(post.id);
}
</script>
