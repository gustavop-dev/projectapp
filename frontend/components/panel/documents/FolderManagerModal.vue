<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
        @click.self="close"
      >
        <div class="bg-surface rounded-2xl shadow-2xl w-full max-w-xl flex flex-col max-h-[88vh]">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-5 border-b border-border-muted flex-shrink-0">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-xl bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center">
                <svg class="w-5 h-5 text-amber-500 dark:text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-semibold text-text-default">Gestionar carpetas</h3>
                <p class="text-xs text-text-muted mt-0.5">Crea, renombra, elimina o reordena arrastrando</p>
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

          <!-- New folder form -->
          <div class="px-6 pt-5 pb-4 flex-shrink-0">
            <form class="flex gap-2" @submit.prevent="handleCreate">
              <div class="relative flex-1">
                <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
                <input
                  v-model="newName"
                  type="text"
                  placeholder="Nombre de la nueva carpeta..."
                  class="w-full pl-9 pr-3 py-2.5 border border-border-default rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface dark:placeholder-gray-500 transition-colors"
                />
              </div>
              <button
                type="submit"
                :disabled="!newName.trim() || folderStore.isUpdating"
                class="px-4 py-2.5 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary-strong transition-colors disabled:opacity-50 flex-shrink-0"
              >
                Crear
              </button>
            </form>
          </div>

          <div v-if="localFolders.length" class="px-6 pb-2 flex-shrink-0">
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-semibold text-text-subtle uppercase tracking-wider">
                {{ localFolders.length }} carpeta{{ localFolders.length !== 1 ? 's' : '' }}
              </span>
              <div class="flex-1 h-px bg-surface-raised"></div>
              <span class="text-[10px] text-text-subtle flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
                </svg>
                Arrastra para reordenar
              </span>
            </div>
          </div>

          <!-- Folder list -->
          <div class="flex-1 overflow-y-auto px-6 pb-2">
            <div v-if="!localFolders.length" class="flex flex-col items-center justify-center py-12 text-center">
              <div class="w-14 h-14 rounded-2xl bg-surface-raised flex items-center justify-center mb-3">
                <svg class="w-7 h-7 text-text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
              </div>
              <p class="text-sm font-medium text-text-muted dark:text-text-subtle">Sin carpetas todavía</p>
              <p class="text-xs text-text-subtle mt-1">Usa el campo de arriba para crear la primera.</p>
            </div>

            <draggable
              v-else
              v-model="localFolders"
              item-key="id"
              handle=".drag-handle"
              ghost-class="opacity-40"
              chosen-class="ring-2 ring-emerald-400 shadow-lg"
              drag-class="rotate-1"
              class="space-y-1.5 py-1"
              @end="handleReorder"
            >
              <template #item="{ element: folder }">
                <div
                  :key="folder.id"
                  class="group flex items-center gap-3 px-3 py-3 rounded-xl border border-border-muted hover:border-border-default dark:hover:border-gray-600 bg-surface hover:bg-surface-muted dark:hover:bg-gray-700/50 transition-all"
                >
                  <div
                    class="drag-handle flex-shrink-0 w-5 h-5 flex items-center justify-center text-text-subtle dark:text-text-muted hover:text-text-subtle dark:hover:text-text-muted cursor-grab active:cursor-grabbing transition-colors"
                    title="Arrastrar para reordenar"
                  >
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 6a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 13.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 21a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3z" />
                    </svg>
                  </div>

                  <div class="w-7 h-7 rounded-lg bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center flex-shrink-0">
                    <svg class="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                    </svg>
                  </div>

                  <input
                    v-if="editingId === folder.id"
                    v-model="editingName"
                    type="text"
                    class="flex-1 min-w-0 px-2.5 py-1.5 border border-emerald-300 dark:border-emerald-600 rounded-lg text-sm bg-surface focus:ring-2 focus:ring-focus-ring/30 outline-none"
                    @keyup.enter="commitRename(folder)"
                    @keyup.esc="cancelRename"
                  />
                  <span v-else class="flex-1 min-w-0 text-sm font-medium text-text-default truncate">
                    {{ folder.name }}
                  </span>

                  <span
                    v-if="editingId !== folder.id"
                    class="flex-shrink-0 inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1.5 rounded-full bg-surface-raised text-xs font-medium text-text-muted dark:text-text-subtle"
                  >
                    {{ folder.document_count }}
                  </span>

                  <div v-if="editingId === folder.id" class="flex items-center gap-1.5 flex-shrink-0">
                    <button
                      type="button"
                      class="px-3 py-1 text-xs font-medium bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors"
                      @click="commitRename(folder)"
                    >
                      Guardar
                    </button>
                    <button
                      type="button"
                      class="px-3 py-1 text-xs font-medium text-text-muted hover:text-text-default dark:text-text-subtle dark:hover:text-gray-200 transition-colors"
                      @click="cancelRename"
                    >
                      Cancelar
                    </button>
                  </div>

                  <div v-else class="flex items-center gap-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      type="button"
                      class="w-7 h-7 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors"
                      title="Renombrar"
                      @click="startRename(folder)"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="w-7 h-7 flex items-center justify-center rounded-lg text-text-subtle hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
                      title="Eliminar carpeta"
                      @click="askDelete(folder)"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </template>
            </draggable>
          </div>

          <div v-if="errorMsg" class="px-6 pb-2 flex-shrink-0">
            <p class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">{{ errorMsg }}</p>
          </div>

          <Transition name="fade-modal">
            <div
              v-if="deleteVariant"
              class="mx-6 mb-4 flex-shrink-0 rounded-xl border p-4"
              :class="deleteVariant.panel"
            >
              <div class="flex items-start gap-3">
                <div
                  class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                  :class="deleteVariant.iconWrap"
                >
                  <svg class="w-4 h-4" :class="deleteVariant.iconStroke" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold truncate" :class="deleteVariant.title">
                    {{ deleteVariant.titleText }}
                  </p>
                  <p class="text-xs mt-0.5" :class="deleteVariant.body">
                    {{ deleteVariant.bodyText }}
                  </p>
                  <div class="flex items-center gap-2 mt-3">
                    <button
                      v-if="deleteVariant.kind === 'destructive'"
                      type="button"
                      :disabled="folderStore.isUpdating"
                      class="px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                      @click="confirmDelete"
                    >
                      {{ folderStore.isUpdating ? 'Eliminando...' : 'Confirmar eliminación' }}
                    </button>
                    <button
                      type="button"
                      class="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
                      :class="deleteVariant.dismiss"
                      @click="deletingFolder = null"
                    >
                      {{ deleteVariant.dismissText }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </Transition>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-border-muted flex justify-end flex-shrink-0">
            <button
              type="button"
              class="px-5 py-2 text-sm font-medium text-text-muted hover:text-text-default dark:text-text-subtle dark:hover:text-gray-100 hover:bg-surface-raised dark:hover:bg-gray-700 rounded-xl transition-colors"
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
import { computed, ref, watch } from 'vue';
import draggable from 'vuedraggable';

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
const localFolders = ref([]);

watch(() => folderStore.folders, (v) => {
  localFolders.value = [...v];
}, { immediate: true });

watch(() => props.modelValue, async (open) => {
  if (open) {
    errorMsg.value = '';
    deletingFolder.value = null;
    editingId.value = null;
    await folderStore.fetchFolders();
    // folderStore.folders watcher syncs localFolders automatically
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

const deleteVariant = computed(() => {
  const folder = deletingFolder.value;
  if (!folder) return null;
  if (folder.document_count) {
    return {
      kind: 'blocked',
      panel: 'border-amber-200 dark:border-amber-900/50 bg-amber-50 dark:bg-amber-900/20',
      iconWrap: 'bg-amber-100 dark:bg-amber-900/40',
      iconStroke: 'text-amber-600 dark:text-amber-400',
      title: 'text-amber-800 dark:text-amber-200',
      body: 'text-amber-700 dark:text-amber-300',
      titleText: `No se puede eliminar "${folder.name}"`,
      bodyText: `Primero mueve o elimina sus ${folder.document_count} documento(s).`,
      dismiss: 'bg-amber-600 text-white hover:bg-amber-700',
      dismissText: 'Entendido',
    };
  }
  return {
    kind: 'destructive',
    panel: 'border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-900/20',
    iconWrap: 'bg-red-100 dark:bg-red-900/40',
    iconStroke: 'text-red-600 dark:text-red-400',
    title: 'text-red-800 dark:text-red-200',
    body: 'text-red-600 dark:text-red-400',
    titleText: `Eliminar "${folder.name}"`,
    bodyText: 'Esta acción no se puede deshacer.',
    dismiss: 'text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40',
    dismissText: 'Cancelar',
  };
});

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

async function handleReorder() {
  const orderedIds = localFolders.value.map((f) => f.id);
  const result = await folderStore.reorderFolders(orderedIds);
  if (!result.success) {
    errorMsg.value = 'Error al reordenar. Vuelve a intentarlo.';
    await folderStore.fetchFolders();
  }
}

function formatErr(errors) {
  if (!errors) return '';
  if (typeof errors === 'string') return errors;
  return Object.values(errors).flat().join(' · ');
}
</script>
