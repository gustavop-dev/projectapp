<template>
  <div class="space-y-8">
    <!-- Send section -->
    <section class="bg-white dark:bg-gray-800 border border-emerald-100 dark:border-emerald-700/30 rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Enviar documentos al cliente</h3>
      </div>

      <div v-if="attachments.length" class="space-y-2 mb-4">
        <label v-for="att in attachments" :key="att.id"
          class="flex items-center gap-2 cursor-pointer">
          <input v-model="selectedIds" type="checkbox" :value="att.id"
            class="rounded border-gray-300 dark:border-white/[0.15] text-emerald-600 focus:ring-emerald-500" />
          <span class="px-1.5 py-0.5 bg-gray-200 dark:bg-white/[0.08] text-gray-600 dark:text-gray-400 rounded text-[10px] font-medium">
            {{ att.document_type_display }}
          </span>
          <span class="text-xs text-gray-700 dark:text-white/70">{{ att.title }}</span>
        </label>
      </div>
      <p v-else class="text-xs text-gray-400 dark:text-gray-500 mb-4">
        Sube un documento para poder enviarlo al cliente.
      </p>

      <div class="flex items-center justify-between pt-2">
        <p v-if="clientEmail" class="text-xs text-gray-400 dark:text-gray-500">
          Se enviará a: <span class="font-medium text-gray-600 dark:text-white/70">{{ clientEmail }}</span>
        </p>
        <p v-else class="text-xs text-red-400">No hay email del cliente configurado</p>
        <button type="button"
          :disabled="!selectedIds.length || !clientEmail"
          class="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          @click="showSendModal = true">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
          Enviar al cliente
        </button>
      </div>
      <p v-if="sendSuccess" class="text-xs text-emerald-600 mt-2">
        Documentos enviados correctamente.
      </p>
    </section>

    <!-- Attachments list + upload -->
    <section class="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl p-5">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Documentos adjuntos</h3>
        </div>
      </div>

      <div v-if="attachments.length" class="space-y-2 mb-4">
        <div v-for="att in attachments" :key="att.id"
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
          <button type="button"
            class="text-gray-400 hover:text-red-500 transition-colors p-1"
            @click="handleDelete(att.id)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
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

    <SendDiagnosticDocumentsModal
      :visible="showSendModal"
      :diagnostic="diagnostic"
      :selected-attachments="selectedAttachments"
      @cancel="showSendModal = false"
      @sent="handleDocumentsSent" />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';
import SendDiagnosticDocumentsModal from '~/components/WebAppDiagnostic/SendDiagnosticDocumentsModal.vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';

const props = defineProps({
  diagnostic: { type: Object, required: true },
});

const store = useDiagnosticsStore();

const attachments = computed(() => props.diagnostic.attachments || []);
const clientEmail = computed(() => props.diagnostic.client?.email || '');

const selectedIds = ref([]);
const selectedAttachments = computed(() =>
  attachments.value.filter((a) => selectedIds.value.includes(a.id)),
);

const showSendModal = ref(false);
const sendSuccess = ref(false);

const isUploading = ref(false);
const uploadTitle = ref('');
const uploadType = ref('other');
const uploadCustomLabel = ref('');
const uploadError = ref('');
const fileInput = ref(null);

let successTimer = null;
onBeforeUnmount(() => { clearTimeout(successTimer); });

function handleDocumentsSent() {
  showSendModal.value = false;
  sendSuccess.value = true;
  selectedIds.value = [];
  clearTimeout(successTimer);
  successTimer = setTimeout(() => { sendSuccess.value = false; }, 5000);
}

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
  await store.deleteAttachment(props.diagnostic.id, attachmentId);
  selectedIds.value = selectedIds.value.filter((id) => id !== attachmentId);
}
</script>
