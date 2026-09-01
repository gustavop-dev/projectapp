<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <embed
      v-if="pdfState === 'ready'"
      :src="src"
      type="application/pdf"
      class="min-h-0 w-full flex-1 rounded-xl border border-border-default bg-surface-raised"
      :data-testid="`${testIdPrefix}-frame`"
    >
    <div
      v-else-if="pdfState === 'error'"
      class="flex min-h-0 flex-1 flex-col items-center justify-center gap-1 rounded-xl border border-border-default px-6 text-center"
      :data-testid="`${testIdPrefix}-error`"
    >
      <p class="text-sm font-medium text-text-default">No pudimos mostrar el PDF.</p>
      <p class="text-sm text-text-subtle">{{ errorMessage }}</p>
    </div>
    <div
      v-else
      class="flex min-h-0 flex-1 items-center justify-center gap-2 rounded-xl border border-border-default text-sm text-text-subtle"
      :data-testid="`${testIdPrefix}-loading`"
    >
      <svg class="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
      </svg>
      {{ loadingLabel }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  src: { type: String, default: '' },
  active: { type: Boolean, default: true },
  errorMessage: { type: String, default: 'El archivo no está disponible.' },
  loadingLabel: { type: String, default: 'Cargando la vista previa…' },
  testIdPrefix: { type: String, default: 'pdf-preview' },
});

const pdfState = ref('idle');
let probeToken = 0;

async function probePdf() {
  const token = ++probeToken;
  if (!props.src) {
    pdfState.value = 'error';
    return;
  }
  pdfState.value = 'loading';
  try {
    const response = await fetch(props.src, { credentials: 'same-origin' });
    if (token === probeToken) pdfState.value = response.ok ? 'ready' : 'error';
  } catch {
    if (token === probeToken) pdfState.value = 'error';
  }
}

watch(
  () => [props.active, props.src],
  ([active]) => {
    if (active) probePdf();
    else {
      probeToken += 1;
      pdfState.value = 'idle';
    }
  },
  { immediate: true },
);
</script>
