<template>
  <div>
    <div class="flex items-center gap-4 mb-8">
      <NuxtLink :to="localePath('/panel/portfolio')" class="text-text-subtle hover:text-text-muted transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </NuxtLink>
      <h1 class="text-2xl font-light text-text-default">Editar Proyecto</h1>
      <a v-if="work?.slug" :href="`/portfolio-works/${work.slug}`" target="_blank" class="text-xs text-text-brand hover:text-text-brand  dark:hover:text-emerald-300 transition-colors ml-auto">
        Ver en público →
      </a>
    </div>

    <!-- Loading -->
    <div v-if="portfolioStore.isLoading" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-focus-ring/30 border-t-focus-ring rounded-full animate-spin" />
    </div>

    <form v-else-if="work" class="space-y-6 max-w-3xl" @submit.prevent="handleSave">
      <!-- Cover image upload -->
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-5">
        <h3 class="text-sm font-medium text-text-default mb-3">Imagen de portada</h3>
        <div v-if="work.cover_image_display" class="mb-3 rounded-lg overflow-hidden aspect-[16/9] max-w-md">
          <img :src="work.cover_image_display" alt="Cover" class="w-full h-full object-cover" />
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <label class="inline-flex items-center gap-2 px-4 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm text-text-default hover:bg-surface-raised cursor-pointer transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            {{ isUploading ? 'Subiendo...' : 'Subir imagen' }}
            <input type="file" accept="image/*" class="hidden" :disabled="isUploading" @change="handleCoverUpload" />
          </label>
          <span class="text-xs text-text-subtle">o usa una URL externa abajo</span>
        </div>
        <input v-model="form.cover_image_url" type="url" class="bg-input-bg w-full mt-3 px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="URL externa de imagen (opcional)" />
      </div>

      <!-- Español -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-text-default px-2">Español</legend>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Título (ES)</label>
          <input v-model="form.title_es" type="text" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Tagline (ES)</label>
          <input v-model="form.excerpt_es" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Contenido JSON (ES)</label>
          <textarea v-model="contentJsonEsRaw" rows="12" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-xs font-mono focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all resize-y" placeholder='{ "problem": {...}, "solution": {...}, "results": {...} }' />
        </div>
      </fieldset>

      <!-- English -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-text-default px-2">English</legend>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Title (EN)</label>
          <input v-model="form.title_en" type="text" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Tagline (EN)</label>
          <input v-model="form.excerpt_en" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Content JSON (EN)</label>
          <textarea v-model="contentJsonEnRaw" rows="12" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-xs font-mono focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all resize-y" placeholder='{ "problem": {...}, "solution": {...}, "results": {...} }' />
        </div>
      </fieldset>

      <!-- Project URL + Slug + Order -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">URL del proyecto</label>
          <input v-model="form.project_url" type="url" required class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Slug</label>
          <input v-model="form.slug" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Orden</label>
          <input v-model.number="form.order" type="number" min="0" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
        </div>
      </div>

      <!-- SEO -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-4">
        <legend class="text-sm font-medium text-text-default px-2">SEO</legend>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-text-muted/60 mb-1">Meta título (ES)</label>
            <input v-model="form.meta_title_es" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted/60 mb-1">Meta title (EN)</label>
            <input v-model="form.meta_title_en" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted/60 mb-1">Meta descripción (ES)</label>
            <textarea v-model="form.meta_description_es" rows="2" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all resize-y" />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted/60 mb-1">Meta description (EN)</label>
            <textarea v-model="form.meta_description_en" rows="2" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all resize-y" />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted/60 mb-1">Keywords (ES)</label>
            <input v-model="form.meta_keywords_es" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="keyword1, keyword2" />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted/60 mb-1">Keywords (EN)</label>
            <input v-model="form.meta_keywords_en" type="text" class="bg-input-bg w-full px-4 py-2.5 rounded-xl border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 text-sm focus:ring-2 focus:ring-focus-ring/30/20 focus:border-focus-ring transition-all" placeholder="keyword1, keyword2" />
          </div>
        </div>
      </fieldset>

      <!-- Publishing -->
      <fieldset class="border border-border-default dark:border-white/[0.08] rounded-xl p-5 space-y-3">
        <legend class="text-sm font-medium text-text-default px-2">Publicación</legend>
        <label class="relative inline-flex items-center cursor-pointer gap-3">
          <input v-model="form.is_published" type="checkbox" class="sr-only peer" />
          <div class="w-9 h-5 bg-surface-raised peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-surface after:border-border-default after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary" />
          <span class="text-sm text-text-default">Publicado</span>
        </label>
      </fieldset>

      <!-- Error + actions -->
      <p v-if="errorMsg" class="text-sm text-red-500 dark:text-red-400">{{ errorMsg }}</p>
      <p v-if="successMsg" class="text-sm text-text-brand">{{ successMsg }}</p>

      <div class="flex gap-3 pt-4">
        <button type="submit" :disabled="portfolioStore.isUpdating" class="px-6 py-2.5 bg-primary text-white rounded-xl font-medium text-sm hover:bg-primary-strong transition-colors shadow-sm disabled:opacity-50">
          {{ portfolioStore.isUpdating ? 'Guardando...' : 'Guardar cambios' }}
        </button>
        <NuxtLink :to="localePath('/panel/portfolio')" class="px-6 py-2.5 border border-border-default dark:border-white/[0.08] text-text-muted rounded-xl text-sm hover:bg-surface-raised transition-colors">Volver</NuxtLink>
      </div>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { usePortfolioWorksStore } from '~/stores/portfolio_works';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const portfolioStore = usePortfolioWorksStore();
const work = computed(() => portfolioStore.currentWork);
const errorMsg = ref('');
const successMsg = ref('');
const isUploading = ref(false);

const form = reactive({
  title_es: '', title_en: '',
  excerpt_es: '', excerpt_en: '',
  project_url: '', cover_image_url: '', slug: '',
  order: 0, is_published: false,
  meta_title_es: '', meta_title_en: '',
  meta_description_es: '', meta_description_en: '',
  meta_keywords_es: '', meta_keywords_en: '',
});

const contentJsonEsRaw = ref('{}');
const contentJsonEnRaw = ref('{}');

function populateForm(w) {
  if (!w) return;
  form.title_es = w.title_es || '';
  form.title_en = w.title_en || '';
  form.excerpt_es = w.excerpt_es || '';
  form.excerpt_en = w.excerpt_en || '';
  form.project_url = w.project_url || '';
  form.cover_image_url = w.cover_image_url || '';
  form.slug = w.slug || '';
  form.order = w.order || 0;
  form.is_published = w.is_published || false;
  form.meta_title_es = w.meta_title_es || '';
  form.meta_title_en = w.meta_title_en || '';
  form.meta_description_es = w.meta_description_es || '';
  form.meta_description_en = w.meta_description_en || '';
  form.meta_keywords_es = w.meta_keywords_es || '';
  form.meta_keywords_en = w.meta_keywords_en || '';
  contentJsonEsRaw.value = w.content_json_es && Object.keys(w.content_json_es).length
    ? JSON.stringify(w.content_json_es, null, 2) : '{}';
  contentJsonEnRaw.value = w.content_json_en && Object.keys(w.content_json_en).length
    ? JSON.stringify(w.content_json_en, null, 2) : '{}';
}

onMounted(async () => {
  const id = Number(route.params.id);
  await portfolioStore.fetchAdminWork(id);
  populateForm(work.value);
});

watch(work, (w) => { if (w) populateForm(w); });

async function handleSave() {
  errorMsg.value = '';
  successMsg.value = '';

  let content_json_es = {};
  let content_json_en = {};
  try { content_json_es = JSON.parse(contentJsonEsRaw.value); }
  catch { errorMsg.value = 'JSON inválido en contenido español.'; return; }
  try { content_json_en = JSON.parse(contentJsonEnRaw.value); }
  catch { errorMsg.value = 'JSON inválido en contenido inglés.'; return; }

  const payload = {
    ...form,
    content_json_es,
    content_json_en,
  };

  const result = await portfolioStore.updateWork(Number(route.params.id), payload);
  if (result.success) {
    successMsg.value = 'Proyecto guardado correctamente.';
    setTimeout(() => { successMsg.value = ''; }, 3000);
  } else {
    errorMsg.value = 'Error al guardar. Revisa los campos.';
  }
}

async function handleCoverUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  isUploading.value = true;
  const result = await portfolioStore.uploadCoverImage(Number(route.params.id), file);
  isUploading.value = false;
  if (!result.success) {
    errorMsg.value = 'Error al subir la imagen.';
  }
}
</script>
