<script setup>
import { ref } from 'vue';
import { ArrowDownTrayIcon } from '@heroicons/vue/24/outline';
import BaseDropdown from '~/components/base/BaseDropdown.vue';
import { get_request } from '~/stores/services/request_http';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { downloadBlob, filenameFromDisposition } from '~/utils/downloadFile';

const props = defineProps({
  /** Backend section key (income, expense, hosting, pocket, recurring, ads, card_snapshot). */
  section: { type: String, required: true },
  /** Server-side query params mirroring the active filters. */
  params: { type: Object, default: () => ({}) },
});

const notify = usePanelNotify();
const isExporting = ref(false);

async function exportAs(format) {
  if (isExporting.value) return;
  isExporting.value = true;
  try {
    const query = new URLSearchParams({
      section: props.section,
      file_format: format,
      ...props.params,
    });
    const response = await get_request(`accounting/export/?${query}`, {
      responseType: 'blob',
    });
    const filename = filenameFromDisposition(
      response.headers?.['content-disposition'],
    ) || `contabilidad_${props.section}.${format}`;
    downloadBlob(response.data, filename);
  } catch (error) {
    notify.error({
      title: 'No se pudo exportar',
      detail: 'Intenta de nuevo o revisa los filtros aplicados.',
    });
  } finally {
    isExporting.value = false;
  }
}

const items = [
  { label: 'CSV', onClick: () => exportAs('csv') },
  { label: 'Excel (.xlsx)', onClick: () => exportAs('xlsx') },
];
</script>

<template>
  <BaseDropdown :items="items" align="right">
    <template #trigger>
      <span
        class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors border whitespace-nowrap bg-surface text-text-muted border-border-default hover:border-text-muted"
        :class="{ 'opacity-60 pointer-events-none': isExporting }"
        data-testid="accounting-export-button"
      >
        <ArrowDownTrayIcon class="w-4 h-4" />
        {{ isExporting ? 'Exportando...' : 'Exportar' }}
      </span>
    </template>
  </BaseDropdown>
</template>
