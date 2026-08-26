<script setup>
import { watch } from 'vue';
import StateHistoryModal from '~/components/panel/states/StateHistoryModal.vue';
import { useDocumentStateStore } from '~/stores/document_states';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  documentId: { type: [Number, String], required: true },
});
const emit = defineEmits(['update:modelValue', 'changed']);
const stateStore = useDocumentStateStore();

watch(() => props.modelValue, async (open) => {
  if (open) await stateStore.fetchHistory(props.documentId);
});

async function correctOpening(episode) {
  const current = episode.opened_at ? episode.opened_at.slice(0, 16) : '';
  const value = window.prompt('Fecha y hora real (YYYY-MM-DDTHH:mm)', current);
  if (!value) return;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return;
  const result = await stateStore.correctEpisode(
    props.documentId,
    episode.id,
    parsed.toISOString(),
  );
  if (result.success) {
    await stateStore.fetchHistory(props.documentId);
    emit('changed');
  }
}
</script>

<template>
  <StateHistoryModal
    :model-value="modelValue"
    :history="stateStore.history"
    :loading="stateStore.isLoading"
    title="Historial de estados"
    test-id="document-state-history"
    allow-opening-correction
    @update:model-value="emit('update:modelValue', $event)"
    @correct-opening="correctOpening"
  />
</template>
