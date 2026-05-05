<template>
  <div>
    <div class="flex items-center gap-4 mb-8">
      <NuxtLink :to="localePath('/panel/blog')" class="text-text-subtle hover:text-text-default transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </NuxtLink>
      <h1 class="text-2xl font-light text-text-default">Nuevo Blog Post</h1>
    </div>

    <!-- Tab toggle -->
    <div class="flex gap-1 mb-6 bg-surface-raised rounded-xl p-1 max-w-xs">
      <button
        type="button"
        :class="['flex-1 px-4 py-2 text-sm rounded-lg transition-all', mode === 'manual' ? 'bg-surface shadow-sm font-medium text-text-default' : 'text-text-muted hover:text-text-default']"
        @click="mode = 'manual'"
      >
        Manual
      </button>
      <button
        type="button"
        :class="['flex-1 px-4 py-2 text-sm rounded-lg transition-all', mode === 'json' ? 'bg-surface shadow-sm font-medium text-text-default' : 'text-text-muted hover:text-text-default']"
        @click="mode = 'json'"
      >
        Importar JSON
      </button>
    </div>

    <!-- ============================================================ -->
    <!-- MANUAL MODE -->
    <!-- ============================================================ -->
    <form v-if="mode === 'manual'" class="space-y-6 max-w-3xl" @submit.prevent="handleSubmit">
      <!-- Español Section -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-text-default px-2">Español</legend>
        <div>
          <label for="title_es" class="block text-sm font-medium text-text-default mb-1">Título (ES)</label>
          <input id="title_es" v-model="form.title_es" type="text" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all" placeholder="Título del artículo en español" />
        </div>
        <div>
          <label for="excerpt_es" class="block text-sm font-medium text-text-default mb-1">Resumen (ES)</label>
          <textarea id="excerpt_es" v-model="form.excerpt_es" rows="2" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all resize-y" placeholder="Resumen corto en español (1-2 oraciones)" />
        </div>
        <div>
          <label for="content_es" class="block text-sm font-medium text-text-default mb-1">Contenido HTML (ES)</label>
          <textarea id="content_es" v-model="form.content_es" rows="10" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default text-sm font-mono focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all resize-y" placeholder="<h2>Subtítulo</h2><p>Contenido en español...</p>" />
        </div>
      </fieldset>

      <!-- English Section -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-text-default px-2">English</legend>
        <div>
          <label for="title_en" class="block text-sm font-medium text-text-default mb-1">Title (EN)</label>
          <input id="title_en" v-model="form.title_en" type="text" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all" placeholder="Article title in English" />
        </div>
        <div>
          <label for="excerpt_en" class="block text-sm font-medium text-text-default mb-1">Excerpt (EN)</label>
          <textarea id="excerpt_en" v-model="form.excerpt_en" rows="2" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all resize-y" placeholder="Short summary in English (1-2 sentences)" />
        </div>
        <div>
          <label for="content_en" class="block text-sm font-medium text-text-default mb-1">Content HTML (EN)</label>
          <textarea id="content_en" v-model="form.content_en" rows="10" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default text-sm font-mono focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all resize-y" placeholder="<h2>Subtitle</h2><p>Content in English...</p>" />
        </div>
      </fieldset>

      <!-- Metadata fields -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label for="category" class="block text-sm font-medium text-text-default mb-1">Categoría</label>
          <select id="category" v-model="form.category" class="w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all bg-surface">
            <option value="">Sin categoría</option>
            <option v-for="cat in blogStore.availableCategories" :key="cat.slug" :value="cat.slug">{{ cat.label }}</option>
          </select>
        </div>
        <div>
          <label for="read_time_minutes" class="block text-sm font-medium text-text-default mb-1">Tiempo lectura (min)</label>
          <input id="read_time_minutes" v-model.number="form.read_time_minutes" type="number" min="0" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all" />
        </div>
        <div class="flex items-end">
          <label class="relative inline-flex items-center cursor-pointer gap-3">
            <input v-model="form.is_featured" type="checkbox" class="sr-only peer" />
            <div class="w-9 h-5 bg-surface-raised peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-surface after:border-border-default after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary" />
            <span class="text-sm text-text-default">Destacado</span>
          </label>
        </div>
      </div>

      <!-- Cover image URL -->
      <div>
        <label for="cover_image_url" class="block text-sm font-medium text-text-default mb-1">Imagen de portada (URL)</label>
        <input id="cover_image_url" v-model="form.cover_image_url" type="url" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all" placeholder="https://example.com/image.jpg (opcional)" />
        <p class="text-xs text-text-subtle mt-1">También puedes subir un archivo después de crear el post desde la vista de edición.</p>
      </div>

      <!-- Sources -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="block text-sm font-medium text-text-default">Fuentes</label>
          <button type="button" class="text-xs text-text-brand hover:text-text-brand transition-colors" @click="addSource">+ Agregar fuente</button>
        </div>
        <div v-for="(source, idx) in form.sources" :key="idx" class="flex gap-2 mb-2">
          <input v-model="source.name" type="text" class="bg-input-bg flex-1 px-3 py-2 rounded-lg border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all" placeholder="Nombre de la fuente" />
          <input v-model="source.url" type="url" class="bg-input-bg flex-[2] px-3 py-2 rounded-lg border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all" placeholder="https://..." />
          <button type="button" class="text-text-subtle hover:text-red-500 transition-colors px-2" @click="removeSource(idx)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <p v-if="form.sources.length === 0" class="text-xs text-text-subtle">No hay fuentes agregadas.</p>
      </div>

      <!-- Publishing options -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-text-default px-2">Publicación</legend>
        <div class="flex flex-col gap-3">
          <label class="flex items-center gap-3 cursor-pointer">
            <input v-model="publishMode" type="radio" value="draft" name="createPublishMode" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
            <span class="text-sm text-text-default">Borrador</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input v-model="publishMode" type="radio" value="now" name="createPublishMode" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
            <span class="text-sm text-text-default">Publicar ahora</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input v-model="publishMode" type="radio" value="schedule" name="createPublishMode" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
            <span class="text-sm text-text-default">Programar publicación</span>
          </label>
          <div v-if="publishMode === 'schedule'" class="ml-7">
            <input v-model="scheduledDate" type="datetime-local" class="bg-input-bg px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all" />
            <p class="text-xs text-text-subtle mt-1">El post se publicará automáticamente en la fecha seleccionada.</p>
          </div>
        </div>
      </fieldset>

      <!-- Error -->
      <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>

      <!-- Actions -->
      <div class="flex gap-3 pt-4">
        <button type="submit" :disabled="blogStore.isUpdating" class="px-6 py-2.5 bg-primary text-white rounded-xl font-medium text-sm hover:bg-primary transition-colors shadow-sm disabled:opacity-50">
          {{ blogStore.isUpdating ? 'Creando...' : 'Crear Post' }}
        </button>
        <NuxtLink :to="localePath('/panel/blog')" class="px-6 py-2.5 border border-border-default dark:border-white/[0.08] text-text-muted rounded-xl text-sm hover:bg-surface-raised transition-colors">Cancelar</NuxtLink>
      </div>
    </form>

    <!-- ============================================================ -->
    <!-- JSON IMPORT MODE -->
    <!-- ============================================================ -->
    <div v-else class="max-w-3xl space-y-6">

      <!-- Download template -->
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 class="text-sm font-medium text-text-default">Plantilla JSON</h3>
            <p class="text-xs text-text-subtle mt-0.5">Descarga la plantilla con todas las secciones y campos de ejemplo.</p>
          </div>
          <button type="button" :disabled="isDownloading" class="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-50" @click="downloadTemplate">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            {{ isDownloading ? 'Descargando...' : 'Descargar Plantilla' }}
          </button>
        </div>
      </div>

      <!-- JSON input -->
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
        <h3 class="text-sm font-medium text-text-default mb-3">Pegar o subir JSON</h3>
        <div class="flex items-center gap-3 mb-3">
          <label class="inline-flex items-center gap-2 px-4 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm text-text-default hover:bg-surface-raised cursor-pointer transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
            Subir archivo .json
            <input type="file" accept=".json" class="hidden" @change="handleFileUpload" />
          </label>
          <span v-if="uploadedFileName" class="text-xs text-text-muted">{{ uploadedFileName }}</span>
        </div>
        <textarea
          v-model="jsonRaw"
          rows="14"
          placeholder='{ "title_es": "...", "title_en": "...", "content_json_es": { "intro": "...", "sections": [...] }, ... }'
          class="bg-input-bg w-full px-4 py-3 border border-border-default dark:border-white/[0.08]  rounded-xl text-xs font-mono leading-relaxed focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none resize-y"
          @input="parseJson"
        />

        <div v-if="jsonError" class="mt-2 text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-500/10 px-4 py-2 rounded-lg">{{ jsonError }}</div>

        <div v-if="jsonParsed && !jsonError" class="mt-3 bg-primary-soft border border-emerald-200 dark:border-emerald-500/20 rounded-lg px-4 py-3">
          <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span><span class="text-text-muted">Título:</span> <span class="font-medium text-text-default">{{ jsonParsed.title_es }}</span></span>
            <span><span class="text-text-muted">Categoría:</span> <span class="font-medium text-text-default">{{ jsonParsed.category || '—' }}</span></span>
            <span><span class="text-text-muted">Secciones ES:</span> <span class="font-medium text-text-default">{{ jsonParsed.content_json_es?.sections?.length || 0 }}</span></span>
          </div>
        </div>
      </div>

      <!-- Metadata + submit -->
      <form v-if="jsonParsed && !jsonError" class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6" @submit.prevent="handleJsonSubmit">
        <h3 class="text-sm font-medium text-text-default mb-4">Opciones de publicación</h3>
        <div class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Categoría</label>
              <select v-model="jsonMeta.category" class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface text-text-default">
                <option value="">Sin categoría</option>
                <option v-for="cat in blogStore.availableCategories" :key="cat.slug" :value="cat.slug">{{ cat.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Tiempo lectura (min)</label>
              <input v-model.number="jsonMeta.read_time_minutes" type="number" min="0" class="bg-input-bg w-full px-4 py-2.5 border border-border-default rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none" />
            </div>
            <div class="flex items-end">
              <label class="relative inline-flex items-center cursor-pointer gap-3">
                <input v-model="jsonMeta.is_featured" type="checkbox" class="sr-only peer" />
                <div class="w-9 h-5 bg-surface-raised rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-surface after:border-border-default after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary" />
                <span class="text-xs text-text-default">Destacado</span>
              </label>
            </div>
          </div>

          <!-- Publishing options -->
          <fieldset class="border border-border-default rounded-xl p-4 space-y-3">
            <legend class="text-xs font-medium text-text-muted px-2">Publicación</legend>
            <div class="flex flex-col gap-2">
              <label class="flex items-center gap-3 cursor-pointer">
                <input v-model="jsonPublishMode" type="radio" value="draft" name="jsonPublishMode" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
                <span class="text-sm text-text-default">Borrador</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer">
                <input v-model="jsonPublishMode" type="radio" value="now" name="jsonPublishMode" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
                <span class="text-sm text-text-default">Publicar ahora</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer">
                <input v-model="jsonPublishMode" type="radio" value="schedule" name="jsonPublishMode" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
                <span class="text-sm text-text-default">Programar publicación</span>
              </label>
              <div v-if="jsonPublishMode === 'schedule'" class="ml-7">
                <input v-model="jsonScheduledDate" type="datetime-local" class="bg-input-bg px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-emerald-500 transition-all" />
              </div>
            </div>
          </fieldset>

          <div v-if="errorMsg" class="text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-500/10 px-4 py-3 rounded-xl">{{ errorMsg }}</div>

          <div class="flex flex-wrap items-center gap-4 pt-2">
            <button type="submit" :disabled="blogStore.isUpdating" class="px-5 sm:px-6 py-2.5 bg-primary text-white rounded-xl font-medium text-sm hover:bg-primary transition-colors shadow-sm disabled:opacity-50">
              {{ blogStore.isUpdating ? 'Creando...' : 'Crear desde JSON' }}
            </button>
            <NuxtLink :to="localePath('/panel/blog')" class="text-sm text-text-muted hover:text-text-default">Cancelar</NuxtLink>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { useBlogStore } from '~/stores/blog';
import { usePanelRefresh } from '~/composables/usePanelRefresh';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const blogStore = useBlogStore();
const errorMsg = ref('');
const mode = ref('manual');
const publishMode = ref('draft');
const scheduledDate = ref('');

onMounted(() => {
  blogStore.fetchCategories();
});

usePanelRefresh(() => blogStore.fetchCategories());

// -------------------------------------------------------------------------
// MANUAL mode
// -------------------------------------------------------------------------
const form = reactive({
  title_es: '',
  title_en: '',
  excerpt_es: '',
  excerpt_en: '',
  content_es: '',
  content_en: '',
  cover_image_url: '',
  cover_image_credit: '',
  cover_image_credit_url: '',
  sources: [],
  category: '',
  read_time_minutes: 0,
  is_featured: false,
});

function addSource() { form.sources.push({ name: '', url: '' }); }
function removeSource(idx) { form.sources.splice(idx, 1); }

async function handleSubmit() {
  errorMsg.value = '';
  const payload = {
    title_es: form.title_es,
    title_en: form.title_en,
    excerpt_es: form.excerpt_es,
    excerpt_en: form.excerpt_en,
    content_es: form.content_es,
    content_en: form.content_en,
    sources: form.sources.filter(s => s.name && s.url),
    category: form.category,
    read_time_minutes: form.read_time_minutes,
    is_featured: form.is_featured,
  };

  if (publishMode.value === 'now') {
    payload.is_published = true;
  } else if (publishMode.value === 'schedule') {
    payload.is_published = false;
    payload.published_at = scheduledDate.value ? new Date(scheduledDate.value).toISOString() : null;
  } else {
    payload.is_published = false;
  }

  if (form.cover_image_url) payload.cover_image_url = form.cover_image_url;

  const result = await blogStore.createPost(payload);
  if (result.success) {
    navigateTo(localePath('/panel/blog'));
  } else {
    errorMsg.value = 'Error al crear el post. Revisa los campos.';
  }
}

// -------------------------------------------------------------------------
// JSON IMPORT mode
// -------------------------------------------------------------------------
const jsonRaw = ref('');
const jsonParsed = ref(null);
const jsonError = ref('');
const uploadedFileName = ref('');
const isDownloading = ref(false);

const jsonMeta = reactive({
  category: '',
  read_time_minutes: 8,
  is_featured: false,
});
const jsonPublishMode = ref('draft');
const jsonScheduledDate = ref('');

function parseJson() {
  jsonError.value = '';
  jsonParsed.value = null;
  const raw = jsonRaw.value.trim();
  if (!raw) return;

  let parsed;
  try { parsed = JSON.parse(raw); }
  catch { jsonError.value = 'JSON inválido. Revisa la sintaxis.'; return; }

  if (typeof parsed !== 'object' || Array.isArray(parsed)) {
    jsonError.value = 'El JSON debe ser un objeto, no un array.'; return;
  }
  if (!parsed.title_es || !parsed.title_en) {
    jsonError.value = 'El JSON debe incluir "title_es" y "title_en".'; return;
  }
  if (!parsed.content_json_es || !parsed.content_json_es.intro) {
    jsonError.value = 'El JSON debe incluir "content_json_es" con "intro" y "sections".'; return;
  }

  jsonParsed.value = parsed;
  if (parsed.category) jsonMeta.category = parsed.category;
  if (parsed.read_time_minutes) jsonMeta.read_time_minutes = parsed.read_time_minutes;
}

function handleFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  uploadedFileName.value = file.name;
  const reader = new FileReader();
  reader.onload = (e) => { jsonRaw.value = e.target.result; parseJson(); };
  reader.readAsText(file);
}

async function downloadTemplate() {
  isDownloading.value = true;
  try {
    const result = await blogStore.downloadJSONTemplate();
    if (result.success) {
      const jsonStr = JSON.stringify(result.data, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'blog-template.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  } catch (err) {
    console.error('Error downloading template:', err);
  } finally {
    isDownloading.value = false;
  }
}

async function handleJsonSubmit() {
  errorMsg.value = '';
  if (!jsonParsed.value) { errorMsg.value = 'Pega o sube un JSON válido primero.'; return; }

  const p = jsonParsed.value;
  const payload = {
    title_es: p.title_es,
    title_en: p.title_en,
    excerpt_es: p.excerpt_es || '',
    excerpt_en: p.excerpt_en || '',
    content_json_es: p.content_json_es,
    content_json_en: p.content_json_en || {},
    cover_image_url: p.cover_image_url || p.cover_image || '',
    sources: p.sources || [],
    category: jsonMeta.category,
    read_time_minutes: jsonMeta.read_time_minutes,
    is_featured: jsonMeta.is_featured,
    meta_title_es: p.meta_title_es || '',
    meta_title_en: p.meta_title_en || '',
    meta_description_es: p.meta_description_es || '',
    meta_description_en: p.meta_description_en || '',
    meta_keywords_es: p.meta_keywords_es || '',
    meta_keywords_en: p.meta_keywords_en || '',
    cover_image_credit: p.cover_image_credit || '',
    cover_image_credit_url: p.cover_image_credit_url || '',
    linkedin_summary_es: p.linkedin_summary_es || '',
    linkedin_summary_en: p.linkedin_summary_en || '',
    author: p.author || 'projectapp-team',
  };

  if (jsonPublishMode.value === 'now') {
    payload.is_published = true;
  } else if (jsonPublishMode.value === 'schedule') {
    payload.is_published = false;
    payload.published_at = jsonScheduledDate.value ? new Date(jsonScheduledDate.value).toISOString() : null;
  } else {
    payload.is_published = false;
  }

  const result = await blogStore.createPostFromJSON(payload);
  if (result.success) {
    navigateTo(localePath('/panel/blog'));
  } else {
    errorMsg.value = 'Error al crear el post desde JSON. Revisa los campos.';
  }
}
</script>
