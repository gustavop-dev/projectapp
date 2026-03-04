<template>
  <div>
    <div class="flex items-center gap-4 mb-8">
      <NuxtLink to="/panel/blog" class="text-gray-400 hover:text-gray-600 transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </NuxtLink>
      <h1 class="text-2xl font-light text-gray-900">Editar Blog Post</h1>
    </div>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
    </div>

    <form v-else-if="loaded" class="space-y-6 max-w-3xl" @submit.prevent="handleSubmit">
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
        />
      </div>

      <!-- Slug -->
      <div>
        <label for="slug" class="block text-sm font-medium text-gray-700 mb-1">Slug</label>
        <input
          id="slug"
          v-model="form.slug"
          type="text"
          class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm
                 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
        />
        <p class="text-xs text-gray-400 mt-1">URL: /blog/{{ form.slug || '...' }}</p>
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
          placeholder="https://example.com/image.jpg"
        />
        <!-- Preview -->
        <div v-if="form.cover_image" class="mt-2 rounded-lg overflow-hidden border border-gray-200 max-w-sm">
          <img :src="form.cover_image" alt="Preview" class="w-full h-auto" @error="imgError = true" />
          <p v-if="imgError" class="text-xs text-red-400 p-2">No se pudo cargar la imagen.</p>
        </div>
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
        <span class="text-sm text-gray-700">Publicado</span>
      </div>

      <!-- Error -->
      <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>

      <!-- Success -->
      <p v-if="successMsg" class="text-sm text-emerald-600">{{ successMsg }}</p>

      <!-- Actions -->
      <div class="flex gap-3 pt-4">
        <button
          type="submit"
          :disabled="blogStore.isUpdating"
          class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                 hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
        >
          {{ blogStore.isUpdating ? 'Guardando...' : 'Guardar Cambios' }}
        </button>
        <a
          v-if="post?.slug"
          :href="`/blog/${post.slug}`"
          target="_blank"
          class="px-6 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm
                 hover:bg-gray-50 transition-colors inline-flex items-center gap-1"
        >
          Ver en blog
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch } from 'vue';
import { useBlogStore } from '~/stores/blog';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const blogStore = useBlogStore();
const post = computed(() => blogStore.currentPost);
const loaded = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const imgError = ref(false);

const form = reactive({
  title: '',
  slug: '',
  excerpt: '',
  content: '',
  cover_image: '',
  sources: [],
  is_published: false,
});

onMounted(async () => {
  const result = await blogStore.fetchAdminPost(route.params.id);
  if (result.success && result.data) {
    populateForm(result.data);
  }
  loaded.value = true;
});

function populateForm(data) {
  form.title = data.title || '';
  form.slug = data.slug || '';
  form.excerpt = data.excerpt || '';
  form.content = data.content || '';
  form.cover_image = data.cover_image || '';
  form.sources = Array.isArray(data.sources)
    ? data.sources.map(s => ({ ...s }))
    : [];
  form.is_published = data.is_published || false;
}

watch(() => form.cover_image, () => {
  imgError.value = false;
});

function addSource() {
  form.sources.push({ name: '', url: '' });
}

function removeSource(idx) {
  form.sources.splice(idx, 1);
}

async function handleSubmit() {
  errorMsg.value = '';
  successMsg.value = '';

  const payload = {
    title: form.title,
    slug: form.slug,
    excerpt: form.excerpt,
    content: form.content,
    sources: form.sources.filter(s => s.name && s.url),
    is_published: form.is_published,
  };

  if (form.cover_image) {
    payload.cover_image = form.cover_image;
  }

  const result = await blogStore.updatePost(route.params.id, payload);
  if (result.success) {
    successMsg.value = 'Post actualizado correctamente.';
    setTimeout(() => { successMsg.value = ''; }, 3000);
  } else {
    errorMsg.value = 'Error al actualizar el post. Revisa los campos.';
  }
}
</script>
