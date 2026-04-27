<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="close"
      >
        <div class="bg-surface rounded-2xl shadow-2xl max-w-md w-full p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-text-default">Gestionar etiquetas</h3>
            <button type="button" class="text-text-subtle hover:text-text-muted" @click="close">✕</button>
          </div>

          <!-- New tag form -->
          <form class="flex gap-2 mb-4" @submit.prevent="handleCreate">
            <input
              v-model="newName"
              type="text"
              placeholder="Nombre"
              class="flex-1 px-3 py-2 border border-border-default rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 outline-none"
            />
            <select
              v-model="newColor"
              class="px-3 py-2 border border-border-default rounded-lg text-sm"
            >
              <option v-for="c in COLORS" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
            <button
              type="submit"
              :disabled="!newName.trim() || tagStore.isUpdating"
              class="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-strong disabled:opacity-50"
            >
              Crear
            </button>
          </form>

          <!-- Tag list -->
          <div class="max-h-80 overflow-y-auto">
            <div v-if="!tagStore.tags.length" class="text-sm text-text-muted text-center py-6">
              No hay etiquetas todavía.
            </div>
            <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700">
              <li v-for="tag in tagStore.tags" :key="tag.id" class="py-2 flex items-center gap-2">
                <span class="w-3 h-3 rounded-full flex-shrink-0" :class="tagDotClass(tag.color)"></span>

                <input
                  v-if="editingId === tag.id"
                  v-model="editingName"
                  type="text"
                  class="flex-1 px-2 py-1 border border-border-default rounded text-sm"
                  @keyup.enter="commitRename(tag)"
                />
                <span v-else class="flex-1 text-sm text-text-default truncate">{{ tag.name }}</span>

                <select
                  v-if="editingId === tag.id"
                  v-model="editingColor"
                  class="text-xs px-2 py-1 border border-border-default rounded"
                >
                  <option v-for="c in COLORS" :key="c.value" :value="c.value">{{ c.label }}</option>
                </select>

                <button
                  v-if="editingId === tag.id"
                  type="button"
                  class="text-xs text-text-brand hover:text-text-brand"
                  @click="commitRename(tag)"
                >
                  Guardar
                </button>
                <button
                  v-else
                  type="button"
                  class="text-xs text-text-muted hover:text-text-brand"
                  @click="startRename(tag)"
                >
                  Editar
                </button>
                <button
                  type="button"
                  class="text-xs text-text-muted hover:text-red-600"
                  @click="handleDelete(tag)"
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
              class="px-4 py-2 text-sm text-text-muted hover:text-text-default dark:text-text-subtle"
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
import { TAG_COLOR_OPTIONS, tagDotClass } from '~/utils/documentTagColors.js';

const COLORS = TAG_COLOR_OPTIONS;

const props = defineProps({
  modelValue: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'changed']);

const tagStore = useDocumentTagStore();
const newName = ref('');
const newColor = ref('gray');
const editingId = ref(null);
const editingName = ref('');
const editingColor = ref('gray');
const errorMsg = ref('');

watch(() => props.modelValue, async (open) => {
  if (open) {
    errorMsg.value = '';
    await tagStore.fetchTags();
  }
});

function close() { emit('update:modelValue', false); }

async function handleCreate() {
  const name = newName.value.trim();
  if (!name) return;
  errorMsg.value = '';
  const result = await tagStore.createTag({ name, color: newColor.value });
  if (result.success) {
    newName.value = '';
    newColor.value = 'gray';
    emit('changed');
  } else {
    errorMsg.value = formatErr(result.errors) || 'No se pudo crear la etiqueta.';
  }
}

function startRename(tag) {
  editingId.value = tag.id;
  editingName.value = tag.name;
  editingColor.value = tag.color;
}

async function commitRename(tag) {
  const name = editingName.value.trim();
  if (!name) { editingId.value = null; return; }
  const result = await tagStore.updateTag(tag.id, { name, color: editingColor.value });
  if (result.success) {
    editingId.value = null;
    emit('changed');
  } else {
    errorMsg.value = formatErr(result.errors) || 'No se pudo actualizar.';
  }
}

async function handleDelete(tag) {
  if (!window.confirm(`¿Eliminar la etiqueta "${tag.name}"?`)) return;
  const result = await tagStore.deleteTag(tag.id);
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
