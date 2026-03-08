<template>
  <button
    type="button"
    class="pdf-download fixed bottom-20 right-4 z-40
           flex items-center gap-2 px-4 py-2.5
           bg-white/90 backdrop-blur-sm shadow-lg border border-gray-200
           rounded-xl text-sm font-medium text-gray-700
           hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200
           transition-colors"
    :disabled="isGenerating"
    @click="downloadPdf"
  >
    <!-- Spinner while generating -->
    <svg v-if="isGenerating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
    <!-- Download icon -->
    <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
    <span>{{ isGenerating ? 'Generando...' : 'PDF' }}</span>
  </button>
</template>

<script setup>
import { ref } from 'vue';

const isGenerating = ref(false);

const proposalStore = useProposalStore();

async function downloadPdf() {
  if (isGenerating.value) return;
  isGenerating.value = true;

  try {
    const uuid = proposalStore.currentProposal?.uuid;
    if (!uuid) return;

    // Read selected modules from localStorage if available
    let pdfUrl = `/api/proposals/${uuid}/pdf/`;
    try {
      const raw = localStorage.getItem(`proposal-${uuid}-modules`);
      if (raw) {
        const selectedIds = JSON.parse(raw);
        if (Array.isArray(selectedIds) && selectedIds.length) {
          pdfUrl += `?selected_modules=${encodeURIComponent(selectedIds.join(','))}`;
        }
      }
    } catch (_e) { /* ignore */ }

    const response = await fetch(pdfUrl);
    if (!response.ok) {
      throw new Error(`PDF request failed: ${response.status}`);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const clientName = proposalStore.currentProposal?.client_name || 'Propuesta';
    const safeName = clientName.replace(/[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ ]/g, '').trim();
    const createdAt = proposalStore.currentProposal?.created_at;
    const dateSuffix = createdAt ? new Date(createdAt).toISOString().slice(0, 10) : new Date().toISOString().slice(0, 10);

    const link = document.createElement('a');
    link.href = url;
    link.download = `Propuesta_${safeName}_${dateSuffix}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('PDF download failed:', err);
  } finally {
    isGenerating.value = false;
  }
}
</script>
