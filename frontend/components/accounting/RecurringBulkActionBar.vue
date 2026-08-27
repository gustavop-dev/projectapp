<template>
  <BaseBulkActionBar
    :selected-count="selected.length"
    :outside-count="outsideCount"
    :filtered-count="filteredIds.length"
    :all-filtered-selected="allFilteredSelected"
    :actions="actions"
    :busy="busy"
    testid-prefix="recurring"
    @select-all="selectAllFiltered"
    @clear="emit('update:selected', [])"
  />

  <ConfirmModal
    v-model="confirmState.open"
    size="lg"
    :title="confirmState.title"
    :message="confirmState.message"
    :confirm-text="confirmState.confirmText"
    :cancel-text="confirmState.cancelText"
    :variant="confirmState.variant"
    @confirm="handleConfirmed"
    @cancel="handleCancelled"
  >
    <ul class="mt-4 max-h-64 space-y-1 overflow-y-auto rounded-xl bg-surface-raised p-3 text-sm">
      <li v-for="row in selectedRows" :key="row.id" class="flex gap-2 text-text-default">
        <span class="text-text-subtle">#{{ row.id }}</span>
        <span>{{ row.name }}</span>
      </li>
    </ul>
  </ConfirmModal>
</template>

<script setup>
import { computed } from 'vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import BaseBulkActionBar from '~/components/base/BaseBulkActionBar.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { toggleKeys } from '~/utils/rowSelection';

const props = defineProps({
  rows: { type: Array, default: () => [] },
  selected: { type: Array, default: () => [] },
  filteredIds: { type: Array, default: () => [] },
  busy: { type: Boolean, default: false },
});
const emit = defineEmits(['update:selected', 'submit']);
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const allFilteredSelected = computed(() => (
  props.filteredIds.length > 0
  && props.filteredIds.every((id) => props.selected.includes(id))
));
const outsideCount = computed(() => {
  const visible = new Set(props.filteredIds);
  return props.selected.filter((id) => !visible.has(id)).length;
});
const selectedRows = computed(() => {
  const byId = new Map(props.rows.map((row) => [row.id, row]));
  return props.selected.map((id) => byId.get(id) || {
    id,
    name: 'Registro no disponible; el servidor validará la selección.',
  });
});

const definitions = {
  activate: {
    title: 'Activar pagos recurrentes',
    message: 'Estos pagos volverán a contar en el presupuesto y en el calendario de avisos.',
    confirmText: 'Activar',
    variant: 'info',
  },
  deactivate: {
    title: 'Desactivar pagos recurrentes',
    message: 'Estos pagos dejarán de contar en el presupuesto y no generarán avisos.',
    confirmText: 'Desactivar',
    variant: 'warning',
  },
  archive: {
    title: 'Archivar pagos recurrentes',
    message: 'Se desactivarán y pasarán a Archivados. Sus datos se conservarán.',
    confirmText: 'Archivar',
    variant: 'danger',
  },
};

function confirm(action) {
  const copy = definitions[action];
  requestConfirm({
    ...copy,
    onConfirm: () => emit('submit', { ids: [...props.selected], action }),
  });
}

const actions = computed(() => [
  { action: 'activate', label: 'Activar seleccionados', onClick: () => confirm('activate') },
  { action: 'deactivate', label: 'Desactivar seleccionados', onClick: () => confirm('deactivate') },
  { divider: true },
  {
    action: 'archive', label: 'Archivar seleccionados', danger: true,
    onClick: () => confirm('archive'),
  },
]);

function selectAllFiltered() {
  emit('update:selected', toggleKeys(props.selected, props.filteredIds, true));
}
</script>
