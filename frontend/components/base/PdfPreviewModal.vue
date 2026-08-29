<template>
  <BaseModal
    :model-value="modelValue"
    kind="workspace"
    full-height
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-shrink-0 items-center justify-between gap-3 border-b border-border-muted px-4 py-4 sm:px-6">
      <div class="min-w-0">
        <h3 class="truncate text-base font-semibold text-text-default">{{ title }}</h3>
        <p
          v-if="description"
          class="mt-0.5 text-xs text-text-subtle"
          :data-testid="descriptionTestId || `${testIdPrefix}-description`"
        >
          {{ description }}
        </p>
      </div>
      <BaseButton
        variant="ghost"
        icon-only
        size="md"
        class="h-9 w-9 flex-shrink-0"
        aria-label="Cerrar vista previa del PDF"
        title="Cerrar vista previa del PDF"
        @click="emit('update:modelValue', false)"
      >
        <BaseActionIcon action="close" />
      </BaseButton>
    </div>

    <div class="flex min-h-0 flex-1 flex-col px-3 py-4 sm:px-6 sm:py-5">
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
  </BaseModal>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  src: { type: String, default: '' },
  title: { type: String, default: 'Vista previa del PDF' },
  description: { type: String, default: '' },
  descriptionTestId: { type: String, default: '' },
  errorMessage: { type: String, default: 'El archivo no está disponible.' },
  loadingLabel: { type: String, default: 'Cargando la vista previa…' },
  testIdPrefix: { type: String, default: 'pdf-preview' },
});

const emit = defineEmits(['update:modelValue']);
const pdfState = ref('idle');

async function probePdf() {
  if (!props.src) {
    pdfState.value = 'error';
    return;
  }
  pdfState.value = 'loading';
  try {
    const response = await fetch(props.src, { credentials: 'same-origin' });
    pdfState.value = response.ok ? 'ready' : 'error';
  } catch {
    pdfState.value = 'error';
  }
}

watch(
  () => [props.modelValue, props.src],
  ([open]) => {
    if (open) probePdf();
    else pdfState.value = 'idle';
  },
  { immediate: true },
);
</script>
