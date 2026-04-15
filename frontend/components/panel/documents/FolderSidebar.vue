<template>
  <aside class="bg-white rounded-xl shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
    <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
      <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Carpetas</h3>
      <button
        type="button"
        class="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
        @click="$emit('manage')"
      >
        Gestionar
      </button>
    </div>

    <ul class="p-2 space-y-1" role="list">
      <li>
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors"
          :class="entryClass('all')"
          @click="$emit('select', 'all')"
        >
          <span>Todos</span>
          <span class="text-xs text-gray-400">{{ totalCount }}</span>
        </button>
      </li>
      <li>
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors"
          :class="entryClass('none')"
          @click="$emit('select', 'none')"
        >
          <span>Sin carpeta</span>
        </button>
      </li>

      <li v-if="folders.length" class="my-2 border-t border-gray-100 dark:border-gray-700"></li>

      <li v-for="folder in folders" :key="folder.id">
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-left transition-colors"
          :class="entryClass(folder.id)"
          @click="$emit('select', folder.id)"
        >
          <span class="truncate">{{ folder.name }}</span>
          <span class="text-xs text-gray-400">{{ folder.document_count }}</span>
        </button>
      </li>
    </ul>

    <div class="p-3 border-t border-gray-100 dark:border-gray-700">
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
const props = defineProps({
  folders: { type: Array, default: () => [] },
  activeId: { type: [String, Number], default: 'all' },
  totalCount: { type: Number, default: 0 },
});

defineEmits(['select', 'manage']);

const ACTIVE_CLASS = 'bg-emerald-50 text-emerald-700 font-medium dark:bg-emerald-900/30 dark:text-emerald-300';
const INACTIVE_CLASS = 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700/50';

function entryClass(id) {
  return props.activeId === id ? ACTIVE_CLASS : INACTIVE_CLASS;
}
</script>
