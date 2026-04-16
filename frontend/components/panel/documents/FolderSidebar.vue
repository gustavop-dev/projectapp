<template>
  <aside class="bg-white rounded-xl shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700 flex flex-col">
    <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between flex-shrink-0">
      <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Carpetas</h3>
      <button
        type="button"
        class="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
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
          <span class="text-xs text-gray-400">{{ totalCount }}</span>
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
          <svg v-if="isDragging" class="w-3 h-3 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </li>

      <li v-if="folders.length" class="my-1 border-t border-gray-100 dark:border-gray-700"></li>

      <!-- Folder entries — each is a drop target -->
      <li v-for="folder in folders" :key="folder.id">
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-left transition-all"
          :class="[entryClass(folder.id), dropZoneClass(folder.id)]"
          @click="$emit('select', folder.id)"
          @dragover.prevent="dragOverId = folder.id"
          @dragleave="dragOverId = null"
          @drop.prevent="onDrop(folder.id)"
        >
          <span class="truncate flex-1">{{ folder.name }}</span>
          <span v-if="!isDragging || dragOverId !== folder.id" class="text-xs text-gray-400 ml-1">{{ folder.document_count }}</span>
          <svg v-else class="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </li>
    </ul>

    <div class="p-3 border-t border-gray-100 dark:border-gray-700 flex-shrink-0">
      <button
        type="button"
        class="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
               text-emerald-700 bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 dark:hover:bg-emerald-900/50"
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
import { ref } from 'vue';

const props = defineProps({
  folders: { type: Array, default: () => [] },
  activeId: { type: [String, Number], default: 'all' },
  totalCount: { type: Number, default: 0 },
  isDragging: { type: Boolean, default: false },
});

const emit = defineEmits(['select', 'manage', 'folder-drop']);

const dragOverId = ref(null);

const ACTIVE_CLASS = 'bg-emerald-50 text-emerald-700 font-medium dark:bg-emerald-900/30 dark:text-emerald-300';
const INACTIVE_CLASS = 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700/50';

function entryClass(id) {
  return props.activeId === id ? ACTIVE_CLASS : INACTIVE_CLASS;
}

function dropZoneClass(id) {
  if (!props.isDragging) return '';
  if (dragOverId.value === id) {
    return 'ring-2 ring-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 !text-emerald-700 dark:!text-emerald-300';
  }
  return 'ring-1 ring-dashed ring-gray-200 dark:ring-gray-600';
}

function onDrop(folderId) {
  dragOverId.value = null;
  emit('folder-drop', folderId);
}
</script>
