<template>
  <div>
    <div class="flex items-center gap-4 mb-8">
      <NuxtLink to="/panel/blog" class="text-gray-400 hover:text-gray-600 transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </NuxtLink>
      <h1 class="text-2xl font-light text-gray-900">Nuevo Blog Post</h1>
    </div>

    <form class="space-y-6 max-w-3xl" @submit.prevent="handleSubmit">
      <!-- Title -->
      <div>
        <label for="title" class="block text-sm font-medium text-gray-700 mb-1">Título</label>
        <input
          id="title"
          v-model="form.title"
          type="text"
          required
          class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm
                 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
          placeholder="Título del artículo"
        />
      </div>

      <!-- Excerpt -->
      <div>
        <label for="excerpt" class="block text-sm font-medium text-gray-700 mb-1">Resumen</label>
        <textarea
          id="excerpt"
          v-model="form.excerpt"
          rows="2"
          required
          class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm
                 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y"
          placeholder="Resumen corto para las tarjetas del listado (1-2 oraciones)"
        />
      </div>

      <!-- Content -->
      <div>
        <label for="content" class="block text-sm font-medium text-gray-700 mb-1">Contenido (HTML)</label>
        <textarea
          id="content"
          v-model="form.content"
          rows="14"
          required
          class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-mono
                 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y"
          placeholder="<h2>Subtítulo</h2><p>Contenido del artículo...</p>"
        />
      </div>

      <!-- Cover image URL -->
      <div>
        <label for="cover_image" class="block text-sm font-medium text-gray-700 mb-1">
          Imagen de portada (URL)
        </label>
        <input
          id="cover_image"
          v-model="form.cover_image"
          type="text"
          class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm
                 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
          placeholder="https://example.com/image.jpg (opcional)"
        />
        <p class="text-xs text-gray-400 mt-1">Dejar vacío si no hay imagen disponible aún.</p>
      </div>

      <!-- Sources -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="block text-sm font-medium text-gray-700">Fuentes</label>
          <button
            type="button"
            class="text-xs text-emerald-600 hover:text-emerald-700 transition-colors"
            @click="addSource"
          >
            + Agregar fuente
          </button>
        </div>
        <div v-for="(source, idx) in form.sources" :key="idx" class="flex gap-2 mb-2">
          <input
            v-model="source.name"
            type="text"
            class="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm
                   focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
            placeholder="Nombre de la fuente"
          />
          <input
            v-model="source.url"
            type="url"
            class="flex-[2] px-3 py-2 rounded-lg border border-gray-200 text-sm
                   focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
            placeholder="https://..."
          />
          <button
            type="button"
            class="text-gray-400 hover:text-red-500 transition-colors px-2"
            @click="removeSource(idx)"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <p v-if="form.sources.length === 0" class="text-xs text-gray-400">
          No hay fuentes agregadas.
        </p>
      </div>

      <!-- Publish toggle -->
      <div class="flex items-center gap-3">
        <label class="relative inline-flex items-center cursor-pointer">
          <input v-model="form.is_published" type="checkbox" class="sr-only peer" />
          <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer
                      peer-checked:after:translate-x-full peer-checked:after:border-white
                      after:content-[''] after:absolute after:top-[2px] after:start-[2px]
                      after:bg-white after:border-gray-300 after:border after:rounded-full
                      after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600" />
        </label>
        <span class="text-sm text-gray-700">Publicar inmediatamente</span>
      </div>

      <!-- Error -->
      <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>

      <!-- Actions -->
      <div class="flex gap-3 pt-4">
        <button
          type="submit"
          :disabled="blogStore.isUpdating"
          class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                 hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
        >
          {{ blogStore.isUpdating ? 'Creando...' : 'Crear Post' }}
        </button>
        <NuxtLink
          to="/panel/blog"
          class="px-6 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm
                 hover:bg-gray-50 transition-colors"
        >
          Cancelar
        </NuxtLink>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useBlogStore } from '~/stores/blog';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const blogStore = useBlogStore();
const errorMsg = ref('');

const form = reactive({
  title: '',
  excerpt: '',
  content: '',
  cover_image: '',
  sources: [],
  is_published: false,
});

function addSource() {
  form.sources.push({ name: '', url: '' });
}

function removeSource(idx) {
  form.sources.splice(idx, 1);
}

async function handleSubmit() {
  errorMsg.value = '';

  const payload = {
    title: form.title,
    excerpt: form.excerpt,
    content: form.content,
    sources: form.sources.filter(s => s.name && s.url),
    is_published: form.is_published,
  };

  if (form.cover_image) {
    payload.cover_image = form.cover_image;
  }

  const result = await blogStore.createPost(payload);
  if (result.success) {
    navigateTo('/panel/blog');
  } else {
    errorMsg.value = 'Error al crear el post. Revisa los campos.';
  }
}
</script>
