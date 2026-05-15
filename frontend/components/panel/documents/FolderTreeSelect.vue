<template>
  <div ref="wrapperRef" class="relative w-full">
    <!-- Trigger -->
    <button
      type="button"
      class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg
             bg-surface border border-border-default text-text-default
             hover:bg-surface-raised focus:ring-2 focus:ring-focus-ring/30 outline-none
             transition-colors"
      :aria-expanded="isOpen"
      :aria-haspopup="'listbox'"
      @click="toggleOpen"
    >
      <svg
        v-if="selectedPath.length === 0"
        class="w-3.5 h-3.5 flex-shrink-0 text-text-subtle"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
      </svg>
      <svg
        v-else
        class="w-3.5 h-3.5 flex-shrink-0 text-amber-500 dark:text-amber-400"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
      </svg>

      <span class="flex-1 truncate text-left">
        <span v-if="selectedPath.length === 0" class="text-text-muted">— Raíz —</span>
        <span v-else>{{ selectedLabel }}</span>
      </span>

      <svg
        class="w-3.5 h-3.5 flex-shrink-0 text-text-subtle transition-transform"
        :class="{ 'rotate-180': isOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Popover -->
    <Transition name="dropdown-fade">
      <div
        v-if="isOpen"
        class="absolute left-0 right-0 mt-1 z-20 bg-surface border border-border-default
               rounded-lg shadow-lg overflow-hidden"
        role="listbox"
      >
        <!-- Search -->
        <div v-if="folders.length > 4" class="relative border-b border-border-muted">
          <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-subtle pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            placeholder="Buscar carpeta..."
            class="w-full pl-8 pr-3 py-2 text-xs bg-surface text-text-default placeholder-text-subtle outline-none"
            @keydown.esc="close"
          />
        </div>

        <!-- Options list -->
        <ul class="max-h-72 overflow-y-auto py-1">
          <!-- "Raíz" option always visible -->
          <li>
            <button
              type="button"
              class="w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors"
              :class="modelValue === null
                ? 'bg-primary-soft text-text-brand font-medium'
                : 'text-text-default hover:bg-surface-muted dark:hover:bg-gray-700/50'"
              @click="select(null)"
            >
              <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
              </svg>
              <span class="flex-1">— Raíz —</span>
              <svg
                v-if="modelValue === null"
                class="w-3.5 h-3.5 flex-shrink-0 text-text-brand"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            </button>
          </li>

          <!-- Tree items, flat-rendered with depth-based indentation -->
          <li v-for="row in visibleRows" :key="row.folder.id">
            <button
              type="button"
              :disabled="row.disabled"
              class="w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors"
              :class="[
                rowClass(row),
                row.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
              ]"
              :style="{ paddingLeft: `${12 + row.depth * 16}px` }"
              @click="!row.disabled && select(row.folder.id)"
            >
              <svg class="w-3.5 h-3.5 flex-shrink-0 text-amber-500 dark:text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
              </svg>
              <span class="flex-1 truncate">{{ row.folder.name }}</span>
              <span
                v-if="row.disabled"
                class="text-[10px] uppercase tracking-wider text-text-subtle flex-shrink-0"
              >Nivel máx.</span>
              <svg
                v-else-if="modelValue === row.folder.id"
                class="w-3.5 h-3.5 flex-shrink-0 text-text-brand"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            </button>
          </li>

          <li v-if="searchQuery && visibleRows.length === 0" class="px-3 py-4 text-center text-xs text-text-subtle">
            Sin coincidencias.
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue';
import { onClickOutside, onKeyStroke } from '@vueuse/core';
import { useDocumentFolderStore } from '~/stores/document_folders';

const MAX_FOLDER_DEPTH = 5; // mirrors backend MAX_FOLDER_DEPTH

const props = defineProps({
  modelValue: { type: [Number, null], default: null },
});

const emit = defineEmits(['update:modelValue']);

const folderStore = useDocumentFolderStore();

const isOpen = ref(false);
const searchQuery = ref('');
const wrapperRef = ref(null);
const searchInputRef = ref(null);

// Flatten the tree once, deriving depth + selectability.
const folders = computed(() => {
  const rows = [];
  const walk = (nodes, depth) => {
    for (const n of nodes) {
      rows.push({
        folder: n.folder,
        depth,
        disabled: depth >= MAX_FOLDER_DEPTH - 1,
      });
      if (n.children?.length) walk(n.children, depth + 1);
    }
  };
  walk(folderStore.tree, 0);
  return rows;
});

const visibleRows = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return folders.value;
  // Match by folder name OR any ancestor name (so deep matches still surface).
  return folders.value.filter((row) => {
    if (row.folder.name.toLowerCase().includes(q)) return true;
    const ancestors = folderStore.ancestorsOf(row.folder.id);
    return ancestors.some((a) => a.name.toLowerCase().includes(q));
  });
});

const selectedPath = computed(() => {
  if (props.modelValue == null) return [];
  const folder = folderStore.getById(props.modelValue);
  if (!folder) return [];
  return [...folderStore.ancestorsOf(props.modelValue), folder];
});

const selectedLabel = computed(() =>
  selectedPath.value.map((f) => f.name).join(' › '),
);

function rowClass(row) {
  if (props.modelValue === row.folder.id) {
    return 'bg-primary-soft text-text-brand font-medium';
  }
  return 'text-text-default hover:bg-surface-muted dark:hover:bg-gray-700/50';
}

function toggleOpen() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    nextTick(() => {
      if (searchInputRef.value) searchInputRef.value.focus();
    });
  } else {
    searchQuery.value = '';
  }
}

function close() {
  isOpen.value = false;
  searchQuery.value = '';
}

function select(id) {
  emit('update:modelValue', id);
  close();
}

onClickOutside(wrapperRef, close);
onKeyStroke('Escape', () => { if (isOpen.value) close(); });

// Reset search when popover closes externally.
watch(isOpen, (open) => {
  if (!open) searchQuery.value = '';
});
</script>
