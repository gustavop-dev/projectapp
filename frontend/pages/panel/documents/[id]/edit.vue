<template>
  <div class="w-full">
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
      <div class="min-w-0">
        <NuxtLink
          :to="localePath('/panel/documents')"
          class="inline-flex items-center gap-1 text-sm text-text-muted hover:text-text-default transition-colors"
          aria-label="Volver a documentos"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Volver a documentos
        </NuxtLink>
        <h1 class="text-2xl font-light text-text-default mt-2 truncate">
          {{ documentStore.currentDocument?.title || 'Editar Documento' }}
        </h1>
        <p v-if="documentStore.currentDocument" class="text-sm text-text-muted mt-1">
          {{ statusLabel }}{{ form.client_name ? ` · ${form.client_name}` : '' }}
        </p>
      </div>
      <div v-if="documentStore.currentDocument && !loadError" class="hidden lg:flex items-center gap-3">
        <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-text-muted hover:text-text-default">
          Cancelar
        </NuxtLink>
        <button
          type="button"
          :disabled="isDownloading"
          class="px-5 py-2.5 bg-surface text-text-default border border-border-default rounded-xl font-medium text-sm
                 hover:bg-surface-raised hover:border-border-default transition-colors disabled:opacity-50"
          @click="handleDownloadPdf"
        >
          {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
        </button>
        <button
          type="submit"
          form="doc-edit-form"
          :disabled="documentStore.isUpdating"
          class="px-5 py-2.5 bg-primary text-white rounded-xl font-medium text-sm
                 hover:bg-primary transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ documentStore.isUpdating ? 'Guardando...' : 'Guardar' }}
        </button>
      </div>
    </div>

    <div v-if="documentStore.isLoading" class="text-center py-12 text-text-subtle text-sm">
      Cargando...
    </div>

    <div v-else-if="loadError" class="text-center py-16">
      <p class="text-text-muted text-sm">No se pudo cargar el documento.</p>
      <NuxtLink
        :to="localePath('/panel/documents')"
        class="inline-flex items-center gap-1 mt-3 text-sm text-text-brand hover:text-text-brand"
      >
        ← Volver a la lista
      </NuxtLink>
    </div>

    <form
      v-else-if="documentStore.currentDocument"
      id="doc-edit-form"
      class="grid grid-cols-1 lg:grid-cols-[20rem_minmax(0,1fr)] xl:grid-cols-[24rem_minmax(0,1fr)] gap-6"
      @submit.prevent="handleSave"
    >
      <aside
        class="bg-surface rounded-xl shadow-sm border border-border-muted p-5 sm:p-6
               lg:sticky lg:top-6 lg:self-start lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto"
      >
        <div class="space-y-6">
          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Identificación</h2>
            <div>
              <label for="edit-title" class="block text-sm font-medium text-text-default mb-1">Título</label>
              <input
                id="edit-title"
                v-model="form.title"
                type="text"
                required
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
              />
            </div>
            <div>
              <label for="edit-client" class="block text-sm font-medium text-text-default mb-1">Nombre del cliente</label>
              <input
                id="edit-client"
                v-model="form.client_name"
                type="text"
                placeholder="Empresa S.A."
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default placeholder:text-text-subtle
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Estado</label>
              <select
                v-model="form.status"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
              >
                <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>

          <hr class="border-border-muted" />

          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Organización</h2>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Carpeta</label>
              <select
                v-model="form.folder_id"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
              >
                <option :value="null">Sin carpeta</option>
                <option v-for="folder in folderStore.folders" :key="folder.id" :value="folder.id">
                  {{ folder.name }}
                </option>
              </select>
            </div>
            <TagSelector v-model="form.tag_ids" :tags="tagStore.tags" />
          </div>

          <hr class="border-border-muted" />

          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Opciones de exportación</h2>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Idioma</label>
              <select
                v-model="form.language"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
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
                  <span class="block w-10 h-6 rounded-full transition-colors duration-200 bg-surface-raised peer-checked:bg-primary"></span>
                  <span class="absolute top-1 left-1 w-4 h-4 bg-surface rounded-full shadow transition-transform duration-200 peer-checked:translate-x-4"></span>
                </span>
                <span class="text-sm font-medium text-text-default">{{ option.label }}</span>
              </label>
            </div>
          </div>
        </div>
      </aside>

      <section
        class="bg-surface rounded-xl shadow-sm border border-border-muted p-5 sm:p-6
               flex flex-col min-w-0"
      >
        <div class="flex items-center justify-between mb-3 gap-3 flex-wrap">
          <label for="edit-markdown" class="block text-sm font-medium text-text-default">Contenido Markdown</label>
          <div class="flex items-center gap-2 flex-wrap">
            <span v-if="form.content_markdown" class="text-xs text-text-subtle tabular-nums">
              {{ form.content_markdown.length.toLocaleString() }} caracteres
            </span>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors
                     bg-surface-raised text-text-muted hover:bg-surface-raised"
              :disabled="!form.content_markdown.trim()"
              @click="showFullPreview = true"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
              Vista completa
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
              :class="showPreview
                ? 'bg-primary-soft text-text-brand hover:bg-primary-soft'
                : 'bg-surface-raised text-text-muted hover:bg-surface-raised'"
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
            id="edit-markdown"
            v-model="form.content_markdown"
            placeholder="# Contenido del documento..."
            class="w-full px-4 py-3 border border-border-default rounded-xl text-sm font-mono leading-relaxed bg-surface text-text-default placeholder:text-text-subtle
                   focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none resize-none
                   min-h-[24rem] lg:h-[calc(100vh-18rem)]"
          ></textarea>
          <div
            v-if="showPreview"
            class="border border-border-default rounded-xl bg-surface overflow-y-auto
                   min-h-[24rem] lg:h-[calc(100vh-18rem)]"
          >
            <div class="sticky top-0 px-3 py-2 border-b border-border-default bg-surface-raised rounded-t-xl z-10">
              <span class="text-xs font-medium text-text-muted uppercase tracking-wide">Vista previa</span>
            </div>
            <div
              v-if="form.content_markdown.trim()"
              class="markdown-preview px-5 py-4"
              v-html="previewHtml"
            ></div>
            <div
              v-else
              class="flex items-center justify-center h-64 text-sm text-text-subtle"
            >
              Escribe markdown para ver la vista previa...
            </div>
          </div>
        </div>

        <div v-if="errorMsg" class="mt-4 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl dark:bg-red-900/20 dark:text-red-400">
          {{ errorMsg }}
        </div>

        <div v-if="saveSuccess" class="mt-4 text-sm text-text-brand bg-primary-soft px-4 py-3 rounded-xl">
          Documento guardado correctamente.
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-3 lg:hidden">
          <button
            type="submit"
            :disabled="documentStore.isUpdating"
            class="px-5 sm:px-6 py-2.5 bg-primary text-white rounded-xl font-medium text-sm
                   hover:bg-primary transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ documentStore.isUpdating ? 'Guardando...' : 'Guardar' }}
          </button>
          <button
            type="button"
            :disabled="isDownloading"
            class="px-5 sm:px-6 py-2.5 bg-surface text-text-default border border-border-default rounded-xl font-medium text-sm
                   hover:bg-surface-raised hover:border-border-default transition-colors disabled:opacity-50"
            @click="handleDownloadPdf"
          >
            {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
          </button>
          <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-text-muted hover:text-text-default">
            Cancelar
          </NuxtLink>
        </div>
      </section>
    </form>

    <MarkdownPreviewModal
      v-model="showFullPreview"
      :title="form.title || 'Vista previa'"
    >
      <div
        v-if="form.content_markdown.trim()"
        class="markdown-preview markdown-preview--full max-w-4xl mx-auto"
        v-html="previewHtml"
      ></div>
      <div v-else class="flex items-center justify-center h-full text-sm text-text-subtle">
        No hay contenido para mostrar.
      </div>
    </MarkdownPreviewModal>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue';
import TagSelector from '~/components/panel/documents/TagSelector.vue';
import MarkdownPreviewModal from '~/components/panel/documents/MarkdownPreviewModal.vue';
const { parseMarkdown } = useMarkdownPreview();

const localePath = useLocalePath();
const route = useRoute();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const tagStore = useDocumentTagStore();
const errorMsg = ref('');
const saveSuccess = ref(false);
const loadError = ref(false);
const isDownloading = ref(false);
const showPreview = ref(true);
const showFullPreview = ref(false);

const form = reactive({
  title: '',
  client_name: '',
  language: 'es',
  include_portada: true,
  include_subportada: true,
  include_contraportada: true,
  status: 'draft',
  content_markdown: '',
  folder_id: null,
  tag_ids: [],
});

const coverOptions = [
  { key: 'include_portada', label: 'Incluir portada' },
  { key: 'include_subportada', label: 'Incluir subportada' },
  { key: 'include_contraportada', label: 'Incluir contraportada' },
];

const statusOptions = [
  { value: 'draft', label: 'Borrador' },
  { value: 'published', label: 'Publicado' },
  { value: 'archived', label: 'Archivado' },
];

const previewHtml = computed(() => parseMarkdown(form.content_markdown));
const statusLabel = computed(
  () => statusOptions.find((option) => option.value === form.status)?.label || '',
);

onMounted(async () => {
  const id = route.params.id;
  const [result] = await Promise.all([
    documentStore.fetchDocument(id),
    folderStore.fetchFolders(),
    tagStore.fetchTags(),
  ]);
  if (result.success && result.data) {
    form.title = result.data.title || '';
    form.client_name = result.data.client_name || '';
    form.language = result.data.language || 'es';
    form.include_portada = result.data.include_portada !== undefined ? result.data.include_portada : true;
    form.include_subportada = result.data.include_subportada !== undefined ? result.data.include_subportada : true;
    form.include_contraportada = result.data.include_contraportada !== undefined ? result.data.include_contraportada : true;
    form.status = result.data.status || 'draft';
    form.content_markdown = result.data.content_markdown || '';
    form.folder_id = result.data.folder || null;
    form.tag_ids = Array.isArray(result.data.tag_ids) ? [...result.data.tag_ids] : [];
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
    folder_id: form.folder_id,
    tag_ids: form.tag_ids,
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

.markdown-preview--full :deep(.md-h1) { font-size: 2rem; }
.markdown-preview--full :deep(.md-h2) { font-size: 1.5rem; }
.markdown-preview--full :deep(.md-h3) { font-size: 1.25rem; }
.markdown-preview--full :deep(.md-p),
.markdown-preview--full :deep(.md-ul),
.markdown-preview--full :deep(.md-ol),
.markdown-preview--full :deep(.md-blockquote) {
  font-size: 1rem;
  line-height: 1.75;
}
.markdown-preview--full :deep(.md-table) { font-size: 0.95rem; }
.markdown-preview--full :deep(.md-code-block) { font-size: 0.9rem; }
</style>
