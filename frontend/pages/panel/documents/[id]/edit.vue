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
        <BaseDropdown :items="downloadItems" align="right">
          <template #trigger>
            <button
              type="button"
              :disabled="isDownloading"
              class="px-5 py-2.5 bg-surface text-text-default border border-border-default rounded-xl font-medium text-sm
                     hover:bg-surface-raised transition-colors disabled:opacity-50 inline-flex items-center gap-1.5"
            >
              {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </template>
        </BaseDropdown>
        <button
          type="submit"
          form="doc-edit-form"
          :disabled="documentStore.isUpdating || !hasChanges"
          class="px-5 py-2.5 bg-primary text-white rounded-xl font-medium text-sm
                 hover:bg-primary transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ documentStore.isUpdating ? 'Guardando...' : 'Guardar' }}
        </button>
      </div>
    </div>

    <div
      v-if="documentStore.isLoading"
      class="grid grid-cols-1 lg:grid-cols-[20rem_minmax(0,1fr)] xl:grid-cols-[24rem_minmax(0,1fr)] gap-6"
      role="status"
    >
      <span class="sr-only">Cargando documento...</span>
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-6 space-y-4" aria-hidden="true">
        <BaseSkeleton class="w-1/3" />
        <BaseSkeleton variant="card" class="!h-10" />
        <BaseSkeleton variant="card" class="!h-10" />
        <BaseSkeleton variant="card" class="!h-10" />
      </div>
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-6" aria-hidden="true">
        <BaseSkeleton variant="card" class="!h-96" />
      </div>
    </div>

    <BaseAlert v-else-if="loadError" variant="danger" title="No se pudo cargar el documento">
      <p>Verifica tu conexión e inténtalo de nuevo.</p>
      <div class="mt-3 flex items-center gap-4">
        <BaseButton variant="secondary" size="sm" @click="reloadDocument">Reintentar</BaseButton>
        <NuxtLink
          :to="localePath('/panel/documents')"
          class="text-sm text-text-brand hover:underline"
        >
          ← Volver a la lista
        </NuxtLink>
      </div>
    </BaseAlert>

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
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
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
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Estado</label>
              <select
                v-model="form.status"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
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
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
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
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              >
                <option value="es">Español</option>
                <option value="en">English</option>
              </select>
            </div>
            <div class="space-y-1">
              <div
                v-for="option in coverOptions"
                :key="option.key"
                class="flex items-center gap-3 py-1.5 px-1 select-none"
              >
                <BaseToggle v-model="form[option.key]" :aria-label="option.label" />
                <span class="text-sm font-medium text-text-default">{{ option.label }}</span>
              </div>
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
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
              :class="copiedMarkdown
                ? 'bg-primary-soft text-text-brand hover:bg-primary-soft'
                : 'bg-surface-raised text-text-muted hover:bg-surface-raised'"
              :disabled="!form.content_markdown.trim()"
              @click="handleCopyContent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              {{ copiedMarkdown ? 'Copiado' : 'Copiar' }}
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
              :class="pastedMarkdown
                ? 'bg-primary-soft text-text-brand hover:bg-primary-soft'
                : 'bg-surface-raised text-text-muted hover:bg-surface-raised'"
              @click="handlePasteContent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              {{ pastedMarkdown ? 'Pegado' : 'Pegar' }}
            </button>
            <BaseSegmented
              v-model="form.template_style"
              size="sm"
              :options="templateStyleOptions"
              aria-label="Estilo de plantilla"
            />
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
            ref="markdownTextareaRef"
            v-model="form.content_markdown"
            placeholder="# Contenido del documento..."
            class="w-full px-4 py-3 border border-border-default rounded-xl text-sm font-mono leading-relaxed bg-surface text-text-default placeholder:text-text-subtle
                   focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-none
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
            <DocumentMarkdownBody
              v-if="form.content_markdown.trim()"
              :markdown="form.content_markdown"
              :theme="form.template_style"
              class="px-5 py-4"
            />
            <div
              v-else
              class="flex items-center justify-center h-64 text-sm text-text-subtle"
            >
              Escribe markdown para ver la vista previa...
            </div>
          </div>
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-3 lg:hidden">
          <button
            type="submit"
            :disabled="documentStore.isUpdating || !hasChanges"
            class="px-5 sm:px-6 py-2.5 bg-primary text-white rounded-xl font-medium text-sm
                   hover:bg-primary transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ documentStore.isUpdating ? 'Guardando...' : 'Guardar' }}
          </button>
          <BaseDropdown :items="downloadItems" align="right">
            <template #trigger>
              <button
                type="button"
                :disabled="isDownloading"
                class="px-5 sm:px-6 py-2.5 bg-surface text-text-default border border-border-default rounded-xl font-medium text-sm
                       hover:bg-surface-raised transition-colors disabled:opacity-50 inline-flex items-center gap-1.5"
              >
                {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </template>
          </BaseDropdown>
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
      <DocumentMarkdownBody
        v-if="form.content_markdown.trim()"
        :markdown="form.content_markdown"
        variant="full"
        :theme="form.template_style"
        class="max-w-4xl mx-auto"
      />
      <div v-else class="flex items-center justify-center h-full text-sm text-text-subtle">
        No hay contenido para mostrar.
      </div>
    </MarkdownPreviewModal>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, nextTick } from 'vue';
import TagSelector from '~/components/panel/documents/TagSelector.vue';
import MarkdownPreviewModal from '~/components/panel/documents/MarkdownPreviewModal.vue';
import DocumentMarkdownBody from '~/components/panel/documents/DocumentMarkdownBody.vue';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { usePanelNotify } from '~/composables/usePanelNotify';

const localePath = useLocalePath();
const route = useRoute();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const tagStore = useDocumentTagStore();
const notify = usePanelNotify();
const loadError = ref(false);
const isDownloading = ref(false);
const showPreview = ref(true);
const showFullPreview = ref(false);
const copiedMarkdown = ref(false);
const pastedMarkdown = ref(false);
const markdownTextareaRef = ref(null);

const savedForm = ref(null);
const hasChanges = computed(() => {
  if (!savedForm.value) return false;
  return JSON.stringify({ ...form, tag_ids: [...form.tag_ids] }) !== JSON.stringify(savedForm.value);
});

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
  template_style: 'professional',
});

const coverOptions = [
  { key: 'include_portada', label: 'Incluir portada' },
  { key: 'include_subportada', label: 'Incluir subportada' },
  { key: 'include_contraportada', label: 'Incluir contraportada' },
];

const templateStyleOptions = [
  { value: 'friendly', label: 'Amigable', testId: 'doc-style-friendly' },
  { value: 'professional', label: 'Profesional', testId: 'doc-style-professional' },
];

const statusOptions = [
  { value: 'draft', label: 'Borrador' },
  { value: 'published', label: 'Publicado' },
  { value: 'archived', label: 'Archivado' },
];

const statusLabel = computed(
  () => statusOptions.find((option) => option.value === form.status)?.label || '',
);

async function handleCopyContent() {
  try {
    await navigator.clipboard.writeText(form.content_markdown);
    copiedMarkdown.value = true;
    setTimeout(() => { copiedMarkdown.value = false; }, 2000);
  } catch {
    notify.error({
      title: 'No se pudo copiar al portapapeles',
      detail: 'Tu navegador bloqueó el acceso al portapapeles.',
    });
  }
}

async function handlePasteContent() {
  try {
    const pasted = await navigator.clipboard.readText();
    if (!pasted) return;
    const textarea = markdownTextareaRef.value;
    const start = textarea ? textarea.selectionStart : form.content_markdown.length;
    const end = textarea ? textarea.selectionEnd : form.content_markdown.length;
    form.content_markdown = form.content_markdown.slice(0, start) + pasted + form.content_markdown.slice(end);
    const cursor = start + pasted.length;
    if (textarea) {
      nextTick(() => {
        textarea.focus();
        textarea.setSelectionRange(cursor, cursor);
      });
    }
    pastedMarkdown.value = true;
    setTimeout(() => { pastedMarkdown.value = false; }, 2000);
  } catch {
    notify.error({
      title: 'No se pudo pegar desde el portapapeles',
      detail: 'Tu navegador bloqueó el acceso al portapapeles.',
    });
  }
}

async function reloadDocument() {
  const id = route.params.id;
  loadError.value = false;
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
    form.template_style = result.data.template_style || 'professional';
    savedForm.value = { ...form, tag_ids: [...form.tag_ids] };
  } else {
    loadError.value = true;
  }
}

onMounted(reloadDocument);
usePanelRefresh(reloadDocument);

async function handleSave() {
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
    template_style: form.template_style,
  };

  const result = await documentStore.updateDocument(route.params.id, payload);
  if (result.success) {
    savedForm.value = { ...form, tag_ids: [...form.tag_ids] };
    notify.success({ title: 'Documento guardado' });
  } else {
    const fieldDetail = result.fieldErrors
      ? Object.entries(result.fieldErrors).map(([k, v]) => `${k}: ${v}`).join(' · ')
      : '';
    notify.error({
      title: 'No se pudo guardar el documento',
      detail: fieldDetail || result.message,
    });
  }
}

const downloadItems = computed(() => [
  { label: 'Descargar · Amigable', onClick: () => handleDownloadPdf('friendly') },
  { label: 'Descargar · Profesional', onClick: () => handleDownloadPdf('professional') },
]);

async function handleDownloadPdf(template = null) {
  isDownloading.value = true;
  const result = await documentStore.downloadPdf(
    route.params.id, form.title || 'document', template);
  isDownloading.value = false;
  if (!result.success) {
    notify.error({ title: 'No se pudo descargar el PDF', detail: result.message });
  }
}
</script>

