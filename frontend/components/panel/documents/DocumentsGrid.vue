<script setup>
import DocumentCard from '~/components/panel/documents/DocumentCard.vue'
import { folderRowSummary } from '~/utils/documentStatus'

defineProps({
  documents: { type: Array, default: () => [] },
  subfolders: { type: Array, default: () => [] },
  editToFor: { type: Function, default: () => null },
  draggingDocId: { type: [Number, String], default: null },
  dragOverFolderId: { type: [Number, String], default: null },
  newlyCreatedId: { type: [Number, String], default: null },
})

const emit = defineEmits([
  'open', 'action', 'select-folder',
  'doc-dragstart', 'doc-dragend',
  'folder-dragstart', 'folder-dragend', 'folder-dragover', 'folder-dragleave',
  'drop-on-folder',
])
</script>

<template>
  <div
    class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4"
    data-testid="documents-grid"
  >
    <!-- Subfolder cards first, outside pagination (same rule as the table) -->
    <div
      v-for="sub in subfolders"
      :key="`folder-${sub.id}`"
      class="flex flex-col items-center justify-center gap-2 min-h-44 p-4 rounded-xl
             border-2 border-dashed border-border-default bg-surface cursor-pointer select-none
             text-center outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40"
      :class="{ 'ring-2 ring-success-strong border-success-strong/60': dragOverFolderId === sub.id }"
      role="button"
      tabindex="0"
      draggable="true"
      :data-testid="`folder-card-${sub.id}`"
      @click="emit('select-folder', sub.id)"
      @keydown.enter.prevent="emit('select-folder', sub.id)"
      @dragstart="emit('folder-dragstart', $event, sub)"
      @dragend="emit('folder-dragend')"
      @dragover="emit('folder-dragover', $event, sub.id)"
      @dragleave="emit('folder-dragleave')"
      @drop.prevent="emit('drop-on-folder', sub.id)"
    >
      <svg class="w-10 h-10 text-amber-500 dark:text-amber-400" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
      </svg>
      <span class="text-sm font-medium text-text-default truncate max-w-full">{{ sub.name }}</span>
      <span class="text-xs text-text-subtle">{{ folderRowSummary(sub) }}</span>
    </div>

    <DocumentCard
      v-for="doc in documents"
      :key="doc.id"
      :document="doc"
      :edit-to="editToFor(doc)"
      :dragging="draggingDocId === doc.id"
      :newly-created="newlyCreatedId === doc.id"
      @open="emit('open', doc)"
      @action="emit('action', doc)"
      @dragstart="emit('doc-dragstart', $event, doc)"
      @dragend="emit('doc-dragend')"
    />
  </div>
</template>
