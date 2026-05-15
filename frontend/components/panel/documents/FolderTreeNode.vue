<template>
  <li class="group">
    <div
      class="flex items-center rounded-lg transition-all"
      :class="[entryClass, dropZoneClass]"
      :style="indentStyle"
      @dragover.prevent="onDocDragOver"
      @dragleave="dragOverId === folder.id && (dragOverId = null)"
      @drop.prevent="onDocDrop"
    >
      <!-- Chevron / leaf spacer -->
      <button
        v-if="hasChildren"
        type="button"
        class="flex-shrink-0 w-5 h-7 flex items-center justify-center text-text-subtle hover:text-text-default"
        :title="isExpanded ? 'Colapsar' : 'Expandir'"
        @click.stop="toggle(folder.id)"
      >
        <svg
          class="w-3 h-3 transition-transform"
          :class="{ 'rotate-90': isExpanded }"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
        </svg>
      </button>
      <span v-else class="flex-shrink-0 w-5 h-7"></span>

      <!-- Drag handle (only when not dragging documents) -->
      <div
        v-if="!isDragging"
        class="folder-drag-handle flex-shrink-0 w-4 flex items-center justify-center text-text-subtle dark:text-text-muted opacity-0 group-hover:opacity-100 cursor-grab active:cursor-grabbing transition-opacity"
        title="Arrastrar para reordenar o mover"
      >
        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8 6a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 13.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 21a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3z" />
        </svg>
      </div>

      <!-- Selectable label -->
      <button
        type="button"
        class="flex-1 flex items-center justify-between px-2 py-1.5 text-sm text-left min-w-0"
        @click="$emit('select', folder.id)"
      >
        <span class="truncate flex-1">{{ folder.name }}</span>
        <span
          v-if="!isDragging || dragOverId !== folder.id"
          class="text-xs text-text-subtle ml-1 flex-shrink-0"
        >{{ folder.document_count }}</span>
        <svg v-else class="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    </div>

    <!-- Children: recursive draggable group -->
    <draggable
      v-if="hasChildren && isExpanded"
      :model-value="node.children.map((n) => n.folder)"
      item-key="id"
      handle=".folder-drag-handle"
      ghost-class="opacity-40"
      group="folders"
      :disabled="isDragging"
      tag="ul"
      class="space-y-1 mt-1"
      @change="onChildrenChange"
    >
      <template #item="{ element: childFolder }">
        <FolderTreeNode
          :node="childNodeFor(childFolder.id)"
          :level="level + 1"
          :active-id="activeId"
          :is-dragging="isDragging"
          @select="$emit('select', $event)"
          @folder-drop="$emit('folder-drop', $event)"
        />
      </template>
    </draggable>
  </li>
</template>

<script setup>
import { computed, ref } from 'vue';
import draggable from 'vuedraggable';
import { useFolderExpansion } from '~/composables/useFolderExpansion';
import { useDocumentFolderStore } from '~/stores/document_folders';

const props = defineProps({
  node: { type: Object, required: true }, // { folder, children }
  level: { type: Number, default: 0 },
  activeId: { type: [String, Number], default: 'all' },
  isDragging: { type: Boolean, default: false },
});

const emit = defineEmits(['select', 'folder-drop']);

const folderStore = useDocumentFolderStore();
const { isExpanded: isExp, toggle } = useFolderExpansion();

const dragOverId = ref(null);

const folder = computed(() => props.node.folder);
const hasChildren = computed(() => (props.node.children || []).length > 0);
const isExpanded = computed(() => isExp(folder.value.id));

const ACTIVE_CLASS = 'bg-primary-soft text-text-brand font-medium';
const INACTIVE_CLASS = 'text-text-default hover:bg-surface-muted dark:text-text-subtle dark:hover:bg-gray-700/50';

const entryClass = computed(() =>
  props.activeId === folder.value.id ? ACTIVE_CLASS : INACTIVE_CLASS,
);

const indentStyle = computed(() => ({
  paddingLeft: `${props.level * 12}px`,
}));

const dropZoneClass = computed(() => {
  if (!props.isDragging) return '';
  if (dragOverId.value === folder.value.id) {
    return 'ring-2 ring-emerald-400 bg-primary-soft !text-text-brand dark:!text-emerald-300';
  }
  return 'ring-1 ring-dashed ring-gray-200 dark:ring-gray-600';
});

function onDocDragOver() {
  if (props.isDragging) dragOverId.value = folder.value.id;
}

function onDocDrop() {
  dragOverId.value = null;
  if (!props.isDragging) return;
  emit('folder-drop', folder.value.id);
}

function childNodeFor(id) {
  return props.node.children.find((c) => c.folder.id === id);
}

async function onChildrenChange(evt) {
  if (evt.added) {
    const movedId = evt.added.element.id;
    const position = evt.added.newIndex;
    await folderStore.moveFolder(movedId, { parent_id: folder.value.id, position });
  } else if (evt.moved) {
    const orderedIds = props.node.children.map((n) => n.folder.id);
    // Apply the move in our local view to compute new order.
    const [moved] = orderedIds.splice(evt.moved.oldIndex, 1);
    orderedIds.splice(evt.moved.newIndex, 0, moved);
    await folderStore.reorderFolders({ parent_id: folder.value.id, ids: orderedIds });
  } else if (evt.removed) {
    // Handled by the receiving list's `added` event.
  }
}
</script>
