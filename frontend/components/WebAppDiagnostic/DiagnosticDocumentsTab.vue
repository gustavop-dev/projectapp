<template>
  <div class="space-y-8">
    <!-- ── Documentos (lista unificada: NDA + plantillas) ── -->
    <section class="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Documentos</h3>
      </div>

      <ul class="divide-y divide-gray-100 dark:divide-white/[0.06]">
        <!-- Acuerdo de confidencialidad -->
        <li class="py-3">
          <div class="flex items-start justify-between gap-3 flex-wrap">
            <div class="min-w-0">
              <div class="text-sm font-medium text-gray-800 dark:text-white">Acuerdo de confidencialidad</div>
              <div class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                <template v-if="ndaDoc">PDF · Generado el {{ formatDate(ndaDoc.created_at) }}</template>
                <template v-else>PDF · No generado</template>
              </div>
            </div>
            <div class="flex items-center gap-2 flex-wrap">
              <template v-if="ndaDoc">
                <button type="button" aria-label="Vista previa" title="Vista previa"
                  @click="openPdfPreview('Acuerdo de confidencialidad', ndaPdfUrl)"
                  class="inline-flex items-center justify-center w-8 h-8 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-white/70 rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors">
                  <EyeIcon class="w-4 h-4" />
                </button>
                <a :href="ndaPdfUrl" target="_blank"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Descargar PDF
                </a>
                <a :href="ndaDraftPdfUrl" target="_blank"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 rounded-lg text-xs font-medium hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors">
                  Borrador
                </a>
                <button type="button" @click="showParamsModal = true"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-white/70 rounded-lg text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors">
                  Editar parámetros
                </button>
              </template>
              <button v-else type="button" @click="showParamsModal = true"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors">
                Generar acuerdo
              </button>
            </div>
          </div>
        </li>

        <!-- Plantillas MD del diagnóstico -->
        <li v-if="templatesLoading" class="py-3 text-xs text-gray-400 dark:text-gray-500">Cargando plantillas…</li>
        <li v-else-if="templatesError" class="py-3 text-xs text-red-500">{{ templatesError }}</li>
        <template v-else>
          <li v-for="t in templates" :key="t.slug" class="py-3">
            <div class="flex items-start justify-between gap-3 flex-wrap">
              <div class="min-w-0">
                <div class="text-sm font-medium text-gray-800 dark:text-white">{{ t.title }}</div>
                <div class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                  {{ t.filename }} · {{ formatBytes(t.size_bytes) }}
                </div>
              </div>
              <div class="flex items-center gap-2 flex-wrap">
                <button type="button" :disabled="templateBusy[t.slug]" @click="copyTemplate(t.slug)"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors disabled:opacity-50">
                  {{ templateCopied[t.slug] ? '¡Copiado!' : 'Copiar contenido' }}
                </button>
                <button type="button" :disabled="templateBusy[t.slug]" @click="downloadTemplate(t.slug, t.filename)"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-green-light rounded-lg text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors disabled:opacity-50">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Descargar .md
                </button>
                <button type="button" :disabled="templateBusy[t.slug]" aria-label="Vista previa"
                  title="Vista previa" @click="openMarkdownPreview(t)"
                  class="inline-flex items-center justify-center w-8 h-8 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-green-light rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors disabled:opacity-50">
                  <EyeIcon class="w-4 h-4" />
                </button>
              </div>
            </div>
          </li>
        </template>
      </ul>
    </section>

    <!-- ── Documentos adjuntos ── -->
    <section class="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Documentos adjuntos</h3>
      </div>

      <div v-if="userAttachments.length" class="space-y-2 mb-4">
        <div v-for="att in userAttachments" :key="att.id"
          class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-white/[0.03] rounded-lg">
          <div class="flex items-center gap-2 min-w-0">
            <span class="px-2 py-0.5 bg-gray-200 dark:bg-white/[0.08] text-gray-600 dark:text-gray-400 rounded text-[10px] font-medium">
              {{ att.document_type_display }}
            </span>
            <a :href="att.file" target="_blank" rel="noopener noreferrer"
              class="text-xs text-emerald-600 hover:text-emerald-700 font-medium truncate">
              {{ att.title }}
            </a>
          </div>
          <div class="flex items-center gap-1">
            <button v-if="canPreviewFile(att.file)" type="button" aria-label="Vista previa"
              title="Vista previa" @click="openAttachmentPreview(att)"
              class="text-gray-400 hover:text-emerald-600 transition-colors p-1">
              <EyeIcon class="w-4 h-4" />
            </button>
            <button type="button" class="text-gray-400 hover:text-red-500 transition-colors p-1"
              @click="handleDelete(att.id)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      <p v-else class="text-xs text-gray-400 dark:text-gray-500 mb-4">
        No hay documentos adjuntos.
      </p>

      <!-- Upload form -->
      <div class="border-t border-gray-100 dark:border-gray-700 pt-4">
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
          Subir documento (otrosí, anexo, documento del cliente, etc.)
        </p>
        <div class="flex flex-wrap items-end gap-3">
          <div class="flex-1 min-w-[150px]">
            <label class="block text-xs text-gray-400 dark:text-gray-500 mb-1">Título</label>
            <input v-model="uploadTitle" type="text" placeholder="Ej: Anexo técnico"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-emerald-500" />
          </div>
          <div class="w-36">
            <label class="block text-xs text-gray-400 dark:text-gray-500 mb-1">Tipo</label>
            <select v-model="uploadType"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-emerald-500">
              <option value="amendment">Otrosí</option>
              <option value="legal_annex">Anexo legal</option>
              <option value="client_document">Doc. del cliente</option>
              <option value="other">Otro</option>
            </select>
          </div>
          <div v-if="uploadType === 'other'" class="min-w-[120px]">
            <label class="block text-xs text-gray-400 dark:text-gray-500 mb-1">Nombre categoría</label>
            <input v-model="uploadCustomLabel" type="text" placeholder="Ej: Diseños"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-emerald-500" />
          </div>
          <div>
            <label class="block text-xs text-gray-400 dark:text-gray-500 mb-1">Archivo</label>
            <input ref="fileInput" type="file"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
              class="text-xs dark:text-white/70 file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-emerald-50 dark:file:bg-emerald-900/20 file:text-emerald-700 dark:file:text-emerald-400 file:rounded-lg hover:file:bg-emerald-100 dark:hover:file:bg-emerald-900/30" />
          </div>
          <button type="button" :disabled="isUploading" @click="handleUpload"
            class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50">
            {{ isUploading ? 'Subiendo...' : 'Subir' }}
          </button>
        </div>
        <p v-if="uploadError" class="text-xs text-red-500 mt-2">{{ uploadError }}</p>
      </div>
    </section>

    <ConfidentialityParamsModal
      :visible="showParamsModal"
      :diagnostic="diagnostic"
      @cancel="showParamsModal = false"
      @saved="showParamsModal = false" />

    <MarkdownPreviewModal v-model="previewOpen" :title="previewTitle">
      <div v-if="previewKind === 'markdown'"
        class="markdown-preview markdown-preview--full max-w-4xl mx-auto"
        v-html="previewHtml"></div>
      <iframe v-else-if="previewKind === 'pdf'" :src="previewUrl"
        class="w-full h-[80vh] border-0 rounded-lg bg-white" title="Vista previa"></iframe>
      <img v-else-if="previewKind === 'image'" :src="previewUrl"
        class="max-w-full mx-auto" :alt="previewTitle" />
    </MarkdownPreviewModal>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue';
import { EyeIcon } from '@heroicons/vue/24/outline';
import ConfidentialityParamsModal from '~/components/WebAppDiagnostic/ConfidentialityParamsModal.vue';
import MarkdownPreviewModal from '~/components/panel/documents/MarkdownPreviewModal.vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { useMarkdownPreview } from '~/composables/useMarkdownPreview';
import { get_request } from '~/stores/services/request_http';
import { canPreviewFile, isPdfUrl, isImageUrl } from '~/utils/filePreview';

const { parseMarkdown } = useMarkdownPreview();

const props = defineProps({
  diagnostic: { type: Object, required: true },
});

const store = useDiagnosticsStore();

const DOC_TYPE_CONFIDENTIALITY = 'confidentiality_agreement';

const attachments = computed(() => props.diagnostic.attachments || []);
const ndaDoc = computed(() =>
  attachments.value.find(
    (a) => a.document_type === DOC_TYPE_CONFIDENTIALITY && a.is_generated,
  ) || null,
);
const userAttachments = computed(() =>
  attachments.value.filter((a) => !(a.is_generated && a.document_type === DOC_TYPE_CONFIDENTIALITY)),
);

const ndaPdfUrl = computed(() => `/api/diagnostics/${props.diagnostic.id}/confidentiality/pdf/`);
const ndaDraftPdfUrl = computed(() => `/api/diagnostics/${props.diagnostic.id}/confidentiality/draft-pdf/`);

const showParamsModal = ref(false);

const templates = ref([]);
const templatesLoading = ref(true);
const templatesError = ref('');
const templateCache = reactive({});
const templateCopied = reactive({});
const templateBusy = reactive({});

const previewOpen = ref(false);
const previewKind = ref('markdown');
const previewTitle = ref('Vista previa');
const previewMarkdown = ref('');
const previewUrl = ref('');
const previewHtml = computed(() => parseMarkdown(previewMarkdown.value || ''));

async function openMarkdownPreview(template) {
  const content = await ensureTemplateContent(template.slug);
  previewKind.value = 'markdown';
  previewTitle.value = template.title || 'Vista previa';
  previewMarkdown.value = content || '';
  previewUrl.value = '';
  previewOpen.value = true;
}

function openPdfPreview(title, url) {
  previewKind.value = 'pdf';
  previewTitle.value = title || 'Vista previa';
  previewUrl.value = url;
  previewMarkdown.value = '';
  previewOpen.value = true;
}

function openAttachmentPreview(att) {
  const file = att?.file || '';
  if (isPdfUrl(file)) {
    openPdfPreview(att.title || 'Vista previa', file);
  } else if (isImageUrl(file)) {
    previewKind.value = 'image';
    previewTitle.value = att.title || 'Vista previa';
    previewUrl.value = file;
    previewMarkdown.value = '';
    previewOpen.value = true;
  }
}

onMounted(async () => {
  try {
    const res = await get_request('diagnostic-templates/');
    templates.value = res.data || [];
  } catch (e) {
    templatesError.value = 'No se pudieron cargar las plantillas.';
  } finally {
    templatesLoading.value = false;
  }
});

async function ensureTemplateContent(slug) {
  if (templateCache[slug]) return templateCache[slug];
  templateBusy[slug] = true;
  try {
    const diagnosticId = props.diagnostic?.id;
    const url = diagnosticId
      ? `diagnostic-templates/${slug}/?diagnostic_id=${diagnosticId}`
      : `diagnostic-templates/${slug}/`;
    const res = await get_request(url);
    templateCache[slug] = res.data?.content_markdown || '';
    return templateCache[slug];
  } finally {
    templateBusy[slug] = false;
  }
}

async function copyTemplate(slug) {
  const content = await ensureTemplateContent(slug);
  await navigator.clipboard.writeText(content);
  templateCopied[slug] = true;
  setTimeout(() => { templateCopied[slug] = false; }, 2000);
}

async function downloadTemplate(slug, filename) {
  const content = await ensureTemplateContent(slug);
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(value) {
  if (!value) return '';
  try {
    return new Date(value).toLocaleString('es-CO', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch (e) {
    return value;
  }
}

// ── Uploader ──
const isUploading = ref(false);
const uploadTitle = ref('');
const uploadType = ref('other');
const uploadCustomLabel = ref('');
const uploadError = ref('');
const fileInput = ref(null);

async function handleUpload() {
  const file = fileInput.value?.files?.[0];
  if (!file) {
    uploadError.value = 'Selecciona un archivo.';
    return;
  }
  uploadError.value = '';
  isUploading.value = true;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', uploadTitle.value || file.name);
  formData.append('document_type', uploadType.value);
  if (uploadType.value === 'other' && uploadCustomLabel.value) {
    formData.append('custom_type_label', uploadCustomLabel.value);
  }
  const result = await store.uploadAttachment(props.diagnostic.id, formData);
  if (result.success) {
    uploadTitle.value = '';
    uploadCustomLabel.value = '';
    if (fileInput.value) fileInput.value.value = '';
  } else {
    uploadError.value = result.error || 'Error al subir.';
  }
  isUploading.value = false;
}

async function handleDelete(attachmentId) {
  const result = await store.deleteAttachment(props.diagnostic.id, attachmentId);
  if (!result.success) {
    uploadError.value = result.error || 'No se pudo eliminar el documento.';
  }
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
