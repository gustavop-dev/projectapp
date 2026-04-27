<template>
  <aside class="bg-surface rounded-xl shadow-sm border border-border-muted flex flex-col">
    <div class="px-4 py-3 border-b border-border-muted flex items-center justify-between flex-shrink-0">
      <h3 class="text-xs font-semibold text-text-muted uppercase tracking-wider">Carpetas</h3>
      <button
        type="button"
        class="text-xs font-medium text-text-brand hover:text-text-brand dark:text-emerald-400"
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
          :class="[entryClass('none'), dropZoneClass('none')]"
          @click="$emit('select', 'none')"
          @dragover.prevent="dragOverId = 'none'"
          @dragleave="dragOverId = null"
          @drop.prevent="onDrop(null)"
        >
          <span>Sin carpeta</span>
          <svg v-if="isDragging" class="w-3 h-3 text-text-subtle flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </li>

      <li v-if="folders.length" class="my-1 border-t border-border-muted"></li>

      <!-- Folder entries — draggable to reorder, also drop targets for documents -->
      <draggable
        v-model="localFolders"
        item-key="id"
        handle=".folder-drag-handle"
        ghost-class="opacity-40"
        chosen-class="ring-1 ring-emerald-300"
        :disabled="isDragging"
        tag="div"
        @start="isFolderDragging = true"
        @end="handleFolderReorder"
      >
        <template #item="{ element: folder }">
          <li :key="folder.id" class="group">
            <div
              class="flex items-center rounded-lg transition-all"
              :class="[entryClass(folder.id), dropZoneClass(folder.id)]"
              @dragover.prevent="onFolderDragOver(folder.id)"
              @dragleave="dragOverId = null"
              @drop.prevent="onFolderDrop(folder.id)"
            >
              <div
                v-if="!isDragging"
                class="folder-drag-handle flex-shrink-0 w-5 flex items-center justify-center ml-1 text-text-subtle dark:text-text-muted opacity-0 group-hover:opacity-100 cursor-grab active:cursor-grabbing transition-opacity"
                title="Arrastrar para reordenar"
              >
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 6a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 13.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 21a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3z" />
                </svg>
              </div>
              <button
                type="button"
                class="flex-1 flex items-center justify-between px-3 py-2 text-sm text-left min-w-0"
                @click="$emit('select', folder.id)"
              >
                <span class="truncate flex-1">{{ folder.name }}</span>
                <span v-if="!isDragging || dragOverId !== folder.id" class="text-xs text-text-subtle ml-1 flex-shrink-0">{{ folder.document_count }}</span>
                <svg v-else class="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </li>
        </template>
      </draggable>
    </ul>

    <div class="p-3 border-t border-border-muted flex-shrink-0">
      <button
        type="button"
        class="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
               text-text-brand bg-primary-soft hover:bg-primary-soft dark:text-emerald-400 dark:hover:bg-emerald-900/50"
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
import { ref, watch } from 'vue';
import draggable from 'vuedraggable';

const props = defineProps({
  folders: { type: Array, default: () => [] },
  activeId: { type: [String, Number], default: 'all' },
  totalCount: { type: Number, default: 0 },
  isDragging: { type: Boolean, default: false },
});

const emit = defineEmits(['select', 'manage', 'folder-drop']);

const folderStore = useDocumentFolderStore();
const dragOverId = ref(null);
const localFolders = ref([]);
const isFolderDragging = ref(false);

watch(() => props.folders, (v) => {
  localFolders.value = [...v];
}, { immediate: true });

const ACTIVE_CLASS = 'bg-primary-soft text-text-brand font-medium dark:bg-emerald-900/30 dark:text-emerald-300';
const INACTIVE_CLASS = 'text-text-default hover:bg-gray-50 dark:text-text-subtle dark:hover:bg-gray-700/50';

function entryClass(id) {
  return props.activeId === id ? ACTIVE_CLASS : INACTIVE_CLASS;
}

function dropZoneClass(id) {
  if (!props.isDragging || isFolderDragging.value) return '';
  if (dragOverId.value === id) {
    return 'ring-2 ring-emerald-400 bg-primary-soft !text-text-brand dark:!text-emerald-300';
  }
  return 'ring-1 ring-dashed ring-gray-200 dark:ring-gray-600';
}

function onDrop(folderId) {
  dragOverId.value = null;
  emit('folder-drop', folderId);
}

function onFolderDragOver(folderId) {
  if (!isFolderDragging.value) dragOverId.value = folderId;
}

function onFolderDrop(folderId) {
  if (!isFolderDragging.value) onDrop(folderId);
}

async function handleFolderReorder() {
  isFolderDragging.value = false;
  const newIds = localFolders.value.map((f) => f.id);
  const unchanged = newIds.every((id, i) => id === props.folders[i]?.id);
  if (unchanged) return;
  const result = await folderStore.reorderFolders(newIds);
  if (!result.success) {
    await folderStore.fetchFolders();
  }
}
</script>
