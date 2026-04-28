<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue && document"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="close"
      >
        <div class="bg-surface rounded-2xl shadow-2xl w-full max-w-sm">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-border-muted">
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
              </div>
              <div class="min-w-0">
                <h3 class="text-base font-semibold text-text-default">Mover documento</h3>
                <p class="text-xs text-text-muted truncate max-w-[200px]">{{ document.title }}</p>
              </div>
            </div>
            <button
              type="button"
              class="w-8 h-8 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-muted hover:bg-surface-raised dark:hover:bg-gray-700 transition-colors"
              @click="close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Folder options -->
          <div class="p-4 space-y-1.5 max-h-72 overflow-y-auto">
            <!-- No folder option -->
            <button
              type="button"
              :disabled="isMoving"
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-all text-left disabled:opacity-50"
              :class="document.folder_id === null
                ? 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20'
                : 'border-border-muted hover:border-border-default dark:hover:border-gray-600 hover:bg-surface-muted dark:hover:bg-gray-700/50'"
              @click="moveToFolder(null)"
            >
              <div class="w-7 h-7 rounded-lg bg-surface-raised flex items-center justify-center flex-shrink-0">
                <svg class="w-3.5 h-3.5 text-text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              </div>
              <span class="flex-1 text-sm font-medium text-text-default">Sin carpeta</span>
              <svg
                v-if="document.folder_id === null"
                class="w-4 h-4 text-blue-500 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            </button>

            <!-- Folder entries -->
            <button
              v-for="folder in folderStore.folders"
              :key="folder.id"
              type="button"
              :disabled="isMoving"
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-all text-left disabled:opacity-50"
              :class="document.folder_id === folder.id
                ? 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20'
                : 'border-border-muted hover:border-border-default dark:hover:border-gray-600 hover:bg-surface-muted dark:hover:bg-gray-700/50'"
              @click="moveToFolder(folder.id)"
            >
              <div class="w-7 h-7 rounded-lg bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center flex-shrink-0">
                <svg class="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
              </div>
              <span class="flex-1 min-w-0 text-sm font-medium text-text-default truncate">{{ folder.name }}</span>
              <span class="flex-shrink-0 text-xs text-text-subtle">{{ folder.document_count }}</span>
              <svg
                v-if="document.folder_id === folder.id"
                class="w-4 h-4 text-blue-500 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            </button>

            <div v-if="!folderStore.folders.length" class="text-center py-4">
              <p class="text-sm text-text-muted">No hay carpetas creadas.</p>
            </div>
          </div>

          <!-- Error -->
          <div v-if="errorMsg" class="px-4 pb-2">
            <p class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">{{ errorMsg }}</p>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-border-muted flex justify-end">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-text-muted hover:text-text-default dark:text-text-subtle dark:hover:text-gray-100 hover:bg-surface-raised dark:hover:bg-gray-700 rounded-lg transition-colors"
              @click="close"
            >
              Cancelar
            </button>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  document: { type: Object, default: null },
});
const emit = defineEmits(['update:modelValue', 'changed']);

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const isMoving = ref(false);
const errorMsg = ref('');

function close() {
  emit('update:modelValue', false);
}

async function moveToFolder(folderId) {
  if (!props.document) return;
  if (props.document.folder_id === folderId) {
    close();
    return;
  }
  isMoving.value = true;
  errorMsg.value = '';
  const result = await documentStore.updateDocument(props.document.id, { folder_id: folderId });
  isMoving.value = false;
  if (result.success) {
    emit('changed');
    close();
  } else {
    errorMsg.value = 'No se pudo mover el documento.';
  }
}
</script>
