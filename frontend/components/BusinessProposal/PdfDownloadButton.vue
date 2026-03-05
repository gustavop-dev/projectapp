<template>
  <button
    class="pdf-download fixed bottom-20 right-4 z-40
           flex items-center gap-2 px-4 py-2.5
           bg-white/90 backdrop-blur-sm shadow-lg border border-gray-200
           rounded-xl text-sm font-medium text-gray-700
           hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200
           transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    :disabled="isGenerating"
    @click="generatePdf"
  >
    <svg v-if="!isGenerating" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
    <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <span>{{ isGenerating ? 'Generando...' : 'PDF' }}</span>
  </button>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  clientName: {
    type: String,
    default: 'Propuesta',
  },
  scrollContainer: {
    type: Object,
    default: null,
  },
});

const isGenerating = ref(false);

const PORTRAIT_SECTION_TYPES = new Set([
  'development_stages', 'timeline', 'investment',
]);

function getPageOrientation(panel) {
  const sectionType = panel.getAttribute('data-section-type') || '';
  return PORTRAIT_SECTION_TYPES.has(sectionType) ? 'portrait' : 'landscape';
}

async function generatePdf() {
  if (isGenerating.value) return;
  isGenerating.value = true;

  try {
    const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf'),
    ]);

    const container = props.scrollContainer;
    if (!container) {
      console.error('No scroll container provided for PDF generation');
      return;
    }

    const panels = Array.from(container.querySelectorAll('.panel'));
    if (panels.length === 0) return;

    const firstOrientation = getPageOrientation(panels[0]);
    const pdf = new jsPDF({ orientation: firstOrientation, unit: 'mm', format: 'a4' });

    for (let i = 0; i < panels.length; i++) {
      const panel = panels[i];
      const orientation = getPageOrientation(panel);
      const isPortrait = orientation === 'portrait';

      if (i > 0) {
        pdf.addPage('a4', orientation);
      }

      const pageW = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();

      const canvas = await html2canvas(panel, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
        width: panel.scrollWidth,
        height: panel.scrollHeight,
        windowWidth: panel.scrollWidth,
        windowHeight: panel.scrollHeight,
      });

      const imgData = canvas.toDataURL('image/jpeg', 0.85);
      const imgRatio = canvas.width / canvas.height;

      if (isPortrait && canvas.height > canvas.width) {
        const contentImgW = pageW;
        const contentImgH = contentImgW / imgRatio;
        const totalPages = Math.ceil(contentImgH / pageH);

        for (let p = 0; p < totalPages; p++) {
          if (p > 0) pdf.addPage('a4', 'portrait');
          const yOffset = -(p * pageH);
          pdf.addImage(imgData, 'JPEG', 0, yOffset, contentImgW, contentImgH);
        }
      } else {
        const pageRatio = pageW / pageH;
        let imgW, imgH;
        if (imgRatio > pageRatio) {
          imgW = pageW;
          imgH = pageW / imgRatio;
        } else {
          imgH = pageH;
          imgW = pageH * imgRatio;
        }
        const x = (pageW - imgW) / 2;
        const y = (pageH - imgH) / 2;
        pdf.addImage(imgData, 'JPEG', x, y, imgW, imgH);
      }
    }

    const safeName = props.clientName.replace(/[^a-zA-Z0-9\s-]/g, '').trim().replace(/\s+/g, '-');
    pdf.save(`Propuesta-${safeName || 'ProjectApp'}.pdf`);

  } catch (error) {
    console.error('Error generating PDF:', error);
  } finally {
    isGenerating.value = false;
  }
}
</script>
