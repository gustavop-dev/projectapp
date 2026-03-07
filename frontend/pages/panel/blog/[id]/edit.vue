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
      <!-- Slug -->
      <div>
        <label for="slug" class="block text-sm font-medium text-gray-700 mb-1">Slug</label>
        <input id="slug" v-model="form.slug" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
        <p class="text-xs text-gray-400 mt-1">URL: /blog/{{ form.slug || '...' }}</p>
      </div>

      <!-- Metadata row -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
          <select v-model="form.category" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white">
            <option value="">Sin categoría</option>
            <option value="technology">Technology</option>
            <option value="design">Design</option>
            <option value="guides">Guides</option>
            <option value="business">Business</option>
            <option value="case-study">Case Study</option>
            <option value="ai">AI</option>
            <option value="development">Development</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Tiempo lectura (min)</label>
          <input v-model.number="form.read_time_minutes" type="number" min="0" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
        </div>
        <div class="flex items-end">
          <label class="relative inline-flex items-center cursor-pointer gap-3">
            <input v-model="form.is_featured" type="checkbox" class="sr-only peer" />
            <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600" />
            <span class="text-sm text-gray-700">Destacado</span>
          </label>
        </div>
      </div>

      <!-- Español Section -->
      <fieldset class="border border-gray-200 rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-gray-700 px-2">Español</legend>
        <div>
          <label for="title_es" class="block text-sm font-medium text-gray-700 mb-1">Título (ES)</label>
          <input id="title_es" v-model="form.title_es" type="text" required class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
        </div>
        <div>
          <label for="excerpt_es" class="block text-sm font-medium text-gray-700 mb-1">Resumen (ES)</label>
          <textarea id="excerpt_es" v-model="form.excerpt_es" rows="2" required class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
        </div>
        <div>
          <label for="content_es" class="block text-sm font-medium text-gray-700 mb-1">Contenido HTML (ES)</label>
          <textarea id="content_es" v-model="form.content_es" rows="6" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-mono focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contenido JSON (ES)</label>
          <textarea v-model="form.content_json_es_raw" rows="10" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-mono focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" placeholder='{ "intro": "...", "sections": [...], "conclusion": "...", "cta": "..." }' />
          <p class="text-xs text-gray-400 mt-1">JSON estructurado con intro, sections, conclusion y cta. Tiene prioridad sobre el HTML.</p>
        </div>
      </fieldset>

      <!-- English Section -->
      <fieldset class="border border-gray-200 rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-gray-700 px-2">English</legend>
        <div>
          <label for="title_en" class="block text-sm font-medium text-gray-700 mb-1">Title (EN)</label>
          <input id="title_en" v-model="form.title_en" type="text" required class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
        </div>
        <div>
          <label for="excerpt_en" class="block text-sm font-medium text-gray-700 mb-1">Excerpt (EN)</label>
          <textarea id="excerpt_en" v-model="form.excerpt_en" rows="2" required class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
        </div>
        <div>
          <label for="content_en" class="block text-sm font-medium text-gray-700 mb-1">Content HTML (EN)</label>
          <textarea id="content_en" v-model="form.content_en" rows="6" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-mono focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Content JSON (EN)</label>
          <textarea v-model="form.content_json_en_raw" rows="10" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-mono focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" placeholder='{ "intro": "...", "sections": [...], "conclusion": "...", "cta": "..." }' />
        </div>
      </fieldset>

      <!-- SEO Section (collapsible) -->
      <details class="border border-gray-200 rounded-xl">
        <summary class="text-sm font-medium text-gray-700 px-5 py-3 cursor-pointer select-none">SEO (opcional)</summary>
        <div class="px-5 pb-5 space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Meta título (ES)</label>
              <input v-model="form.meta_title_es" type="text" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Meta title (EN)</label>
              <input v-model="form.meta_title_en" type="text" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
            </div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Meta descripción (ES)</label>
              <textarea v-model="form.meta_description_es" rows="2" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Meta description (EN)</label>
              <textarea v-model="form.meta_description_en" rows="2" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
            </div>
          </div>
        </div>
      </details>

      <!-- Cover image URL -->
      <div>
        <label for="cover_image" class="block text-sm font-medium text-gray-700 mb-1">Imagen de portada (URL)</label>
        <input id="cover_image" v-model="form.cover_image" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="https://example.com/image.jpg" />
        <div v-if="form.cover_image" class="mt-2 rounded-lg overflow-hidden border border-gray-200 max-w-sm">
          <img :src="form.cover_image" alt="Preview" class="w-full h-auto" @error="imgError = true" />
          <p v-if="imgError" class="text-xs text-red-400 p-2">No se pudo cargar la imagen.</p>
        </div>
      </div>

      <!-- Sources -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="block text-sm font-medium text-gray-700">Fuentes</label>
          <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 transition-colors" @click="addSource">+ Agregar fuente</button>
        </div>
        <div v-for="(source, idx) in form.sources" :key="idx" class="flex gap-2 mb-2">
          <input v-model="source.name" type="text" class="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="Nombre de la fuente" />
          <input v-model="source.url" type="url" class="flex-[2] px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="https://..." />
          <button type="button" class="text-gray-400 hover:text-red-500 transition-colors px-2" @click="removeSource(idx)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <p v-if="form.sources.length === 0" class="text-xs text-gray-400">No hay fuentes agregadas.</p>
      </div>

      <!-- Publish toggle -->
      <div class="flex items-center gap-3">
        <label class="relative inline-flex items-center cursor-pointer">
          <input v-model="form.is_published" type="checkbox" class="sr-only peer" />
          <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600" />
        </label>
        <span class="text-sm text-gray-700">Publicado</span>
      </div>

      <!-- Error / Success -->
      <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>
      <p v-if="successMsg" class="text-sm text-emerald-600">{{ successMsg }}</p>

      <!-- Actions -->
      <div class="flex gap-3 pt-4">
        <button type="submit" :disabled="blogStore.isUpdating" class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50">
          {{ blogStore.isUpdating ? 'Guardando...' : 'Guardar Cambios' }}
        </button>
        <a v-if="post?.slug" :href="`/blog/${post.slug}`" target="_blank" class="px-6 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition-colors inline-flex items-center gap-1">
          Ver en blog
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
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
  title_es: '',
  title_en: '',
  slug: '',
  excerpt_es: '',
  excerpt_en: '',
  content_es: '',
  content_en: '',
  content_json_es_raw: '',
  content_json_en_raw: '',
  cover_image: '',
  sources: [],
  category: '',
  read_time_minutes: 0,
  is_featured: false,
  is_published: false,
  meta_title_es: '',
  meta_title_en: '',
  meta_description_es: '',
  meta_description_en: '',
});

onMounted(async () => {
  const result = await blogStore.fetchAdminPost(route.params.id);
  if (result.success && result.data) {
    populateForm(result.data);
  }
  loaded.value = true;
});

function jsonToStr(val) {
  if (!val || (typeof val === 'object' && Object.keys(val).length === 0)) return '';
  return JSON.stringify(val, null, 2);
}

function strToJson(str) {
  if (!str || !str.trim()) return {};
  try { return JSON.parse(str); }
  catch { return {}; }
}

function populateForm(data) {
  form.title_es = data.title_es || '';
  form.title_en = data.title_en || '';
  form.slug = data.slug || '';
  form.excerpt_es = data.excerpt_es || '';
  form.excerpt_en = data.excerpt_en || '';
  form.content_es = data.content_es || '';
  form.content_en = data.content_en || '';
  form.content_json_es_raw = jsonToStr(data.content_json_es);
  form.content_json_en_raw = jsonToStr(data.content_json_en);
  form.cover_image = data.cover_image || '';
  form.sources = Array.isArray(data.sources)
    ? data.sources.map(s => ({ ...s }))
    : [];
  form.category = data.category || '';
  form.read_time_minutes = data.read_time_minutes || 0;
  form.is_featured = data.is_featured || false;
  form.is_published = data.is_published || false;
  form.meta_title_es = data.meta_title_es || '';
  form.meta_title_en = data.meta_title_en || '';
  form.meta_description_es = data.meta_description_es || '';
  form.meta_description_en = data.meta_description_en || '';
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
    title_es: form.title_es,
    title_en: form.title_en,
    slug: form.slug,
    excerpt_es: form.excerpt_es,
    excerpt_en: form.excerpt_en,
    content_es: form.content_es,
    content_en: form.content_en,
    content_json_es: strToJson(form.content_json_es_raw),
    content_json_en: strToJson(form.content_json_en_raw),
    sources: form.sources.filter(s => s.name && s.url),
    category: form.category,
    read_time_minutes: form.read_time_minutes,
    is_featured: form.is_featured,
    is_published: form.is_published,
    meta_title_es: form.meta_title_es,
    meta_title_en: form.meta_title_en,
    meta_description_es: form.meta_description_es,
    meta_description_en: form.meta_description_en,
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
