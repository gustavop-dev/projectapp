<script setup>
/**
 * Aviso permanente de cambios sin guardar.
 *
 * El título ES la lista de campos. Decir "hay cambios" sin decir cuáles es el
 * aviso que ya existía —el botón Guardar habilitado— y que nadie leyó como una
 * advertencia: un botón habilitado se lee como "puedes guardar", no como "te
 * falta guardar".
 */
defineProps({
  /** "Cliente y proyecto sin guardar" — ya viene armado por useUnsavedGuard. */
  title: { type: String, required: true },
  /** La lista completa, sólo cuando el título pasó a contarlos. */
  detail: { type: String, default: '' },
  message: { type: String, default: 'Si sales de esta página, se pierden.' },
  canSave: { type: Boolean, default: true },
  saving: { type: Boolean, default: false },
  canDiscard: { type: Boolean, default: true },
  testid: { type: String, default: 'unsaved-changes-notice' },
});

defineEmits(['save', 'discard']);
</script>

<template>
  <BaseAlert variant="warning" :title="title" :data-testid="testid">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="min-w-0">
        <p v-if="detail" class="font-medium" :data-testid="`${testid}-detail`">{{ detail }}</p>
        <p>{{ message }}</p>
      </div>
      <div class="flex flex-shrink-0 flex-wrap items-center gap-2">
        <BaseButton
          v-if="canSave"
          variant="primary"
          size="sm"
          :loading="saving"
          :data-testid="`${testid}-save`"
          @click="$emit('save')"
        >
          Guardar ahora
        </BaseButton>
        <BaseButton
          v-if="canDiscard"
          variant="secondary"
          size="sm"
          :disabled="saving"
          :data-testid="`${testid}-discard`"
          @click="$emit('discard')"
        >
          Descartar cambios
        </BaseButton>
      </div>
    </div>
  </BaseAlert>
</template>
