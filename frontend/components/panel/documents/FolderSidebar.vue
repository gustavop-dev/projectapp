<template>
  <aside class="bg-surface rounded-xl shadow-sm border border-border-muted flex flex-col">
    <div class="px-4 py-3 border-b border-border-muted flex items-center justify-between flex-shrink-0">
      <h3 class="text-xs font-semibold text-text-muted uppercase tracking-wider">Carpetas</h3>
      <button
        type="button"
        class="text-xs font-medium text-text-brand hover:text-text-brand"
        @click="$emit('manage')"
      >
        Gestionar
      </button>
    </div>

    <ul class="p-2 space-y-1 flex-1 overflow-y-auto" role="list">
      <li>
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all"
          :class="entryClass('all')"
          @click="$emit('select', 'all')"
        >
          <span>Todos</span>
          <span class="text-xs text-text-subtle">{{ totalCount }}</span>
        </button>
      </li>

      <!-- No folder — also a drop target -->
      <li>
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all"
          :class="[entryClass('none'), noneDropZoneClass]"
          @click="$emit('select', 'none')"
          @dragover.prevent="dragOverNone = true"
          @dragleave="dragOverNone = false"
          @drop.prevent="onNoneDrop"
        >
          <span>Sin carpeta</span>
          <svg v-if="isDragging" class="w-3 h-3 text-text-subtle flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </li>

      <li v-if="rootNodes.length" class="my-1 border-t border-border-muted"></li>

      <!-- Root folder tree (recursive) — draggable at root scope -->
      <draggable
        :model-value="rootFolders"
        item-key="id"
        handle=".folder-drag-handle"
        ghost-class="opacity-40"
        group="folders"
        :disabled="isDragging"
        tag="div"
        @change="onRootChange"
      >
        <template #item="{ element: rootFolder }">
          <FolderTreeNode
            :node="nodeFor(rootFolder.id)"
            :level="0"
            :active-id="activeId"
            :is-dragging="isDragging"
            @select="$emit('select', $event)"
            @folder-drop="$emit('folder-drop', $event)"
          />
        </template>
      </draggable>
    </ul>

    <div class="p-3 border-t border-border-muted flex-shrink-0">
      <button
        type="button"
        class="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
               text-text-brand bg-primary-soft hover:bg-primary-soft"
        @click="$emit('manage')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nueva carpeta
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import draggable from 'vuedraggable';
import FolderTreeNode from './FolderTreeNode.vue';
import { useDocumentFolderStore } from '~/stores/document_folders';
import { useFolderExpansion } from '~/composables/useFolderExpansion';

const props = defineProps({
  folders: { type: Array, default: () => [] }, // not used directly anymore; kept for back-compat
  activeId: { type: [String, Number], default: 'all' },
  totalCount: { type: Number, default: 0 },
  isDragging: { type: Boolean, default: false },
});

const emit = defineEmits(['select', 'manage', 'folder-drop']);

const folderStore = useDocumentFolderStore();
const { expandPath } = useFolderExpansion();

const rootNodes = computed(() => folderStore.tree);
const rootFolders = computed(() => rootNodes.value.map((n) => n.folder));

function nodeFor(id) {
  return rootNodes.value.find((n) => n.folder.id === id);
}

const dragOverNone = ref(false);

const ACTIVE_CLASS = 'bg-primary-soft text-text-brand font-medium';
const INACTIVE_CLASS = 'text-text-default hover:bg-surface-muted dark:text-text-subtle dark:hover:bg-gray-700/50';

function entryClass(id) {
  return props.activeId === id ? ACTIVE_CLASS : INACTIVE_CLASS;
}

const noneDropZoneClass = computed(() => {
  if (!props.isDragging) return '';
  if (dragOverNone.value) {
    return 'ring-2 ring-emerald-400 bg-primary-soft !text-text-brand dark:!text-emerald-300';
  }
  return 'ring-1 ring-dashed ring-gray-200 dark:ring-gray-600';
});

function onNoneDrop() {
  dragOverNone.value = false;
  if (!props.isDragging) return;
  emit('folder-drop', null);
}

async function onRootChange(evt) {
  if (evt.added) {
    const movedId = evt.added.element.id;
    const position = evt.added.newIndex;
    await folderStore.moveFolder(movedId, { parent_id: null, position });
  } else if (evt.moved) {
    const orderedIds = rootFolders.value.map((f) => f.id);
    const [moved] = orderedIds.splice(evt.moved.oldIndex, 1);
    orderedIds.splice(evt.moved.newIndex, 0, moved);
    await folderStore.reorderFolders({ parent_id: null, ids: orderedIds });
  }
}

// Auto-expand ancestors of the active folder so it's always visible on load.
watch(
  [() => props.activeId, () => folderStore.folders.length],
  () => {
    if (typeof props.activeId !== 'number') return;
    const ancestorIds = folderStore.ancestorsOf(props.activeId).map((a) => a.id);
    expandPath(ancestorIds);
  },
  { immediate: true },
);
</script>
