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
                <p class="text-xs text-text-muted mt-0.5">Crea subcarpetas, edita, elimina o reordena arrastrando</p>
              </div>
            </div>
            <button
              type="button"
              class="w-8 h-8 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-muted hover:bg-surface-raised transition-colors"
              @click="close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- New folder form -->
          <div class="px-6 pt-5 pb-4 flex-shrink-0 space-y-2">
            <form class="flex gap-2" @submit.prevent="handleCreate">
              <div class="relative flex-1">
                <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
                <input
                  v-model="newName"
                  type="text"
                  placeholder="Nombre de la nueva carpeta..."
                  class="w-full pl-9 pr-3 py-2.5 border border-border-default rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none bg-surface placeholder:text-input-placeholder transition-colors"
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
            <label class="flex items-center gap-2 text-xs text-text-muted">
              <span class="flex-shrink-0">Dentro de:</span>
              <select
                v-model="newParent"
                class="flex-1 min-w-0 px-2.5 py-2 border border-border-default rounded-lg text-sm bg-surface text-text-default focus:ring-2 focus:ring-focus-ring/30 outline-none"
              >
                <option :value="null">Ninguna (carpeta raíz)</option>
                <option v-for="opt in createOptions" :key="opt.id" :value="opt.id">
                  {{ opt.label }}
                </option>
              </select>
            </label>
          </div>

          <div v-if="folderStore.folders.length" class="px-6 pb-2 flex-shrink-0">
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-semibold text-text-subtle uppercase tracking-wider">
                {{ folderStore.folders.length }} carpeta{{ folderStore.folders.length !== 1 ? 's' : '' }}
              </span>
              <div class="flex-1 h-px bg-surface-raised"></div>
              <span class="text-2xs text-text-subtle flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
                </svg>
                Arrastra para reordenar (por nivel)
              </span>
            </div>
          </div>

          <!-- Folder tree -->
          <div class="flex-1 overflow-y-auto px-6 pb-2">
            <div v-if="!folderStore.folders.length" class="flex flex-col items-center justify-center py-12 text-center">
              <div class="w-14 h-14 rounded-2xl bg-surface-raised flex items-center justify-center mb-3">
                <svg class="w-7 h-7 text-text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                </svg>
              </div>
              <p class="text-sm font-medium text-text-muted">Sin carpetas todavía</p>
              <p class="text-xs text-text-subtle mt-1">Usa el campo de arriba para crear la primera.</p>
            </div>

            <FolderManagerTree
              v-else
              :siblings="folderStore.rootFolders"
              :parent-id="null"
              :depth="0"
              :editing-id="editingFolder?.id ?? null"
              :deleting-id="deletingFolder?.id ?? null"
              class="py-1"
              @edit="startEdit"
              @delete="askDelete"
              @reorder="handleReorder"
            />
          </div>

          <!-- Edit panel -->
          <Transition name="fade-modal">
            <div
              v-if="editingFolder"
              class="mx-6 mb-4 flex-shrink-0 rounded-xl border border-primary/20 bg-primary-soft p-4"
            >
              <p class="text-xs font-semibold text-text-brand mb-2">
                Editar "{{ editingFolder.name }}"
              </p>
              <div class="space-y-2">
                <input
                  v-model="editName"
                  type="text"
                  placeholder="Nombre de la carpeta"
                  class="w-full px-2.5 py-2 border border-input-border rounded-lg text-sm bg-surface text-text-default focus:ring-2 focus:ring-focus-ring/30 outline-none"
                  @keyup.enter="commitEdit"
                  @keyup.esc="editingFolder = null"
                />
                <label class="flex items-center gap-2 text-xs text-text-muted">
                  <span class="flex-shrink-0">Carpeta padre:</span>
                  <select
                    v-model="editParent"
                    class="flex-1 min-w-0 px-2.5 py-2 border border-border-default rounded-lg text-sm bg-surface text-text-default focus:ring-2 focus:ring-focus-ring/30 outline-none"
                  >
                    <option :value="null">Ninguna (carpeta raíz)</option>
                    <option v-for="opt in editOptions" :key="opt.id" :value="opt.id">
                      {{ opt.label }}
                    </option>
                  </select>
                </label>
              </div>
              <div class="flex items-center gap-2 mt-3">
                <button
                  type="button"
                  :disabled="folderStore.isUpdating || !editName.trim()"
                  class="px-3 py-1.5 bg-primary text-white text-xs font-medium rounded-lg hover:bg-primary-strong disabled:opacity-50 transition-colors"
                  @click="commitEdit"
                >
                  {{ folderStore.isUpdating ? 'Guardando...' : 'Guardar' }}
                </button>
                <button
                  type="button"
                  class="px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text-default rounded-lg transition-colors"
                  @click="editingFolder = null"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </Transition>

          <div v-if="errorMsg" class="px-6 pb-2 flex-shrink-0">
            <p class="text-xs text-danger-strong bg-danger-soft px-3 py-2 rounded-lg">{{ errorMsg }}</p>
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
              class="px-5 py-2 text-sm font-medium text-text-muted hover:text-text-default hover:bg-surface-raised rounded-xl transition-colors"
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
import FolderManagerTree from '~/components/panel/documents/FolderManagerTree.vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  initialParent: { type: Number, default: null },
});
const emit = defineEmits(['update:modelValue', 'changed']);

const folderStore = useDocumentFolderStore();
const newName = ref('');
const newParent = ref(null);
const editingFolder = ref(null);
const editName = ref('');
const editParent = ref(null);
const deletingFolder = ref(null);
const errorMsg = ref('');

watch(() => props.modelValue, async (open) => {
  if (open) {
    errorMsg.value = '';
    deletingFolder.value = null;
    editingFolder.value = null;
    newName.value = '';
    newParent.value = props.initialParent ?? null;
    await folderStore.fetchFolders();
  }
});

// Lista plana e indentada de carpetas para los <select> de carpeta padre.
function buildFolderOptions(excludeId) {
  const exclude = new Set();
  if (excludeId != null) {
    exclude.add(excludeId);
    folderStore.descendantIdsOf(excludeId).forEach((id) => exclude.add(id));
  }
  const options = [];
  const walk = (parentId, depth) => {
    folderStore.childrenOf(parentId)
      .filter((f) => !exclude.has(f.id))
      .forEach((f) => {
        options.push({ id: f.id, label: `${'   '.repeat(depth)}${f.name}` });
        walk(f.id, depth + 1);
      });
  };
  walk(null, 0);
  return options;
}

const createOptions = computed(() => buildFolderOptions(null));
const editOptions = computed(() => (
  editingFolder.value ? buildFolderOptions(editingFolder.value.id) : []
));

function close() {
  emit('update:modelValue', false);
}

async function handleCreate() {
  const name = newName.value.trim();
  if (!name) return;
  errorMsg.value = '';
  const result = await folderStore.createFolder({ name, parent: newParent.value });
  if (result.success) {
    newName.value = '';
    newParent.value = props.initialParent ?? null;
    emit('changed');
  } else {
    errorMsg.value = formatErr(result.errors) || 'No se pudo crear la carpeta.';
  }
}

function startEdit(folder) {
  editingFolder.value = folder;
  editName.value = folder.name;
  editParent.value = folder.parent ?? null;
  deletingFolder.value = null;
}

async function commitEdit() {
  const name = editName.value.trim();
  if (!editingFolder.value || !name) return;
  errorMsg.value = '';
  const result = await folderStore.updateFolder(editingFolder.value.id, {
    name,
    parent: editParent.value,
  });
  if (result.success) {
    editingFolder.value = null;
    emit('changed');
  } else {
    errorMsg.value = formatErr(result.errors) || 'No se pudo guardar.';
  }
}

function askDelete(folder) {
  deletingFolder.value = folder;
  editingFolder.value = null;
}

const deleteVariant = computed(() => {
  const folder = deletingFolder.value;
  if (!folder) return null;
  if (folder.document_count) {
    return {
      kind: 'blocked',
      panel: 'border-warning-strong/30 bg-warning-soft',
      iconWrap: 'bg-warning-soft',
      iconStroke: 'text-warning-strong',
      title: 'text-warning-strong',
      body: 'text-warning-strong',
      titleText: `No se puede eliminar "${folder.name}"`,
      bodyText: `Primero mueve o elimina sus ${folder.document_count} documento(s).`,
      dismiss: 'bg-amber-600 text-white hover:bg-amber-700',
      dismissText: 'Entendido',
    };
  }
  if (folder.children_count) {
    return {
      kind: 'blocked',
      panel: 'border-warning-strong/30 bg-warning-soft',
      iconWrap: 'bg-warning-soft',
      iconStroke: 'text-warning-strong',
      title: 'text-warning-strong',
      body: 'text-warning-strong',
      titleText: `No se puede eliminar "${folder.name}"`,
      bodyText: `Primero mueve o elimina sus ${folder.children_count} subcarpeta(s).`,
      dismiss: 'bg-amber-600 text-white hover:bg-amber-700',
      dismissText: 'Entendido',
    };
  }
  return {
    kind: 'destructive',
    panel: 'border-danger-strong/30 bg-danger-soft',
    iconWrap: 'bg-danger-soft',
    iconStroke: 'text-danger-strong',
    title: 'text-danger-strong',
    body: 'text-danger-strong',
    titleText: `Eliminar "${folder.name}"`,
    bodyText: 'Esta acción no se puede deshacer.',
    dismiss: 'text-danger-strong hover:bg-danger-soft',
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

async function handleReorder({ orderedIds }) {
  const result = await folderStore.reorderFolders(orderedIds);
  if (!result.success) {
    errorMsg.value = 'Error al reordenar. Vuelve a intentarlo.';
  }
  await folderStore.fetchFolders();
}

function formatErr(errors) {
  if (!errors) return '';
  if (typeof errors === 'string') return errors;
  return Object.values(errors).flat().join(' · ');
}
</script>
