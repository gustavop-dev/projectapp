<template>
  <div class="space-y-8">
    <!-- Contract section -->
    <section class="bg-white border border-gray-100 rounded-xl p-5">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 class="text-sm font-semibold text-gray-800">Contrato de desarrollo</h3>
        </div>
        <div v-if="contractDoc" class="flex items-center gap-2">
          <a :href="contractPdfUrl" target="_blank"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-100 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Descargar
          </a>
          <a :href="draftContractPdfUrl" target="_blank"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-lg text-xs font-medium hover:bg-amber-100 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Borrador
          </a>
          <button type="button" @click="$emit('editContract')"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 text-gray-600 rounded-lg text-xs font-medium hover:bg-gray-100 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Editar parámetros
          </button>
        </div>
        <div v-else class="flex items-center gap-2">
          <span class="text-xs text-gray-400">No generado</span>
          <button type="button" @click="$emit('generateContract')"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-100 transition-colors">
            Generar contrato
          </button>
        </div>
      </div>
      <p v-if="contractDoc" class="text-xs text-gray-500">
        Generado el {{ formatDate(contractDoc.created_at) }}
      </p>
    </section>

    <!-- Proposal PDFs section -->
    <section class="bg-white border border-gray-100 rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800">PDFs de la propuesta</h3>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <a :href="'/api/proposals/' + proposal.uuid + '/pdf/'" target="_blank"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-100 transition-colors">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Propuesta comercial
        </a>
        <a :href="'/api/proposals/' + proposal.uuid + '/pdf/?doc=technical'" target="_blank"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-100 transition-colors">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Detalle técnico
        </a>
      </div>
    </section>

    <!-- Send documents to client section -->
    <section class="bg-white border border-emerald-100 rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800">Enviar documentos al cliente</h3>
      </div>

      <!-- Main documents checkboxes -->
      <div class="space-y-2 mb-4">
        <label class="flex items-center gap-2 cursor-pointer"
          :class="{ 'opacity-50 cursor-not-allowed': !contractDoc }">
          <input type="checkbox" value="draft_contract"
            v-model="selectedMainDocs"
            :disabled="!contractDoc"
            class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
          <span class="text-xs text-gray-700">Contrato de desarrollo (borrador)</span>
          <span v-if="!contractDoc" class="text-[10px] text-gray-400">(no generado)</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" value="commercial"
            v-model="selectedMainDocs"
            class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
          <span class="text-xs text-gray-700">Propuesta comercial</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" value="technical"
            v-model="selectedMainDocs"
            class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
          <span class="text-xs text-gray-700">Detalle técnico</span>
        </label>
      </div>

      <!-- Additional documents checkboxes -->
      <div v-if="additionalDocs.length" class="border-t border-gray-100 pt-3 mb-4">
        <p class="text-[10px] text-gray-400 uppercase tracking-wide mb-2">Documentos adicionales</p>
        <div class="space-y-2">
          <label v-for="doc in additionalDocs" :key="doc.id"
            class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" :value="doc.id"
              v-model="selectedAdditionalDocIds"
              class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
            <span class="px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded text-[10px] font-medium">
              {{ doc.document_type_display }}
            </span>
            <span class="text-xs text-gray-700">{{ doc.title }}</span>
          </label>
        </div>
      </div>

      <!-- Send button and client email -->
      <div class="flex items-center justify-between pt-2">
        <p v-if="proposal.client_email" class="text-xs text-gray-400">
          Se enviará a: <span class="font-medium text-gray-600">{{ proposal.client_email }}</span>
        </p>
        <p v-else class="text-xs text-red-400">No hay email del cliente configurado</p>
        <button type="button"
          :disabled="!hasSelectedDocs || !proposal.client_email"
          @click="showSendModal = true"
          class="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
          Enviar al cliente
        </button>
      </div>

      <!-- Success message -->
      <p v-if="sendSuccess" class="text-xs text-emerald-600 mt-2">
        Documentos enviados correctamente.
      </p>
    </section>

    <!-- Additional documents section -->
    <section class="bg-white border border-gray-100 rounded-xl p-5">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <h3 class="text-sm font-semibold text-gray-800">Documentos adicionales</h3>
        </div>
      </div>

      <!-- Existing documents list -->
      <div v-if="additionalDocs.length" class="space-y-2 mb-4">
        <div v-for="doc in additionalDocs" :key="doc.id"
          class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 bg-gray-200 text-gray-600 rounded text-[10px] font-medium">
              {{ doc.document_type_display }}
            </span>
            <a :href="doc.file" target="_blank" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium">
              {{ doc.title }}
            </a>
          </div>
          <button v-if="!doc.is_generated" type="button" @click="handleDelete(doc.id)"
            class="text-gray-400 hover:text-red-500 transition-colors p-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      <p v-else class="text-xs text-gray-400 mb-4">No hay documentos adicionales.</p>

      <!-- Upload form -->
      <div class="border-t border-gray-100 pt-4">
        <p class="text-xs text-gray-500 mb-3">Subir documento (otrosí, anexo, documento del cliente, etc.)</p>
        <div class="flex flex-wrap items-end gap-3">
          <div class="flex-1 min-w-[150px]">
            <label class="block text-xs text-gray-400 mb-1">Título</label>
            <input v-model="uploadTitle" type="text" placeholder="Ej: Anexo técnico"
              class="w-full px-3 py-2 border border-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-emerald-500" />
          </div>
          <div class="w-36">
            <label class="block text-xs text-gray-400 mb-1">Tipo</label>
            <select v-model="uploadType"
              class="w-full px-3 py-2 border border-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-emerald-500">
              <option value="amendment">Otrosí</option>
              <option value="legal_annex">Anexo legal</option>
              <option value="client_document">Doc. del cliente</option>
              <option value="other">Otro</option>
            </select>
          </div>
          <div v-if="uploadType === 'other'" class="min-w-[120px]">
            <label class="block text-xs text-gray-400 mb-1">Nombre categoría</label>
            <input v-model="uploadCustomLabel" type="text" placeholder="Ej: Diseños"
              class="w-full px-3 py-2 border border-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-emerald-500" />
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1">Archivo</label>
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
              class="text-xs file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-emerald-50 file:text-emerald-700 file:rounded-lg hover:file:bg-emerald-100" />
          </div>
          <button type="button" :disabled="isUploading" @click="handleUpload"
            class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50">
            {{ isUploading ? 'Subiendo...' : 'Subir' }}
          </button>
        </div>
      </div>
    </section>
    <!-- Send documents modal -->
    <SendDocumentsModal
      :visible="showSendModal"
      :proposal="proposal"
      :selected-main-docs="selectedMainDocs"
      :selected-additional-docs="selectedAdditionalDocsList"
      @cancel="showSendModal = false"
      @sent="handleDocumentsSent"
    />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';
import SendDocumentsModal from '~/components/BusinessProposal/admin/SendDocumentsModal.vue';

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

// Send documents state
const selectedMainDocs = ref(['draft_contract', 'commercial', 'technical']);
const selectedAdditionalDocIds = ref([]);
const sendSuccess = ref(false);
const showSendModal = ref(false);

const contractDoc = computed(() =>
  props.documents.find(d => d.document_type === 'contract'),
);

const contractPdfUrl = computed(() =>
  `/api/proposals/${props.proposal.id}/contract/pdf/`,
);

const draftContractPdfUrl = computed(() =>
  `/api/proposals/${props.proposal.id}/contract/draft-pdf/`,
);

const additionalDocs = computed(() =>
  props.documents.filter(d => d.document_type !== 'contract'),
);

const hasSelectedDocs = computed(() =>
  selectedMainDocs.value.length > 0 || selectedAdditionalDocIds.value.length > 0,
);

function formatDate(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'long', year: 'numeric',
  });
}

const selectedAdditionalDocsList = computed(() =>
  additionalDocs.value.filter(d => selectedAdditionalDocIds.value.includes(d.id)),
);

let successTimer = null;
onBeforeUnmount(() => { clearTimeout(successTimer); });

function handleDocumentsSent() {
  showSendModal.value = false;
  sendSuccess.value = true;
  clearTimeout(successTimer);
  successTimer = setTimeout(() => { sendSuccess.value = false; }, 5000);
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
  }
  isUploading.value = false;
}

async function handleDelete(docId) {
  const result = await proposalStore.deleteProposalDocument(props.proposal.id, docId);
  if (result.success) {
    emit('refresh');
  }
}
</script>
