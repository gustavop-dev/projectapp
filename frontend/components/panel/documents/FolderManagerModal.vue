<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="close"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg dark:bg-gray-800 flex flex-col max-h-[90vh]">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex-shrink-0">
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center">
                <svg class="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
              </div>
              <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">Gestionar carpetas</h3>
            </div>
            <button
              type="button"
              class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              @click="close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- New folder form -->
          <div class="px-6 pt-4 pb-3 flex-shrink-0">
            <form class="flex gap-2" @submit.prevent="handleCreate">
              <div class="relative flex-1">
                <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
                <input
                  v-model="newName"
                  type="text"
                  placeholder="Nombre de la nueva carpeta"
                  class="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
                />
              </div>
              <button
                type="submit"
                :disabled="!newName.trim() || folderStore.isUpdating"
                class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 flex-shrink-0"
              >
                Crear
              </button>
            </form>
          </div>

          <!-- Folder list -->
          <div class="flex-1 overflow-y-auto px-6 pb-2">
            <div v-if="!folderStore.folders.length" class="flex flex-col items-center justify-center py-10 text-center">
              <div class="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-3">
                <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
              </div>
              <p class="text-sm text-gray-500 dark:text-gray-400">No hay carpetas todavía.</p>
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Crea una usando el campo de arriba.</p>
            </div>

            <div v-else class="space-y-1.5 py-1">
              <div
                v-for="folder in folderStore.folders"
                :key="folder.id"
                class="group flex items-center gap-3 px-3 py-2.5 rounded-xl border border-gray-100 dark:border-gray-700 hover:border-gray-200 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-all"
              >
                <div class="w-7 h-7 rounded-lg bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center flex-shrink-0">
                  <svg class="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                  </svg>
                </div>

                <input
                  v-if="editingId === folder.id"
                  v-model="editingName"
                  type="text"
                  class="flex-1 min-w-0 px-2.5 py-1 border border-emerald-300 dark:border-emerald-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-200 focus:ring-2 focus:ring-emerald-500 outline-none"
                  @keyup.enter="commitRename(folder)"
                  @keyup.esc="cancelRename"
                />
                <span v-else class="flex-1 min-w-0 text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                  {{ folder.name }}
                </span>

                <span
                  v-if="editingId !== folder.id"
                  class="flex-shrink-0 inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1.5 rounded-full bg-gray-100 dark:bg-gray-600 text-xs font-medium text-gray-500 dark:text-gray-300"
                >
                  {{ folder.document_count }}
                </span>

                <div v-if="editingId === folder.id" class="flex items-center gap-1.5 flex-shrink-0">
                  <button
                    type="button"
                    class="px-3 py-1 text-xs font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                    @click="commitRename(folder)"
                  >
                    Guardar
                  </button>
                  <button
                    type="button"
                    class="px-3 py-1 text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                    @click="cancelRename"
                  >
                    Cancelar
                  </button>
                </div>

                <div v-else class="flex items-center gap-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    class="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/30 transition-colors"
                    title="Renombrar"
                    @click="startRename(folder)"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
                    title="Eliminar carpeta"
                    @click="askDelete(folder)"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="errorMsg" class="px-6 pb-2 flex-shrink-0">
            <p class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">{{ errorMsg }}</p>
          </div>

          <Transition name="fade-modal">
            <div
              v-if="deletingFolder"
              class="mx-6 mb-4 flex-shrink-0 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-900/20 p-4"
            >
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-red-100 dark:bg-red-900/40 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-red-800 dark:text-red-200 truncate">
                    Eliminar "{{ deletingFolder.name }}"
                  </p>
                  <p class="text-xs text-red-600 dark:text-red-400 mt-0.5">
                    <template v-if="deletingFolder.document_count">
                      Sus {{ deletingFolder.document_count }} documento(s) quedarán sin carpeta.
                    </template>
                    <template v-else>
                      Esta acción no se puede deshacer.
                    </template>
                  </p>
                  <div class="flex items-center gap-2 mt-3">
                    <button
                      type="button"
                      :disabled="folderStore.isUpdating"
                      class="px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                      @click="confirmDelete"
                    >
                      {{ folderStore.isUpdating ? 'Eliminando...' : 'Confirmar eliminación' }}
                    </button>
                    <button
                      type="button"
                      class="px-3 py-1.5 text-xs font-medium text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-lg transition-colors"
                      @click="deletingFolder = null"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </Transition>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-gray-100 dark:border-gray-700 flex justify-end flex-shrink-0">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 dark:text-gray-300 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              @click="close"
            >
              Cerrar
            </button>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'changed']);

const folderStore = useDocumentFolderStore();
const newName = ref('');
const editingId = ref(null);
const editingName = ref('');
const deletingFolder = ref(null);
const errorMsg = ref('');

watch(() => props.modelValue, async (open) => {
  if (open) {
    errorMsg.value = '';
    deletingFolder.value = null;
    editingId.value = null;
    await folderStore.fetchFolders();
  }
});

function close() {
  emit('update:modelValue', false);
}

async function handleCreate() {
  const name = newName.value.trim();
  if (!name) return;
  errorMsg.value = '';
  const result = await folderStore.createFolder({ name });
  if (result.success) {
    newName.value = '';
    emit('changed');
  } else {
    errorMsg.value = formatErr(result.errors) || 'No se pudo crear la carpeta.';
  }
}

function startRename(folder) {
  editingId.value = folder.id;
  editingName.value = folder.name;
  deletingFolder.value = null;
}

function cancelRename() {
  editingId.value = null;
}

async function commitRename(folder) {
  const name = editingName.value.trim();
  if (!name || name === folder.name) {
    cancelRename();
    return;
  }
  errorMsg.value = '';
  const result = await folderStore.updateFolder(folder.id, { name });
  if (result.success) {
    cancelRename();
    emit('changed');
  } else {
    errorMsg.value = formatErr(result.errors) || 'No se pudo renombrar.';
  }
}

function askDelete(folder) {
  deletingFolder.value = folder;
  editingId.value = null;
}

async function confirmDelete() {
  if (!deletingFolder.value) return;
  errorMsg.value = '';
  const result = await folderStore.deleteFolder(deletingFolder.value.id);
  deletingFolder.value = null;
  if (result.success) {
    emit('changed');
  } else {
    errorMsg.value = formatErr(result.errors) || 'No se pudo eliminar.';
  }
}

function formatErr(errors) {
  if (!errors) return '';
  if (typeof errors === 'string') return errors;
  return Object.values(errors).flat().join(' · ');
}
</script>
