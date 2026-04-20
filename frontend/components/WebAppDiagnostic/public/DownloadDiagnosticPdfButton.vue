<template>
  <button
    type="button"
    data-testid="download-diagnostic-pdf-btn"
    class="pdf-download fixed bottom-[4.75rem] right-4 z-40
           w-12 h-12 rounded-full
           bg-white/90 backdrop-blur-sm shadow-lg border border-esmerald/15
           flex items-center justify-center text-esmerald/70
           hover:bg-esmerald/5 hover:text-esmerald hover:border-esmerald/30
           transition-colors"
    :disabled="isGenerating"
    :title="isGenerating ? 'Generando...' : 'Descargar PDF'"
    @click="downloadPdf"
  >
    <svg v-if="isGenerating" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  </button>
</template>

<script setup>
import { ref } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';

const isGenerating = ref(false);
const store = useDiagnosticsStore();

async function downloadPdf() {
  if (isGenerating.value) return;
  isGenerating.value = true;

  try {
    const uuid = store.current?.uuid;
    if (!uuid) return;

    const pdfUrl = `/api/diagnostics/public/${uuid}/pdf/`;
    const response = await fetch(pdfUrl);
    if (!response.ok) {
      throw new Error(`PDF request failed: ${response.status}`);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const title = store.current?.title || store.current?.client_name || 'Diagnostico';
    const safeName = title.replace(/[^\w\sáéíóúñÁÉÍÓÚÑ-]/g, '').trim().replace(/\s+/g, '_').slice(0, 100);
    const d = new Date();
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yy = String(d.getFullYear()).slice(-2);
    const dateSuffix = `${dd}-${mm}-${yy}`;

    const link = document.createElement('a');
    link.href = url;
    link.download = `Diagnostico_${safeName}_${dateSuffix}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Diagnostic PDF download failed:', err);
  } finally {
    isGenerating.value = false;
  }
}
</script>
