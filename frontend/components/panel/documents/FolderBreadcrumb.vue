<template>
  <nav
    class="flex items-center gap-0.5 flex-wrap text-sm mb-4"
    aria-label="Ruta de carpetas"
  >
    <button
      type="button"
      class="px-2 py-1 rounded-lg transition-colors"
      :class="segmentClass(dragOverId === 'all')"
      @click="$emit('select', 'all')"
      @dragover="onDragOver($event, 'all')"
      @dragleave="dragOverId = null"
      @drop.prevent="onDrop('all')"
    >
      Todos
    </button>

    <template v-if="activeId === 'none'">
      <span class="px-1 text-text-subtle select-none">›</span>
      <span class="px-2 py-1 font-medium text-text-default">Sin carpeta</span>
    </template>

    <template v-for="(crumb, idx) in ancestors" :key="crumb.id">
      <span class="px-1 text-text-subtle select-none">›</span>
      <button
        v-if="idx < ancestors.length - 1"
        type="button"
        class="px-2 py-1 rounded-lg transition-colors max-w-[180px] truncate"
        :class="segmentClass(dragOverId === crumb.id)"
        @click="$emit('select', crumb.id)"
        @dragover="onDragOver($event, crumb.id)"
        @dragleave="dragOverId = null"
        @drop.prevent="onDrop(crumb.id)"
      >
        {{ crumb.name }}
      </button>
      <span
        v-else
        class="px-2 py-1 font-medium text-text-default max-w-[200px] truncate"
      >
        {{ crumb.name }}
      </span>
    </template>
  </nav>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  activeId: { type: [String, Number], default: 'all' },
  draggingFolderId: { type: [String, Number], default: null },
});
const emit = defineEmits(['select', 'nest']);

const folderStore = useDocumentFolderStore();
const dragOverId = ref(null);

const ancestors = computed(() => {
  if (typeof props.activeId !== 'number') return [];
  return folderStore.ancestorsOf(props.activeId);
});

function segmentClass(isOver) {
  if (isOver) return 'bg-primary-soft text-text-brand ring-1 ring-emerald-400';
  return 'text-text-muted hover:bg-surface-muted hover:text-text-default';
}

// Un destino es válido si hay una carpeta en arrastre y el destino no es ella
// misma ni uno de sus descendientes (evita ciclos).
function isValidTarget(id) {
  if (props.draggingFolderId == null) return false;
  const destId = id === 'all' ? null : id;
  if (destId === props.draggingFolderId) return false;
  if (destId != null
    && folderStore.descendantIdsOf(props.draggingFolderId).has(destId)) {
    return false;
  }
  return true;
}

function onDragOver(event, id) {
  if (!isValidTarget(id)) return;
  event.preventDefault();
  dragOverId.value = id;
}

function onDrop(id) {
  dragOverId.value = null;
  if (!isValidTarget(id)) return;
  emit('nest', {
    destId: id === 'all' ? null : id,
    draggedFolderId: props.draggingFolderId,
  });
}
</script>
