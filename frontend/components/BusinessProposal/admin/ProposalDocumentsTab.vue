<template>
  <div class="space-y-8">
    <!-- ── Documentos (lista unificada) ── -->
    <section class="bg-surface border border-border-muted rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default dark:text-white">Documentos</h3>
      </div>

      <ul class="divide-y divide-gray-100 dark:divide-white/[0.06]">
        <!-- Contrato de desarrollo -->
        <li class="py-3 flex items-start justify-between gap-3 flex-wrap">
          <div class="min-w-0">
            <div class="text-sm font-medium text-text-default dark:text-white">Contrato de desarrollo</div>
            <div class="text-xs text-text-subtle dark:text-text-subtle mt-0.5">
              <template v-if="contractDoc">PDF · Generado el {{ formatDate(contractDoc.created_at) }}</template>
              <template v-else>PDF · No generado</template>
            </div>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <template v-if="contractDoc">
              <button type="button" aria-label="Vista previa" title="Vista previa"
                @click="openPdfPreview('Contrato de desarrollo', contractPdfUrl)"
                class="inline-flex items-center justify-center w-8 h-8 bg-surface-raised text-text-muted rounded-lg hover:bg-surface-raised transition-colors">
                <EyeIcon class="w-4 h-4" />
              </button>
              <a :href="contractPdfUrl" target="_blank"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-soft text-text-brand rounded-lg text-xs font-medium hover:bg-primary-soft transition-colors">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Descargar PDF
              </a>
              <a :href="draftContractPdfUrl" target="_blank"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 rounded-lg text-xs font-medium hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors">
                Borrador
              </a>
              <button type="button" :disabled="contractActionsDisabled" @click="$emit('editContract')"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-surface-raised text-text-muted rounded-lg text-xs font-medium hover:bg-surface-raised transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                Editar parámetros
              </button>
            </template>
            <button v-else type="button" :disabled="contractActionsDisabled" @click="$emit('generateContract')"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-soft text-text-brand rounded-lg text-xs font-medium hover:bg-primary-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              Generar contrato
            </button>
          </div>
        </li>

        <!-- Propuesta comercial -->
        <li class="py-3 flex items-start justify-between gap-3 flex-wrap">
          <div class="min-w-0">
            <div class="text-sm font-medium text-text-default dark:text-white">Propuesta comercial</div>
            <div class="text-xs text-text-subtle dark:text-text-subtle mt-0.5">PDF con branding</div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" aria-label="Vista previa" title="Vista previa"
              @click="openPdfPreview('Propuesta comercial', commercialPdfUrl)"
              class="inline-flex items-center justify-center w-8 h-8 bg-surface-raised text-text-muted rounded-lg hover:bg-surface-raised transition-colors">
              <EyeIcon class="w-4 h-4" />
            </button>
            <a :href="commercialPdfUrl" target="_blank"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-soft text-text-brand rounded-lg text-xs font-medium hover:bg-primary-soft transition-colors">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Descargar PDF
            </a>
          </div>
        </li>

        <!-- Detalle técnico -->
        <li class="py-3 flex items-start justify-between gap-3 flex-wrap">
          <div class="min-w-0">
            <div class="text-sm font-medium text-text-default dark:text-white">Detalle técnico</div>
            <div class="text-xs text-text-subtle dark:text-text-subtle mt-0.5">PDF con branding</div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" aria-label="Vista previa" title="Vista previa"
              @click="openPdfPreview('Detalle técnico', technicalPdfUrl)"
              class="inline-flex items-center justify-center w-8 h-8 bg-surface-raised text-text-muted rounded-lg hover:bg-surface-raised transition-colors">
              <EyeIcon class="w-4 h-4" />
            </button>
            <a :href="technicalPdfUrl" target="_blank"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-soft text-text-brand rounded-lg text-xs font-medium hover:bg-primary-soft transition-colors">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Descargar PDF
            </a>
          </div>
        </li>
      </ul>
    </section>

    <!-- ── Documentos adjuntos ── -->
    <section class="bg-surface border border-border-muted rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default dark:text-white">Documentos adjuntos</h3>
      </div>

      <div v-if="additionalDocs.length" class="space-y-2 mb-4">
        <div v-for="doc in additionalDocs" :key="doc.id"
          class="flex items-center justify-between py-2 px-3 bg-surface-raised rounded-lg">
          <div class="flex items-center gap-2 min-w-0">
            <span class="px-2 py-0.5 bg-surface-raised text-text-muted/60 rounded text-[10px] font-medium">
              {{ doc.document_type_display }}
            </span>
            <a :href="doc.file" target="_blank" class="text-xs text-text-brand hover:text-text-brand font-medium truncate">
              {{ doc.title }}
            </a>
          </div>
          <div class="flex items-center gap-1">
            <button v-if="canPreviewFile(doc.file)" type="button" aria-label="Vista previa"
              title="Vista previa" @click="openDocPreview(doc)"
              class="text-text-subtle hover:text-text-brand transition-colors p-1">
              <EyeIcon class="w-4 h-4" />
            </button>
            <button v-if="!doc.is_generated" type="button" @click="handleDelete(doc.id)"
              class="text-text-subtle hover:text-red-500 transition-colors p-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      <p v-else class="text-xs text-text-subtle dark:text-text-subtle mb-4">No hay documentos adjuntos.</p>

      <!-- Upload form -->
      <div class="border-t border-border-muted pt-4">
        <p class="text-xs text-text-muted mb-3">Subir documento (otrosí, anexo, documento del cliente, etc.)</p>
        <div class="flex flex-wrap items-end gap-3">
          <div class="flex-1 min-w-[150px]">
            <label class="block text-xs text-text-subtle dark:text-text-subtle mb-1">Título</label>
            <input v-model="uploadTitle" type="text" placeholder="Ej: Anexo técnico"
              class="w-full px-3 py-2 border border-border-default dark:bg-primary-strong dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-focus-ring/30" />
          </div>
          <div class="w-36">
            <label class="block text-xs text-text-subtle dark:text-text-subtle mb-1">Tipo</label>
            <select v-model="uploadType"
              class="w-full px-3 py-2 border border-border-default dark:bg-primary-strong dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-focus-ring/30">
              <option value="amendment">Otrosí</option>
              <option value="legal_annex">Anexo legal</option>
              <option value="client_document">Doc. del cliente</option>
              <option value="other">Otro</option>
            </select>
          </div>
          <div v-if="uploadType === 'other'" class="min-w-[120px]">
            <label class="block text-xs text-text-subtle dark:text-text-subtle mb-1">Nombre categoría</label>
            <input v-model="uploadCustomLabel" type="text" placeholder="Ej: Diseños"
              class="w-full px-3 py-2 border border-border-default dark:bg-primary-strong dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-focus-ring/30" />
          </div>
          <div>
            <label class="block text-xs text-text-subtle dark:text-text-subtle mb-1">Archivo</label>
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
              class="text-xs dark:text-white/70 file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-primary-soft file:text-text-brand file:rounded-lg hover:file:bg-primary-soft" />
          </div>
          <button type="button" :disabled="isUploading" @click="handleUpload"
            class="px-4 py-2 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary-strong transition-colors disabled:opacity-50">
            {{ isUploading ? 'Subiendo...' : 'Subir' }}
          </button>
        </div>
      </div>
    </section>

    <MarkdownPreviewModal v-model="previewOpen" :title="previewTitle">
      <div v-if="previewLoading"
        class="flex items-center justify-center h-[60vh] text-sm text-text-muted">
        Cargando vista previa…
      </div>
      <div v-else-if="previewError"
        class="flex items-center justify-center h-[60vh] text-sm text-red-500">
        {{ previewError }}
      </div>
      <iframe v-else-if="previewKind === 'pdf' && previewUrl" :src="previewUrl"
        class="w-full h-[80vh] border-0 rounded-lg bg-surface" title="Vista previa"></iframe>
      <img v-else-if="previewKind === 'image' && previewUrl" :src="previewUrl"
        class="max-w-full mx-auto" :alt="previewTitle" />
    </MarkdownPreviewModal>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import { EyeIcon } from '@heroicons/vue/24/outline';
import { usePanelToast } from '~/composables/usePanelToast';
import { CONTRACT_LOCKED_STATUSES } from '~/utils/proposalStatus';
import { isPdfUrl, isImageUrl, canPreviewFile } from '~/utils/filePreview';
import MarkdownPreviewModal from '~/components/panel/documents/MarkdownPreviewModal.vue';

const { showToast } = usePanelToast();

const props = defineProps({
  proposal: { type: Object, required: true },
  documents: { type: Array, default: () => [] },
});

const emit = defineEmits(['refresh', 'editContract', 'generateContract']);

const proposalStore = useProposalStore();
const isUploading = ref(false);
const uploadTitle = ref('');
const uploadType = ref('other');
const uploadCustomLabel = ref('');
const fileInput = ref(null);

const contractDoc = computed(() =>
  props.documents.find(d => d.document_type === 'contract'),
);

const contractActionsDisabled = computed(() =>
  CONTRACT_LOCKED_STATUSES.includes(props.proposal?.status),
);

const contractPdfUrl = computed(() =>
  `/api/proposals/${props.proposal.id}/contract/pdf/`,
);
const draftContractPdfUrl = computed(() =>
  `/api/proposals/${props.proposal.id}/contract/draft-pdf/`,
);
const commercialPdfUrl = computed(() =>
  `/api/proposals/${props.proposal.uuid}/pdf/`,
);
const technicalPdfUrl = computed(() =>
  `/api/proposals/${props.proposal.uuid}/pdf/?doc=technical`,
);

const additionalDocs = computed(() =>
  props.documents.filter(d => d.document_type !== 'contract'),
);

const previewOpen = ref(false);
const previewKind = ref('pdf');
const previewTitle = ref('Vista previa');
const previewUrl = ref('');
const previewLoading = ref(false);
const previewError = ref('');
let previewRequestId = 0;
let previewAbortController = null;

function releasePreviewObjectUrl() {
  if (previewUrl.value && typeof URL !== 'undefined') {
    URL.revokeObjectURL(previewUrl.value);
  }
  previewUrl.value = '';
}

function abortInflightPreview() {
  if (previewAbortController) {
    previewAbortController.abort();
    previewAbortController = null;
  }
}

async function loadPreviewBlob(kind, title, url) {
  abortInflightPreview();
  releasePreviewObjectUrl();
  previewKind.value = kind;
  previewTitle.value = title || 'Vista previa';
  previewError.value = '';
  previewLoading.value = true;
  previewOpen.value = true;

  const controller = new AbortController();
  previewAbortController = controller;
  const requestId = ++previewRequestId;
  try {
    const response = await fetch(url, { credentials: 'include', signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const blob = await response.blob();
    if (requestId !== previewRequestId || !previewOpen.value) return;
    previewUrl.value = URL.createObjectURL(blob);
  } catch (err) {
    if (requestId !== previewRequestId || err?.name === 'AbortError') return;
    previewError.value = 'No se pudo cargar la vista previa.';
    showToast({ type: 'error', text: 'No se pudo cargar la vista previa.' });
  } finally {
    if (requestId === previewRequestId) {
      previewLoading.value = false;
      previewAbortController = null;
    }
  }
}

function openPdfPreview(title, url) {
  loadPreviewBlob('pdf', title, url);
}

function openDocPreview(doc) {
  const file = doc?.file || '';
  if (isPdfUrl(file)) {
    loadPreviewBlob('pdf', doc?.title, file);
  } else if (isImageUrl(file)) {
    loadPreviewBlob('image', doc?.title, file);
  }
}

watch(previewOpen, (open) => {
  if (!open) {
    previewRequestId++;
    abortInflightPreview();
    releasePreviewObjectUrl();
    previewLoading.value = false;
    previewError.value = '';
  }
});

onBeforeUnmount(() => {
  abortInflightPreview();
  releasePreviewObjectUrl();
});

function formatDate(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'long', year: 'numeric',
  });
}

async function handleUpload() {
  const file = fileInput.value?.files?.[0];
  if (!file) return;

  isUploading.value = true;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', uploadTitle.value || file.name);
  formData.append('document_type', uploadType.value);
  if (uploadType.value === 'other' && uploadCustomLabel.value) {
    formData.append('custom_type_label', uploadCustomLabel.value);
  }

  const result = await proposalStore.uploadProposalDocument(props.proposal.id, formData);
  if (result.success) {
    uploadTitle.value = '';
    uploadCustomLabel.value = '';
    if (fileInput.value) fileInput.value.value = '';
    emit('refresh');
    showToast({ type: 'success', text: 'Documento subido.' });
  } else {
    showToast({ type: 'error', text: 'No se pudo subir el documento.' });
  }
  isUploading.value = false;
}

async function handleDelete(docId) {
  const result = await proposalStore.deleteProposalDocument(props.proposal.id, docId);
  if (result.success) {
    emit('refresh');
    showToast({ type: 'success', text: 'Documento eliminado.' });
  } else {
    showToast({ type: 'error', text: 'No se pudo eliminar el documento.' });
  }
}
</script>
