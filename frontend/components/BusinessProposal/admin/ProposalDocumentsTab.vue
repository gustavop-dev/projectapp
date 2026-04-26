<template>
  <div class="space-y-8">
    <!-- ── Documentos (lista unificada) ── -->
    <section class="bg-white dark:bg-esmerald border border-gray-100 dark:border-white/[0.06] rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Documentos</h3>
      </div>

      <ul class="divide-y divide-gray-100 dark:divide-white/[0.06]">
        <!-- Contrato de desarrollo -->
        <li class="py-3 flex items-start justify-between gap-3 flex-wrap">
          <div class="min-w-0">
            <div class="text-sm font-medium text-gray-800 dark:text-white">Contrato de desarrollo</div>
            <div class="text-xs text-gray-400 dark:text-green-light/40 mt-0.5">
              <template v-if="contractDoc">PDF · Generado el {{ formatDate(contractDoc.created_at) }}</template>
              <template v-else>PDF · No generado</template>
            </div>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <template v-if="contractDoc">
              <button type="button" aria-label="Vista previa" title="Vista previa"
                @click="openPdfPreview('Contrato de desarrollo', contractPdfUrl)"
                class="inline-flex items-center justify-center w-8 h-8 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-green-light rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors">
                <EyeIcon class="w-4 h-4" />
              </button>
              <a :href="contractPdfUrl" target="_blank"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors">
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
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-green-light rounded-lg text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                Editar parámetros
              </button>
            </template>
            <button v-else type="button" :disabled="contractActionsDisabled" @click="$emit('generateContract')"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              Generar contrato
            </button>
          </div>
        </li>

        <!-- Propuesta comercial -->
        <li class="py-3 flex items-start justify-between gap-3 flex-wrap">
          <div class="min-w-0">
            <div class="text-sm font-medium text-gray-800 dark:text-white">Propuesta comercial</div>
            <div class="text-xs text-gray-400 dark:text-green-light/40 mt-0.5">PDF con branding</div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" aria-label="Vista previa" title="Vista previa"
              @click="openPdfPreview('Propuesta comercial', commercialPdfUrl)"
              class="inline-flex items-center justify-center w-8 h-8 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-green-light rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors">
              <EyeIcon class="w-4 h-4" />
            </button>
            <a :href="commercialPdfUrl" target="_blank"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors">
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
            <div class="text-sm font-medium text-gray-800 dark:text-white">Detalle técnico</div>
            <div class="text-xs text-gray-400 dark:text-green-light/40 mt-0.5">PDF con branding</div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" aria-label="Vista previa" title="Vista previa"
              @click="openPdfPreview('Detalle técnico', technicalPdfUrl)"
              class="inline-flex items-center justify-center w-8 h-8 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-green-light rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors">
              <EyeIcon class="w-4 h-4" />
            </button>
            <a :href="technicalPdfUrl" target="_blank"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors">
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
    <section class="bg-white dark:bg-esmerald border border-gray-100 dark:border-white/[0.06] rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Documentos adjuntos</h3>
      </div>

      <div v-if="additionalDocs.length" class="space-y-2 mb-4">
        <div v-for="doc in additionalDocs" :key="doc.id"
          class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-white/[0.03] rounded-lg">
          <div class="flex items-center gap-2 min-w-0">
            <span class="px-2 py-0.5 bg-gray-200 dark:bg-white/[0.08] text-gray-600 dark:text-green-light/60 rounded text-[10px] font-medium">
              {{ doc.document_type_display }}
            </span>
            <a :href="doc.file" target="_blank" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium truncate">
              {{ doc.title }}
            </a>
          </div>
          <div class="flex items-center gap-1">
            <button v-if="canPreviewFile(doc.file)" type="button" aria-label="Vista previa"
              title="Vista previa" @click="openDocPreview(doc)"
              class="text-gray-400 hover:text-emerald-600 transition-colors p-1">
              <EyeIcon class="w-4 h-4" />
            </button>
            <button v-if="!doc.is_generated" type="button" @click="handleDelete(doc.id)"
              class="text-gray-400 hover:text-red-500 transition-colors p-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      <p v-else class="text-xs text-gray-400 dark:text-green-light/40 mb-4">No hay documentos adjuntos.</p>

      <!-- Upload form -->
      <div class="border-t border-gray-100 dark:border-white/[0.06] pt-4">
        <p class="text-xs text-gray-500 dark:text-green-light/60 mb-3">Subir documento (otrosí, anexo, documento del cliente, etc.)</p>
        <div class="flex flex-wrap items-end gap-3">
          <div class="flex-1 min-w-[150px]">
            <label class="block text-xs text-gray-400 dark:text-green-light/40 mb-1">Título</label>
            <input v-model="uploadTitle" type="text" placeholder="Ej: Anexo técnico"
              class="w-full px-3 py-2 border border-gray-200 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-emerald-500" />
          </div>
          <div class="w-36">
            <label class="block text-xs text-gray-400 dark:text-green-light/40 mb-1">Tipo</label>
            <select v-model="uploadType"
              class="w-full px-3 py-2 border border-gray-200 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-emerald-500">
              <option value="amendment">Otrosí</option>
              <option value="legal_annex">Anexo legal</option>
              <option value="client_document">Doc. del cliente</option>
              <option value="other">Otro</option>
            </select>
          </div>
          <div v-if="uploadType === 'other'" class="min-w-[120px]">
            <label class="block text-xs text-gray-400 dark:text-green-light/40 mb-1">Nombre categoría</label>
            <input v-model="uploadCustomLabel" type="text" placeholder="Ej: Diseños"
              class="w-full px-3 py-2 border border-gray-200 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white rounded-lg text-xs focus:ring-2 focus:ring-emerald-500" />
          </div>
          <div>
            <label class="block text-xs text-gray-400 dark:text-green-light/40 mb-1">Archivo</label>
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
              class="text-xs dark:text-white/70 file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-emerald-50 dark:file:bg-emerald-900/20 file:text-emerald-700 dark:file:text-emerald-400 file:rounded-lg hover:file:bg-emerald-100 dark:hover:file:bg-emerald-900/30" />
          </div>
          <button type="button" :disabled="isUploading" @click="handleUpload"
            class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50">
            {{ isUploading ? 'Subiendo...' : 'Subir' }}
          </button>
        </div>
      </div>
    </section>

    <MarkdownPreviewModal v-model="previewOpen" :title="previewTitle">
      <iframe v-if="previewKind === 'pdf'" :src="previewUrl"
        class="w-full h-[80vh] border-0 rounded-lg bg-white" title="Vista previa"></iframe>
      <img v-else-if="previewKind === 'image'" :src="previewUrl"
        class="max-w-full mx-auto" :alt="previewTitle" />
    </MarkdownPreviewModal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
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

function openPdfPreview(title, url) {
  previewKind.value = 'pdf';
  previewTitle.value = title || 'Vista previa';
  previewUrl.value = url;
  previewOpen.value = true;
}

function openDocPreview(doc) {
  const file = doc?.file || '';
  if (isPdfUrl(file)) {
    openPdfPreview(doc.title || 'Vista previa', file);
  } else if (isImageUrl(file)) {
    previewKind.value = 'image';
    previewTitle.value = doc.title || 'Vista previa';
    previewUrl.value = file;
    previewOpen.value = true;
  }
}

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
