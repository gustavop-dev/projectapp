<template>
  <div>
    <div class="flex items-center gap-4 mb-8">
      <NuxtLink :to="localePath('/panel/portfolio')" class="text-text-subtle hover:text-text-muted transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </NuxtLink>
      <h1 class="text-2xl font-light text-text-default">Nuevo Proyecto</h1>
    </div>

    <!-- Tab toggle -->
    <div class="flex gap-1 mb-6 bg-surface-raised rounded-xl p-1 max-w-xs">
      <button type="button" :class="['flex-1 px-4 py-2 text-sm rounded-lg transition-all', mode === 'manual' ? 'bg-surface shadow-sm font-medium text-text-default' : 'text-text-muted hover:text-text-default']" @click="mode = 'manual'">
        Manual
      </button>
      <button type="button" :class="['flex-1 px-4 py-2 text-sm rounded-lg transition-all', mode === 'json' ? 'bg-surface shadow-sm font-medium text-text-default' : 'text-text-muted hover:text-text-default']" @click="mode = 'json'">
        Importar JSON
      </button>
    </div>

    <!-- MANUAL MODE -->
    <form v-if="mode === 'manual'" class="space-y-6 max-w-3xl" @submit.prevent="handleSubmit">
      <!-- Español -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-text-default px-2">Español</legend>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Título (ES)</label>
          <input v-model="form.title_es" type="text" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="Título del proyecto en español" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Tagline (ES)</label>
          <input v-model="form.excerpt_es" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="Tagline corto en español" />
        </div>
      </fieldset>

      <!-- English -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-text-default px-2">English</legend>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Title (EN)</label>
          <input v-model="form.title_en" type="text" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="Project title in English" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Tagline (EN)</label>
          <input v-model="form.excerpt_en" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="Short tagline in English" />
        </div>
      </fieldset>

      <!-- Project URL + Cover -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">URL del proyecto</label>
          <input v-model="form.project_url" type="url" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="https://example.com" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Imagen de portada (URL)</label>
          <input v-model="form.cover_image_url" type="url" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="https://... (opcional)" />
        </div>
      </div>

      <!-- Order -->
      <div class="max-w-[200px]">
        <label class="block text-sm font-medium text-text-default mb-1">Orden</label>
        <input v-model.number="form.order" type="number" min="0" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
      </div>

      <!-- Publishing -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-3">
        <legend class="text-sm font-medium text-text-default px-2">Publicación</legend>
        <label class="flex items-center gap-3 cursor-pointer">
          <input v-model="publishMode" type="radio" value="draft" name="pm" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
          <span class="text-sm text-text-default">Borrador</span>
        </label>
        <label class="flex items-center gap-3 cursor-pointer">
          <input v-model="publishMode" type="radio" value="now" name="pm" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
          <span class="text-sm text-text-default">Publicar ahora</span>
        </label>
      </fieldset>

      <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>

      <div class="flex gap-3 pt-4">
        <button type="submit" :disabled="portfolioStore.isUpdating" class="px-6 py-2.5 bg-primary text-white rounded-xl font-medium text-sm hover:bg-primary-strong transition-colors shadow-sm disabled:opacity-50">
          {{ portfolioStore.isUpdating ? 'Creando...' : 'Crear Proyecto' }}
        </button>
        <NuxtLink :to="localePath('/panel/portfolio')" class="px-6 py-2.5 border border-border-default dark:border-white/[0.08] text-text-muted rounded-xl text-sm hover:bg-surface-raised transition-colors">Cancelar</NuxtLink>
      </div>
    </form>

    <!-- JSON IMPORT MODE -->
    <div v-else class="max-w-3xl space-y-6">
      <!-- Download template -->
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 class="text-sm font-medium text-text-default">Plantilla JSON</h3>
            <p class="text-xs text-text-subtle mt-0.5">Descarga la plantilla con la estructura problem/solution/results.</p>
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
          <label class="inline-flex items-center gap-2 px-4 py-2 border border-border-default rounded-lg text-sm text-text-default hover:bg-surface-muted cursor-pointer transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
            Subir archivo .json
            <input type="file" accept=".json" class="hidden" @change="handleFileUpload" />
          </label>
          <span v-if="uploadedFileName" class="text-xs text-text-muted">{{ uploadedFileName }}</span>
        </div>
        <textarea v-model="jsonRaw" rows="14" placeholder='{ "title_es": "...", "title_en": "...", "project_url": "...", "content_json_es": { "problem": {...}, "solution": {...}, "results": {...} } }' class="bg-input-bg w-full px-4 py-3 border border-border-default rounded-xl text-xs font-mono leading-relaxed focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-y" @input="parseJson" />
        <div v-if="jsonError" class="mt-2 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-lg">{{ jsonError }}</div>
        <div v-if="jsonParsed && !jsonError" class="mt-3 bg-primary-soft border border-emerald-200 rounded-lg px-4 py-3">
          <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span><span class="text-text-muted">Título:</span> <span class="font-medium text-text-default">{{ jsonParsed.title_es }}</span></span>
            <span><span class="text-text-muted">URL:</span> <span class="font-medium text-text-default">{{ jsonParsed.project_url || '—' }}</span></span>
          </div>
        </div>
      </div>

      <!-- Submit from JSON -->
      <form v-if="jsonParsed && !jsonError" class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6" @submit.prevent="handleJsonSubmit">
        <h3 class="text-sm font-medium text-text-default mb-4">Opciones de publicación</h3>
        <div class="space-y-4">
          <fieldset class="border border-border-default rounded-xl p-4 space-y-3">
            <legend class="text-xs font-medium text-text-muted px-2">Publicación</legend>
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="jsonPublishMode" type="radio" value="draft" name="jpm" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
              <span class="text-sm text-text-default">Borrador</span>
            </label>
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="jsonPublishMode" type="radio" value="now" name="jpm" class="w-4 h-4 text-text-brand focus:ring-focus-ring/30" />
              <span class="text-sm text-text-default">Publicar ahora</span>
            </label>
          </fieldset>
          <div v-if="errorMsg" class="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl">{{ errorMsg }}</div>
          <div class="flex flex-wrap items-center gap-4 pt-2">
            <button type="submit" :disabled="portfolioStore.isUpdating" class="px-6 py-2.5 bg-primary text-white rounded-xl font-medium text-sm hover:bg-primary-strong transition-colors shadow-sm disabled:opacity-50">
              {{ portfolioStore.isUpdating ? 'Creando...' : 'Crear desde JSON' }}
            </button>
            <NuxtLink :to="localePath('/panel/portfolio')" class="text-sm text-text-muted hover:text-text-default">Cancelar</NuxtLink>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { usePortfolioWorksStore } from '~/stores/portfolio_works';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const portfolioStore = usePortfolioWorksStore();
const errorMsg = ref('');
const mode = ref('manual');
const publishMode = ref('draft');

const form = reactive({
  title_es: '', title_en: '',
  excerpt_es: '', excerpt_en: '',
  project_url: '', cover_image_url: '',
  order: 0,
});

async function handleSubmit() {
  errorMsg.value = '';
  const payload = { ...form, sources: [] };
  payload.is_published = publishMode.value === 'now';
  if (form.cover_image_url) payload.cover_image_url = form.cover_image_url;

  const result = await portfolioStore.createWork(payload);
  if (result.success) {
    navigateTo(localePath(`/panel/portfolio/${result.data.id}/edit`));
  } else {
    errorMsg.value = 'Error al crear el proyecto. Revisa los campos.';
  }
}

// JSON mode
const jsonRaw = ref('');
const jsonParsed = ref(null);
const jsonError = ref('');
const uploadedFileName = ref('');
const isDownloading = ref(false);
const jsonPublishMode = ref('draft');

function parseJson() {
  jsonError.value = '';
  jsonParsed.value = null;
  const raw = jsonRaw.value.trim();
  if (!raw) return;
  let parsed;
  try { parsed = JSON.parse(raw); }
  catch { jsonError.value = 'JSON inválido.'; return; }
  if (!parsed.title_es || !parsed.title_en) { jsonError.value = 'Falta "title_es" o "title_en".'; return; }
  if (!parsed.project_url) { jsonError.value = 'Falta "project_url".'; return; }
  if (!parsed.content_json_es) { jsonError.value = 'Falta "content_json_es".'; return; }
  jsonParsed.value = parsed;
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
    const result = await portfolioStore.downloadJSONTemplate();
    if (result.success) {
      const jsonStr = JSON.stringify(result.data, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'portfolio-template.json';
      document.body.appendChild(a); a.click();
      document.body.removeChild(a); URL.revokeObjectURL(url);
    }
  } finally { isDownloading.value = false; }
}

async function handleJsonSubmit() {
  errorMsg.value = '';
  if (!jsonParsed.value) { errorMsg.value = 'Pega o sube un JSON válido primero.'; return; }
  const p = jsonParsed.value;
  const payload = {
    title_es: p.title_es, title_en: p.title_en,
    excerpt_es: p.excerpt_es || '', excerpt_en: p.excerpt_en || '',
    content_json_es: p.content_json_es, content_json_en: p.content_json_en || {},
    project_url: p.project_url,
    cover_image_url: p.cover_image_url || '',
    is_published: jsonPublishMode.value === 'now',
    order: p.order || 0,
    meta_title_es: p.meta_title_es || '', meta_title_en: p.meta_title_en || '',
    meta_description_es: p.meta_description_es || '', meta_description_en: p.meta_description_en || '',
    meta_keywords_es: p.meta_keywords_es || '', meta_keywords_en: p.meta_keywords_en || '',
  };
  const result = await portfolioStore.createWorkFromJSON(payload);
  if (result.success) {
    navigateTo(localePath(`/panel/portfolio/${result.data.id}/edit`));
  } else {
    errorMsg.value = 'Error al crear desde JSON. Revisa los campos.';
  }
}
</script>
