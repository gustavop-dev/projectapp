<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="close"
      >
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 dark:bg-gray-800">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Gestionar carpetas</h3>
            <button type="button" class="text-gray-400 hover:text-gray-600" @click="close">✕</button>
          </div>

          <!-- New folder form -->
          <form class="flex gap-2 mb-4" @submit.prevent="handleCreate">
            <input
              v-model="newName"
              type="text"
              placeholder="Nombre de la nueva carpeta"
              class="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
            />
            <button
              type="submit"
              :disabled="!newName.trim() || folderStore.isUpdating"
              class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
            >
              Crear
            </button>
          </form>

          <!-- Folder list -->
          <div class="max-h-80 overflow-y-auto">
            <div v-if="!folderStore.folders.length" class="text-sm text-gray-500 dark:text-gray-400 text-center py-6">
              No hay carpetas todavía.
            </div>
            <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700">
              <li v-for="folder in folderStore.folders" :key="folder.id" class="py-2 flex items-center gap-2">
                <input
                  v-if="editingId === folder.id"
                  v-model="editingName"
                  type="text"
                  class="flex-1 px-2 py-1 border border-gray-200 rounded text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
                  @keyup.enter="commitRename(folder)"
                />
                <span v-else class="flex-1 text-sm text-gray-800 dark:text-gray-200 truncate">{{ folder.name }}</span>

                <span class="text-xs text-gray-400">{{ folder.document_count }}</span>

                <button
                  v-if="editingId === folder.id"
                  type="button"
                  class="text-xs text-emerald-600 hover:text-emerald-700"
                  @click="commitRename(folder)"
                >
                  Guardar
                </button>
                <button
                  v-else
                  type="button"
                  class="text-xs text-gray-500 hover:text-emerald-600"
                  @click="startRename(folder)"
                >
                  Renombrar
                </button>
                <button
                  type="button"
                  class="text-xs text-gray-500 hover:text-red-600"
                  @click="handleDelete(folder)"
                >
                  Eliminar
                </button>
              </li>
            </ul>
          </div>

          <p v-if="errorMsg" class="text-xs text-red-600 mt-3">{{ errorMsg }}</p>

          <div class="flex justify-end mt-4">
            <button
              type="button"
              class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 dark:text-gray-300"
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
const errorMsg = ref('');

watch(() => props.modelValue, async (open) => {
  if (open) {
    errorMsg.value = '';
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
}

async function commitRename(folder) {
  const name = editingName.value.trim();
  if (!name || name === folder.name) {
    editingId.value = null;
    return;
  }
  const result = await folderStore.updateFolder(folder.id, { name });
  if (result.success) {
    editingId.value = null;
    emit('changed');
  } else {
    errorMsg.value = formatErr(result.errors) || 'No se pudo renombrar.';
  }
}

async function handleDelete(folder) {
  const msg = folder.document_count
    ? `¿Eliminar "${folder.name}"? Sus ${folder.document_count} documento(s) quedarán sin carpeta.`
    : `¿Eliminar "${folder.name}"?`;
  if (!window.confirm(msg)) return;
  const result = await folderStore.deleteFolder(folder.id);
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
