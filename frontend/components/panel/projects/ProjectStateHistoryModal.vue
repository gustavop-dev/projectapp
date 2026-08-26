<script setup>
import { watch } from 'vue';
import StateHistoryModal from '~/components/panel/states/StateHistoryModal.vue';
import { useProjectStateStore } from '~/stores/project_states';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  project: { type: Object, default: null },
});
const emit = defineEmits(['update:modelValue']);
const stateStore = useProjectStateStore();

watch(() => props.modelValue, async (open) => {
  if (open && props.project?.id) await stateStore.fetchHistory(props.project.id);
});
</script>

<template>
  <StateHistoryModal
    :model-value="modelValue"
    :history="stateStore.history"
    :loading="stateStore.isLoading"
    :title="project ? `Historial de ${project.name}` : 'Historial del proyecto'"
    test-id="project-state-history"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>
