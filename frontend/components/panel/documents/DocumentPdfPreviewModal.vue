<template>
  <PdfPreviewModal
    :model-value="modelValue"
    :src="pdfSrc"
    :title="title"
    :description="`El PDF incluye: ${pagesLabel}`"
    description-test-id="doc-pdf-preview-pages"
    error-message="Un documento sin contenido todavía no genera archivo."
    loading-label="Generando la vista previa…"
    test-id-prefix="doc-pdf-preview"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed } from 'vue';
import PdfPreviewModal from '~/components/base/PdfPreviewModal.vue';
import { describeIncludedPages } from '~/utils/documentCoverPages';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  documentId: { type: [Number, String], default: null },
  title: { type: String, default: 'Vista previa del PDF' },
  templateStyle: { type: String, default: '' },
  version: { type: String, default: '' },
  coverOptions: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['update:modelValue']);
const pagesLabel = computed(() => describeIncludedPages(props.coverOptions));
const pdfSrc = computed(() => {
  if (!props.documentId) return '';
  const params = new URLSearchParams({ inline: '1' });
  if (props.templateStyle) params.set('template', props.templateStyle);
  if (props.version) params.set('v', props.version);
  return `/api/documents/${props.documentId}/pdf/?${params.toString()}`;
});
</script>
