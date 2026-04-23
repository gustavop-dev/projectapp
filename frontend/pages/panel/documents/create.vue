<template>
  <div class="w-full">
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
      <div>
        <NuxtLink
          :to="localePath('/panel/documents')"
          class="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
          aria-label="Volver a documentos"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Volver a documentos
        </NuxtLink>
        <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-2">Nuevo Documento</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Crea un documento a partir de Markdown (pegado o subido).</p>
      </div>
      <div class="hidden lg:flex items-center gap-3">
        <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
          Cancelar
        </NuxtLink>
        <button
          type="submit"
          form="doc-create-form"
          :disabled="!canSubmit"
          :title="canSubmit ? '' : 'Falta título o contenido'"
          class="px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                 hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ documentStore.isUpdating ? 'Creando...' : 'Crear Documento' }}
        </button>
      </div>
    </div>

    <form
      id="doc-create-form"
      class="grid grid-cols-1 lg:grid-cols-[20rem_minmax(0,1fr)] xl:grid-cols-[24rem_minmax(0,1fr)] gap-6"
      @submit.prevent="handleSubmit"
    >
      <aside
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 sm:p-6 dark:bg-gray-800 dark:border-gray-700
               lg:sticky lg:top-6 lg:self-start lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto"
      >
        <div class="space-y-6">
          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-gray-500 dark:text-gray-400">Identificación</h2>
            <div>
              <label for="doc-title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título *</label>
              <input
                id="doc-title"
                v-model="form.title"
                type="text"
                required
                placeholder="Mi Documento"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                       dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
              />
            </div>
            <div>
              <label for="doc-client" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre del cliente</label>
              <input
                id="doc-client"
                v-model="form.client_name"
                type="text"
                placeholder="Empresa S.A."
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                       dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
              />
            </div>
          </div>

          <hr class="border-gray-100 dark:border-gray-700" />

          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-gray-500 dark:text-gray-400">Organización</h2>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Carpeta</label>
              <select
                v-model="form.folder_id"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white
                       dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
              >
                <option :value="null">Sin carpeta</option>
                <option v-for="folder in folderStore.folders" :key="folder.id" :value="folder.id">
                  {{ folder.name }}
                </option>
              </select>
            </div>
            <TagSelector v-model="form.tag_ids" :tags="tagStore.tags" />
          </div>

          <hr class="border-gray-100 dark:border-gray-700" />

          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-gray-500 dark:text-gray-400">Opciones de exportación</h2>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Idioma</label>
              <select
                v-model="form.language"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white
                       dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
              >
                <option value="es">Español</option>
                <option value="en">English</option>
              </select>
            </div>
            <div class="space-y-1">
              <label
                v-for="option in coverOptions"
                :key="option.key"
                class="flex items-center gap-3 cursor-pointer py-1.5 px-1 select-none"
              >
                <span class="relative flex-shrink-0">
                  <input v-model="form[option.key]" type="checkbox" class="sr-only peer" />
                  <span class="block w-10 h-6 rounded-full transition-colors duration-200 bg-gray-200 peer-checked:bg-emerald-500 dark:bg-gray-600 dark:peer-checked:bg-emerald-500"></span>
                  <span class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 peer-checked:translate-x-4"></span>
                </span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ option.label }}</span>
              </label>
            </div>
          </div>
        </div>
      </aside>

      <section
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 sm:p-6 dark:bg-gray-800 dark:border-gray-700
               flex flex-col min-w-0"
      >
        <div class="flex gap-1 mb-5 bg-gray-100 dark:bg-gray-700 rounded-xl p-1 w-full sm:w-fit">
          <button
            v-for="tab in modeTabs"
            :key="tab.id"
            type="button"
            :class="[
              'inline-flex items-center justify-center gap-2 flex-1 sm:flex-none sm:min-w-[11rem] px-4 py-2 text-sm rounded-lg transition-all',
              mode === tab.id
                ? 'bg-white dark:bg-gray-800 shadow-sm font-medium text-gray-900 dark:text-gray-100 ring-1 ring-emerald-500/20'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            ]"
            @click="mode = tab.id"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="tab.iconPath" />
            </svg>
            {{ tab.label }}
          </button>
        </div>

        <div v-if="mode === 'paste'" class="flex-1 flex flex-col min-h-0">
          <div class="flex items-center justify-between mb-2 gap-3 flex-wrap">
            <label for="doc-markdown" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Contenido Markdown *</label>
            <div class="flex items-center gap-3">
              <span v-if="form.content_markdown" class="text-xs text-gray-400 dark:text-gray-500 tabular-nums">
                {{ form.content_markdown.length.toLocaleString() }} caracteres
              </span>
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
          </div>
          <div :class="showPreview ? 'grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0' : 'flex-1 min-h-0 flex'">
            <textarea
              id="doc-markdown"
              v-model="form.content_markdown"
              placeholder="# Mi Documento&#10;&#10;Escribe o pega tu contenido en formato Markdown..."
              class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm font-mono leading-relaxed
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-none
                     min-h-[24rem] lg:h-[calc(100vh-20rem)]
                     dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
            ></textarea>
            <div
              v-if="showPreview"
              class="border border-gray-200 rounded-xl bg-white overflow-y-auto dark:bg-gray-900 dark:border-gray-600
                     min-h-[24rem] lg:h-[calc(100vh-20rem)]"
            >
              <div class="sticky top-0 px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-t-xl z-10">
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

        <div v-if="mode === 'upload'" class="flex-1 flex flex-col">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Archivo Markdown (.md)</label>
          <div
            :class="[
              'border-2 border-dashed rounded-xl p-8 sm:p-10 text-center transition-colors',
              isDragging
                ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                : 'border-gray-200 hover:border-gray-300 dark:border-gray-600 dark:hover:border-gray-500'
            ]"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
          >
            <svg class="w-10 h-10 mx-auto text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="mt-3 text-sm text-gray-600 dark:text-gray-300">
              Arrastra un archivo <code class="text-xs px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">.md</code> aquí
            </p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">o</p>
            <label
              class="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium
                     hover:bg-emerald-700 cursor-pointer transition-colors shadow-sm"
            >
              Seleccionar archivo
              <input type="file" accept=".md,.markdown,.txt" class="hidden" @change="handleFileUpload" />
            </label>
            <p v-if="uploadedFileName" class="mt-4 text-xs text-gray-500 dark:text-gray-400">
              <span class="font-medium">Archivo:</span> {{ uploadedFileName }}
            </p>
          </div>
          <textarea
            v-model="form.content_markdown"
            rows="12"
            readonly
            placeholder="El contenido del archivo aparecerá aquí..."
            class="w-full mt-4 px-4 py-3 border border-gray-200 rounded-xl text-sm font-mono leading-relaxed
                   bg-gray-50 outline-none resize-y
                   dark:bg-gray-700/50 dark:border-gray-600 dark:text-gray-300 dark:placeholder-gray-500"
          ></textarea>
        </div>

        <div v-if="errorMsg" class="mt-4 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl dark:bg-red-900/20 dark:text-red-400">
          {{ errorMsg }}
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-4 lg:hidden">
          <button
            type="submit"
            :disabled="!canSubmit"
            class="px-5 sm:px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                   hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ documentStore.isUpdating ? 'Creando...' : 'Crear Documento' }}
          </button>
          <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
            Cancelar
          </NuxtLink>
        </div>
      </section>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue';
import TagSelector from '~/components/panel/documents/TagSelector.vue';
const { parseMarkdown } = useMarkdownPreview();

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const tagStore = useDocumentTagStore();
const errorMsg = ref('');
const mode = ref('paste');
const uploadedFileName = ref('');
const showPreview = ref(true);
const isDragging = ref(false);
const route = useRoute();

const form = reactive({
  title: '',
  client_name: '',
  language: 'es',
  include_portada: true,
  include_subportada: true,
  include_contraportada: true,
  content_markdown: '',
  folder_id: null,
  tag_ids: [],
});

onMounted(async () => {
  await Promise.all([folderStore.fetchFolders(), tagStore.fetchTags()]);
  const preselectFolder = route.query.folder;
  if (preselectFolder && preselectFolder !== 'all' && preselectFolder !== 'none') {
    const numeric = Number(preselectFolder);
    if (!Number.isNaN(numeric)) form.folder_id = numeric;
  }
});

const previewHtml = computed(() => parseMarkdown(form.content_markdown));
const canSubmit = computed(
  () => !documentStore.isUpdating && form.title.trim() && form.content_markdown.trim(),
);

const coverOptions = [
  { key: 'include_portada', label: 'Incluir portada' },
  { key: 'include_subportada', label: 'Incluir subportada' },
  { key: 'include_contraportada', label: 'Incluir contraportada' },
];

const modeTabs = [
  {
    id: 'paste',
    label: 'Pegar Markdown',
    iconPath: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
  },
  {
    id: 'upload',
    label: 'Cargar Archivo',
    iconPath: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12',
  },
];

function readMarkdownFile(file) {
  if (!file) return;
  uploadedFileName.value = file.name;
  const reader = new FileReader();
  reader.onload = (e) => {
    form.content_markdown = e.target?.result || '';
  };
  reader.readAsText(file);
}

function handleFileUpload(event) {
  readMarkdownFile(event.target.files?.[0]);
}

function handleDragLeave(event) {
  // dragleave also fires when the cursor enters a child; ignore those so the highlight doesn't flicker.
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isDragging.value = false;
  }
}

function handleDrop(event) {
  isDragging.value = false;
  readMarkdownFile(event.dataTransfer?.files?.[0]);
}

function formatError(errors) {
  if (errors && typeof errors === 'object') {
    return Object.entries(errors)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join(' | ');
  }
  return 'Error al crear el documento.';
}

async function handleSubmit() {
  errorMsg.value = '';
  const payload = {
    title: form.title.trim(),
    client_name: form.client_name.trim(),
    language: form.language,
    include_portada: form.include_portada,
    include_subportada: form.include_subportada,
    include_contraportada: form.include_contraportada,
    markdown: form.content_markdown,
    folder_id: form.folder_id,
    tag_ids: form.tag_ids,
  };

  const result = await documentStore.createFromMarkdown(payload);
  if (result.success) {
    navigateTo(localePath(`/panel/documents/${result.data.id}/edit`));
  } else {
    errorMsg.value = formatError(result.errors);
  }
}
</script>

<style scoped>
/* Markdown preview typography styles */
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
.markdown-preview :deep(.md-ul) {
  list-style-type: disc;
}
.markdown-preview :deep(.md-ol) {
  list-style-type: decimal;
}
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
.markdown-preview :deep(.md-inline-code) {
  background-color: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 0.25rem;
  padding: 0.125rem 0.375rem;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 0.825em;
  color: #dc2626;
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
.markdown-preview :deep(.md-link:hover) {
  color: #047857;
}
.markdown-preview :deep(strong) {
  font-weight: 600;
}
.markdown-preview :deep(em) {
  font-style: italic;
}

/* Dark mode overrides — use :global(.dark) to reach <html class="dark"> from scoped context */
:global(.dark) .markdown-preview :deep(.md-h1) {
  color: #6ee7b7;
  border-bottom-color: #374151;
}
:global(.dark) .markdown-preview :deep(.md-h2) {
  color: #6ee7b7;
}
:global(.dark) .markdown-preview :deep(.md-h3) {
  color: #a7f3d0;
}
:global(.dark) .markdown-preview :deep(.md-h4),
:global(.dark) .markdown-preview :deep(.md-h5),
:global(.dark) .markdown-preview :deep(.md-h6) {
  color: #a7f3d0;
}
:global(.dark) .markdown-preview :deep(.md-p),
:global(.dark) .markdown-preview :deep(.md-ul),
:global(.dark) .markdown-preview :deep(.md-ol) {
  color: #d1d5db;
}
:global(.dark) .markdown-preview :deep(.md-ul li),
:global(.dark) .markdown-preview :deep(.md-ol li) {
  color: #d1d5db;
}
:global(.dark) .markdown-preview :deep(.md-blockquote) {
  background-color: rgba(16, 185, 129, 0.1);
  border-left-color: #10b981;
  color: #9ca3af;
}
:global(.dark) .markdown-preview :deep(.md-code-block) {
  background-color: #1f2937;
  border-color: #374151;
}
:global(.dark) .markdown-preview :deep(.md-code-block code) {
  color: #e5e7eb;
}
:global(.dark) .markdown-preview :deep(.md-inline-code) {
  background-color: #1f2937;
  border-color: #374151;
  color: #f87171;
}
:global(.dark) .markdown-preview :deep(.md-table th) {
  background-color: #1f2937;
  border-color: #374151;
  color: #d1d5db;
}
:global(.dark) .markdown-preview :deep(.md-table td) {
  border-color: #374151;
  color: #9ca3af;
}
:global(.dark) .markdown-preview :deep(.md-table tbody tr:nth-child(even)) {
  background-color: rgba(31, 41, 55, 0.5);
}
:global(.dark) .markdown-preview :deep(.md-hr) {
  border-top-color: #374151;
}
:global(.dark) .markdown-preview :deep(.md-link) {
  color: #6ee7b7;
}
:global(.dark) .markdown-preview :deep(.md-link:hover) {
  color: #a7f3d0;
}

/* Strikethrough */
.markdown-preview :deep(del) {
  text-decoration: line-through;
  color: #6b7280;
}

/* Inline code */
.markdown-preview :deep(code) {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85em;
  background-color: #f3f4f6;
  color: #374151;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid #e5e7eb;
}

/* Nested lists */
.markdown-preview :deep(ul ul),
.markdown-preview :deep(ol ol),
.markdown-preview :deep(ul ol),
.markdown-preview :deep(ol ul) {
  margin-top: 4px;
  margin-bottom: 4px;
  margin-left: 20px;
}

/* Callouts */
.markdown-preview :deep(.callout) {
  border-radius: 6px;
  padding: 10px 14px;
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.markdown-preview :deep(.callout-label) {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.markdown-preview :deep(.callout-body) {
  font-size: 13px;
  line-height: 1.5;
}
.markdown-preview :deep(.callout-note) {
  background-color: #e6efef;
  border-left: 3px solid #002921;
}
.markdown-preview :deep(.callout-note .callout-label) { color: #002921; }
.markdown-preview :deep(.callout-tip) {
  background-color: #f0fff4;
  border-left: 3px solid #809490;
}
.markdown-preview :deep(.callout-tip .callout-label) { color: #809490; }
.markdown-preview :deep(.callout-important) {
  background-color: #eef2ff;
  border-left: 3px solid #6366f1;
}
.markdown-preview :deep(.callout-important .callout-label) { color: #6366f1; }
.markdown-preview :deep(.callout-warning) {
  background-color: #fffbeb;
  border-left: 3px solid #d97706;
}
.markdown-preview :deep(.callout-warning .callout-label) { color: #d97706; }
.markdown-preview :deep(.callout-caution) {
  background-color: #fff1f2;
  border-left: 3px solid #f43f5e;
}
.markdown-preview :deep(.callout-caution .callout-label) { color: #f43f5e; }

/* Dark mode overrides for new elements */
:global(.dark) .markdown-preview :deep(del) { color: #9ca3af; }
:global(.dark) .markdown-preview :deep(code) {
  background-color: #374151;
  color: #d1d5db;
  border-color: #4b5563;
}
:global(.dark) .markdown-preview :deep(.callout-note) {
  background-color: #0d2b24;
  border-color: #809490;
}
:global(.dark) .markdown-preview :deep(.callout-tip) {
  background-color: #052e16;
  border-color: #4ade80;
}
:global(.dark) .markdown-preview :deep(.callout-tip .callout-label) { color: #4ade80; }
:global(.dark) .markdown-preview :deep(.callout-important) {
  background-color: #1e1b4b;
  border-color: #818cf8;
}
:global(.dark) .markdown-preview :deep(.callout-important .callout-label) { color: #818cf8; }
:global(.dark) .markdown-preview :deep(.callout-warning) {
  background-color: #1c1400;
  border-color: #fbbf24;
}
:global(.dark) .markdown-preview :deep(.callout-warning .callout-label) { color: #fbbf24; }
:global(.dark) .markdown-preview :deep(.callout-caution) {
  background-color: #200a0e;
  border-color: #fb7185;
}
:global(.dark) .markdown-preview :deep(.callout-caution .callout-label) { color: #fb7185; }
</style>
