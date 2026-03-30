<template>
  <div>
    <div class="mb-8">
      <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors">
        ← Volver a documentos
      </NuxtLink>
      <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-2">
        {{ documentStore.currentDocument?.title || 'Editar Documento' }}
      </h1>
    </div>

    <!-- Loading -->
    <div v-if="documentStore.isLoading" class="text-center py-12 text-gray-400 dark:text-gray-500 text-sm">
      Cargando...
    </div>

    <!-- Not found -->
    <div v-else-if="loadError" class="text-center py-16">
      <p class="text-gray-500 dark:text-gray-400 text-sm">No se pudo cargar el documento.</p>
      <NuxtLink
        :to="localePath('/panel/documents')"
        class="inline-flex items-center gap-1 mt-3 text-sm text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
      >
        ← Volver a la lista
      </NuxtLink>
    </div>

    <!-- Edit form -->
    <form v-else-if="documentStore.currentDocument" class="space-y-6 transition-all" :class="showPreview ? 'max-w-6xl' : 'max-w-3xl'" @submit.prevent="handleSave">
      <!-- Metadata card -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 dark:bg-gray-800 dark:border-gray-700">
        <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">Metadatos</h3>
        <div class="space-y-4">
          <!-- Title -->
          <div>
            <label for="edit-title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Titulo</label>
            <input
              id="edit-title"
              v-model="form.title"
              type="text"
              required
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                     dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
            />
          </div>

          <!-- Client name -->
          <div>
            <label for="edit-client" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre del cliente</label>
            <input
              id="edit-client"
              v-model="form.client_name"
              type="text"
              placeholder="Empresa S.A."
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                     dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
            />
          </div>

          <!-- Language + Cover toggles + Status -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Idioma</label>
              <select
                v-model="form.language"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white
                       dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
              >
                <option value="es">Espanol</option>
                <option value="en">English</option>
              </select>
            </div>
            <div class="flex flex-col justify-end gap-1">
              <label class="flex items-center gap-3 cursor-pointer py-1 px-1 select-none">
                <span class="relative flex-shrink-0">
                  <input v-model="form.include_portada" type="checkbox" class="sr-only peer" />
                  <span class="block w-10 h-6 rounded-full transition-colors duration-200 bg-gray-200 peer-checked:bg-emerald-500 dark:bg-gray-600 dark:peer-checked:bg-emerald-500"></span>
                  <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 peer-checked:translate-x-4"></span>
                </span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Portada</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer py-1 px-1 select-none">
                <span class="relative flex-shrink-0">
                  <input v-model="form.include_subportada" type="checkbox" class="sr-only peer" />
                  <span class="block w-10 h-6 rounded-full transition-colors duration-200 bg-gray-200 peer-checked:bg-emerald-500 dark:bg-gray-600 dark:peer-checked:bg-emerald-500"></span>
                  <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 peer-checked:translate-x-4"></span>
                </span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Subportada</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer py-1 px-1 select-none">
                <span class="relative flex-shrink-0">
                  <input v-model="form.include_contraportada" type="checkbox" class="sr-only peer" />
                  <span class="block w-10 h-6 rounded-full transition-colors duration-200 bg-gray-200 peer-checked:bg-emerald-500 dark:bg-gray-600 dark:peer-checked:bg-emerald-500"></span>
                  <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 peer-checked:translate-x-4"></span>
                </span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Contraportada</span>
              </label>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Estado</label>
              <select
                v-model="form.status"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white
                       dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
              >
                <option value="draft">Borrador</option>
                <option value="published">Publicado</option>
                <option value="archived">Archivado</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Content card -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 dark:bg-gray-800 dark:border-gray-700">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Contenido Markdown</h3>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
            :class="showPreview
              ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 dark:hover:bg-emerald-900/50'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600'"
            @click="showPreview = !showPreview"
          >
            <svg v-if="showPreview" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
            </svg>
            {{ showPreview ? 'Ocultar vista previa' : 'Vista previa' }}
          </button>
        </div>
        <div :class="showPreview ? 'grid grid-cols-1 lg:grid-cols-2 gap-4' : ''">
          <textarea
            v-model="form.content_markdown"
            rows="20"
            placeholder="# Contenido del documento..."
            class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm font-mono leading-relaxed
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y
                   dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
          ></textarea>
          <div
            v-if="showPreview"
            class="border border-gray-200 rounded-xl bg-white overflow-y-auto dark:bg-gray-900 dark:border-gray-600"
            style="min-height: 24rem; max-height: 40rem;"
          >
            <div class="px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-t-xl">
              <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Vista previa</span>
            </div>
            <div
              v-if="form.content_markdown.trim()"
              class="markdown-preview px-5 py-4"
              v-html="previewHtml"
            ></div>
            <div
              v-else
              class="flex items-center justify-center h-64 text-sm text-gray-400 dark:text-gray-500"
            >
              Escribe markdown para ver la vista previa...
            </div>
          </div>
        </div>
      </div>

      <!-- Errors -->
      <div v-if="errorMsg" class="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl dark:bg-red-900/20 dark:text-red-400">
        {{ errorMsg }}
      </div>

      <!-- Success -->
      <div v-if="saveSuccess" class="text-sm text-emerald-600 bg-emerald-50 px-4 py-3 rounded-xl dark:bg-emerald-900/20 dark:text-emerald-400">
        Documento guardado correctamente.
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          :disabled="documentStore.isUpdating"
          class="px-5 sm:px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                 hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
        >
          {{ documentStore.isUpdating ? 'Guardando...' : 'Guardar' }}
        </button>
        <button
          type="button"
          :disabled="isDownloading"
          class="px-5 sm:px-6 py-2.5 bg-white text-gray-700 border border-gray-200 rounded-xl font-medium text-sm
                 hover:bg-gray-50 hover:border-gray-300 transition-colors
                 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 disabled:opacity-50"
          @click="handleDownloadPdf"
        >
          {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
        </button>
        <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
          Cancelar
        </NuxtLink>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue';
const { parseMarkdown } = useMarkdownPreview();

const localePath = useLocalePath();
const route = useRoute();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const errorMsg = ref('');
const saveSuccess = ref(false);
const loadError = ref(false);
const isDownloading = ref(false);
const showPreview = ref(true);

const form = reactive({
  title: '',
  client_name: '',
  language: 'es',
  include_portada: true,
  include_subportada: true,
  include_contraportada: true,
  status: 'draft',
  content_markdown: '',
});

const previewHtml = computed(() => parseMarkdown(form.content_markdown));

onMounted(async () => {
  const id = route.params.id;
  const result = await documentStore.fetchDocument(id);
  if (result.success && result.data) {
    form.title = result.data.title || '';
    form.client_name = result.data.client_name || '';
    form.language = result.data.language || 'es';
    form.include_portada = result.data.include_portada !== undefined ? result.data.include_portada : true;
    form.include_subportada = result.data.include_subportada !== undefined ? result.data.include_subportada : true;
    form.include_contraportada = result.data.include_contraportada !== undefined ? result.data.include_contraportada : true;
    form.status = result.data.status || 'draft';
    form.content_markdown = result.data.content_markdown || '';
  } else {
    loadError.value = true;
  }
});

function formatError(errors) {
  if (errors && typeof errors === 'object') {
    return Object.entries(errors)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join(' | ');
  }
  return 'Error al guardar el documento.';
}

async function handleSave() {
  errorMsg.value = '';
  saveSuccess.value = false;

  const payload = {
    title: form.title.trim(),
    client_name: form.client_name.trim(),
    language: form.language,
    include_portada: form.include_portada,
    include_subportada: form.include_subportada,
    include_contraportada: form.include_contraportada,
    status: form.status,
    content_markdown: form.content_markdown,
  };

  const result = await documentStore.updateDocument(route.params.id, payload);
  if (result.success) {
    saveSuccess.value = true;
    setTimeout(() => { saveSuccess.value = false; }, 3000);
  } else {
    errorMsg.value = formatError(result.errors);
  }
}

async function handleDownloadPdf() {
  isDownloading.value = true;
  await documentStore.downloadPdf(route.params.id, form.title || 'document');
  isDownloading.value = false;
}
</script>

<style scoped>
.markdown-preview :deep(.md-h1) {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.3;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #d1d5db;
  color: #047857;
}
.markdown-preview :deep(.md-h2) {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.35;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  color: #047857;
}
.markdown-preview :deep(.md-h3) {
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.4;
  margin-top: 1rem;
  margin-bottom: 0.4rem;
  color: #059669;
}
.markdown-preview :deep(.md-h4),
.markdown-preview :deep(.md-h5),
.markdown-preview :deep(.md-h6) {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.4;
  margin-top: 0.85rem;
  margin-bottom: 0.35rem;
  color: #059669;
}
.markdown-preview :deep(.md-p) {
  margin-bottom: 0.75rem;
  line-height: 1.7;
  font-size: 0.875rem;
  color: #374151;
}
.markdown-preview :deep(.md-ul),
.markdown-preview :deep(.md-ol) {
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
  font-size: 0.875rem;
  color: #374151;
}
.markdown-preview :deep(.md-ul) { list-style-type: disc; }
.markdown-preview :deep(.md-ol) { list-style-type: decimal; }
.markdown-preview :deep(.md-ul li),
.markdown-preview :deep(.md-ol li) {
  margin-bottom: 0.25rem;
  line-height: 1.6;
}
.markdown-preview :deep(.md-blockquote) {
  border-left: 3px solid #10b981;
  background-color: #f0fdf4;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  font-style: italic;
  font-size: 0.875rem;
  color: #4b5563;
  border-radius: 0 0.5rem 0.5rem 0;
}
.markdown-preview :deep(.md-code-block) {
  background-color: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  overflow-x: auto;
  font-size: 0.8rem;
  line-height: 1.6;
}
.markdown-preview :deep(.md-code-block code) {
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  color: #1f2937;
}
.markdown-preview :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 0.75rem;
  font-size: 0.8rem;
}
.markdown-preview :deep(.md-table th) {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
}
.markdown-preview :deep(.md-table td) {
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  color: #4b5563;
}
.markdown-preview :deep(.md-table tbody tr:nth-child(even)) {
  background-color: #f9fafb;
}
.markdown-preview :deep(.md-hr) {
  border: none;
  border-top: 1px solid #d1d5db;
  margin: 1.25rem 0;
}
.markdown-preview :deep(.md-link) {
  color: #059669;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.markdown-preview :deep(.md-link:hover) { color: #047857; }
.markdown-preview :deep(strong) { font-weight: 600; }
.markdown-preview :deep(em) { font-style: italic; }
.markdown-preview :deep(del) { text-decoration: line-through; color: #6b7280; }
.markdown-preview :deep(code) {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85em;
  background-color: #f3f4f6;
  color: #374151;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid #e5e7eb;
}
.markdown-preview :deep(ul ul),
.markdown-preview :deep(ol ol),
.markdown-preview :deep(ul ol),
.markdown-preview :deep(ol ul) {
  margin-top: 4px;
  margin-bottom: 4px;
  margin-left: 20px;
}
.markdown-preview :deep(.callout) {
  border-radius: 6px;
  padding: 10px 14px;
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.markdown-preview :deep(.callout-label) { font-size: 11px; font-weight: 700; letter-spacing: 0.05em; }
.markdown-preview :deep(.callout-body) { font-size: 13px; line-height: 1.5; }
.markdown-preview :deep(.callout-note) { background-color: #e6efef; border-left: 3px solid #002921; }
.markdown-preview :deep(.callout-note .callout-label) { color: #002921; }
.markdown-preview :deep(.callout-tip) { background-color: #f0fff4; border-left: 3px solid #809490; }
.markdown-preview :deep(.callout-tip .callout-label) { color: #809490; }
.markdown-preview :deep(.callout-important) { background-color: #eef2ff; border-left: 3px solid #6366f1; }
.markdown-preview :deep(.callout-important .callout-label) { color: #6366f1; }
.markdown-preview :deep(.callout-warning) { background-color: #fffbeb; border-left: 3px solid #d97706; }
.markdown-preview :deep(.callout-warning .callout-label) { color: #d97706; }
.markdown-preview :deep(.callout-caution) { background-color: #fff1f2; border-left: 3px solid #f43f5e; }
.markdown-preview :deep(.callout-caution .callout-label) { color: #f43f5e; }

/* Dark mode */
:global(.dark) .markdown-preview :deep(.md-h1) { color: #6ee7b7; border-bottom-color: #374151; }
:global(.dark) .markdown-preview :deep(.md-h2) { color: #6ee7b7; }
:global(.dark) .markdown-preview :deep(.md-h3) { color: #a7f3d0; }
:global(.dark) .markdown-preview :deep(.md-h4),
:global(.dark) .markdown-preview :deep(.md-h5),
:global(.dark) .markdown-preview :deep(.md-h6) { color: #a7f3d0; }
:global(.dark) .markdown-preview :deep(.md-p),
:global(.dark) .markdown-preview :deep(.md-ul),
:global(.dark) .markdown-preview :deep(.md-ol) { color: #d1d5db; }
:global(.dark) .markdown-preview :deep(.md-ul li),
:global(.dark) .markdown-preview :deep(.md-ol li) { color: #d1d5db; }
:global(.dark) .markdown-preview :deep(.md-blockquote) {
  background-color: rgba(16, 185, 129, 0.1);
  border-left-color: #10b981;
  color: #9ca3af;
}
:global(.dark) .markdown-preview :deep(.md-code-block) { background-color: #1f2937; border-color: #374151; }
:global(.dark) .markdown-preview :deep(.md-code-block code) { color: #e5e7eb; }
:global(.dark) .markdown-preview :deep(.md-table th) { background-color: #1f2937; border-color: #374151; color: #d1d5db; }
:global(.dark) .markdown-preview :deep(.md-table td) { border-color: #374151; color: #9ca3af; }
:global(.dark) .markdown-preview :deep(.md-table tbody tr:nth-child(even)) { background-color: rgba(31, 41, 55, 0.5); }
:global(.dark) .markdown-preview :deep(.md-hr) { border-top-color: #374151; }
:global(.dark) .markdown-preview :deep(.md-link) { color: #6ee7b7; }
:global(.dark) .markdown-preview :deep(.md-link:hover) { color: #a7f3d0; }
:global(.dark) .markdown-preview :deep(del) { color: #9ca3af; }
:global(.dark) .markdown-preview :deep(code) { background-color: #374151; color: #d1d5db; border-color: #4b5563; }
:global(.dark) .markdown-preview :deep(.callout-note) { background-color: #0d2b24; border-color: #809490; }
:global(.dark) .markdown-preview :deep(.callout-tip) { background-color: #052e16; border-color: #4ade80; }
:global(.dark) .markdown-preview :deep(.callout-tip .callout-label) { color: #4ade80; }
:global(.dark) .markdown-preview :deep(.callout-important) { background-color: #1e1b4b; border-color: #818cf8; }
:global(.dark) .markdown-preview :deep(.callout-important .callout-label) { color: #818cf8; }
:global(.dark) .markdown-preview :deep(.callout-warning) { background-color: #1c1400; border-color: #fbbf24; }
:global(.dark) .markdown-preview :deep(.callout-warning .callout-label) { color: #fbbf24; }
:global(.dark) .markdown-preview :deep(.callout-caution) { background-color: #200a0e; border-color: #fb7185; }
:global(.dark) .markdown-preview :deep(.callout-caution .callout-label) { color: #fb7185; }
</style>
