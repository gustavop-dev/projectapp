<template>
  <draggable
    v-model="localSiblings"
    item-key="id"
    handle=".folder-tree-handle"
    ghost-class="opacity-40"
    chosen-class="ring-2 ring-emerald-400"
    drag-class="rotate-1"
    class="space-y-1"
    @end="onReorderEnd"
  >
    <template #item="{ element: folder }">
      <div :key="folder.id">
        <div
          class="group flex items-center gap-2 px-2 py-2 rounded-lg border transition-all"
          :class="rowClass(folder)"
          :style="{ marginLeft: `${depth * 18}px` }"
        >
          <div
            class="folder-tree-handle flex-shrink-0 w-4 flex items-center justify-center
                   text-text-subtle dark:text-text-muted cursor-grab active:cursor-grabbing"
            title="Arrastrar para reordenar"
          >
            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 6a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 13.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 21a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3z" />
            </svg>
          </div>

          <div class="w-6 h-6 rounded-lg bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center flex-shrink-0">
            <svg class="w-3 h-3 text-amber-500 dark:text-amber-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
            </svg>
          </div>

          <span class="flex-1 min-w-0 text-sm font-medium text-text-default truncate">
            {{ folder.name }}
          </span>

          <span class="flex-shrink-0 text-xs text-text-subtle">
            {{ folder.document_count }} doc
          </span>

          <div class="flex items-center gap-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              type="button"
              class="w-7 h-7 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors"
              title="Editar carpeta"
              @click="$emit('edit', folder)"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              type="button"
              class="w-7 h-7 flex items-center justify-center rounded-lg text-text-subtle hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
              title="Eliminar carpeta"
              @click="$emit('delete', folder)"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        <FolderManagerTree
          v-if="childrenOf(folder.id).length"
          :siblings="childrenOf(folder.id)"
          :parent-id="folder.id"
          :depth="depth + 1"
          :editing-id="editingId"
          :deleting-id="deletingId"
          class="mt-1"
          @edit="$emit('edit', $event)"
          @delete="$emit('delete', $event)"
          @reorder="$emit('reorder', $event)"
        />
      </div>
    </template>
  </draggable>
</template>

<script setup>
import { ref, watch } from 'vue';
import draggable from 'vuedraggable';
// Auto-referencia explícita para el render recursivo del árbol.
import FolderManagerTree from '~/components/panel/documents/FolderManagerTree.vue';

const props = defineProps({
  siblings: { type: Array, default: () => [] },
  parentId: { type: Number, default: null },
  depth: { type: Number, default: 0 },
  editingId: { type: Number, default: null },
  deletingId: { type: Number, default: null },
});
const emit = defineEmits(['edit', 'delete', 'reorder']);

const folderStore = useDocumentFolderStore();
const localSiblings = ref([]);

watch(() => props.siblings, (v) => {
  localSiblings.value = [...v];
}, { immediate: true });

function childrenOf(id) {
  return folderStore.childrenOf(id);
}

function rowClass(folder) {
  if (folder.id === props.editingId) {
    return 'border-emerald-300 dark:border-emerald-600 bg-primary-soft';
  }
  if (folder.id === props.deletingId) {
    return 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20';
  }
  return 'border-border-muted hover:border-border-default dark:hover:border-gray-600 '
    + 'bg-surface hover:bg-surface-muted dark:hover:bg-gray-700/50';
}

// vuedraggable aísla cada lista por defecto: el reorden solo afecta este nivel.
function onReorderEnd() {
  emit('reorder', {
    parentId: props.parentId,
    orderedIds: localSiblings.value.map((f) => f.id),
  });
}
</script>
