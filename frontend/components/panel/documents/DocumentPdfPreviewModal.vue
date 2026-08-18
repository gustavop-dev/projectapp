<template>
  <BaseModal
    :model-value="modelValue"
    size="full"
    full-height
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex items-center justify-between gap-3 px-6 py-4 border-b border-border-muted flex-shrink-0">
      <div class="min-w-0">
        <h3 class="text-base font-semibold text-text-default truncate">{{ title }}</h3>
        <p class="text-xs text-text-subtle mt-0.5" data-testid="doc-pdf-preview-pages">
          El PDF incluye: {{ pagesLabel }}
        </p>
      </div>
      <BaseButton
        variant="ghost"
        icon-only
        size="md"
        class="w-9 h-9 flex-shrink-0"
        aria-label="Cerrar vista previa del PDF"
        @click="emit('update:modelValue', false)"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </BaseButton>
    </div>

    <div class="flex-1 min-h-0 flex flex-col px-6 py-5">
      <!-- El mismo archivo que entrega la descarga: lo genera el endpoint del
           documento, con `?inline=1` para que el visor lo muestre en vez de
           bajarlo. -->
      <embed
        v-if="pdfState === 'ready'"
        :src="pdfSrc"
        type="application/pdf"
        class="flex-1 min-h-0 w-full rounded-xl border border-border-default bg-surface-raised"
        data-testid="doc-pdf-preview-frame"
      >
      <div
        v-else-if="pdfState === 'error'"
        class="flex-1 min-h-0 flex flex-col items-center justify-center gap-1 rounded-xl border border-border-default px-6 text-center"
        data-testid="doc-pdf-preview-error"
      >
        <p class="text-sm font-medium text-text-default">
          No pudimos mostrar el PDF.
        </p>
        <p class="text-sm text-text-subtle">
          Un documento sin contenido todavía no genera archivo.
        </p>
      </div>
      <!-- `idle` cae acá a propósito: mientras no haya veredicto, lo honesto
           es decir que se está generando, no que falló. -->
      <div
        v-else
        class="flex-1 min-h-0 flex items-center justify-center gap-2 rounded-xl border border-border-default text-sm text-text-subtle"
        data-testid="doc-pdf-preview-loading"
      >
        <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
        Generando la vista previa…
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { describeIncludedPages } from '~/utils/documentCoverPages';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  documentId: { type: [Number, String], default: null },
  title: { type: String, default: 'Vista previa del PDF' },
  templateStyle: { type: String, default: '' },
  /** Sello de la versión guardada (`updated_at`): sin él, el navegador
   * devolvería el PDF cacheado y la vista previa mentiría tras guardar. */
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

// Un <embed> no emite load ni error: el estado del visor sale de sondear la
// URL con fetch, igual que el visor de cuentas de cobro.
const pdfState = ref('idle');

async function probePdf() {
  if (!pdfSrc.value) {
    pdfState.value = 'error';
    return;
  }
  pdfState.value = 'loading';
  try {
    const response = await fetch(pdfSrc.value, { credentials: 'same-origin' });
    pdfState.value = response.ok ? 'ready' : 'error';
  } catch {
    pdfState.value = 'error';
  }
}

// Se sondea en cada apertura, no una sola vez: entre una y otra el documento
// pudo guardarse con otras casillas, y ahí está el punto de esta vista.
// `immediate` porque el modal puede montarse ya abierto: sin eso se quedaba
// esperando un cambio que nunca llegaba.
watch(() => props.modelValue, (open) => {
  if (open) probePdf();
  else pdfState.value = 'idle';
}, { immediate: true });
</script>
