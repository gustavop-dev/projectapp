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

    <PdfPreviewPane
      class="px-3 py-4 sm:px-6 sm:py-5"
      :src="src"
      :active="modelValue"
      :error-message="errorMessage"
      :loading-label="loadingLabel"
      :test-id-prefix="testIdPrefix"
    />
  </BaseModal>
</template>

<script setup>
import PdfPreviewPane from './PdfPreviewPane.vue';

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
</script>
