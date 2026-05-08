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
              <div class="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center">
                <svg class="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              <h3 class="text-base font-semibold text-text-default">Renombrar documento</h3>
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

          <!-- Body -->
          <form class="p-6 space-y-4" @submit.prevent="submit">
            <div>
              <label class="block text-xs text-text-muted mb-1.5">Nuevo nombre</label>
              <input
                ref="inputRef"
                v-model="editingTitle"
                type="text"
                placeholder="Nombre del documento"
                class="bg-input-bg w-full px-3 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm text-text-default focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
                :disabled="isSaving"
                @keyup.esc="close"
              />
            </div>

            <p v-if="errorMsg" class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">
              {{ errorMsg }}
            </p>

            <div class="flex justify-end gap-2 pt-2">
              <button
                type="button"
                class="px-4 py-2 text-sm font-medium text-text-muted hover:text-text-default hover:bg-surface-raised dark:hover:bg-gray-700 rounded-lg transition-colors"
                @click="close"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="px-4 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="!canSubmit || isSaving"
              >
                {{ isSaving ? 'Guardando...' : 'Guardar' }}
              </button>
            </div>
          </form>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  document: { type: Object, default: null },
});
const emit = defineEmits(['update:modelValue', 'changed']);

const documentStore = useDocumentStore();

const editingTitle = ref('');
const isSaving = ref(false);
const errorMsg = ref('');
const inputRef = ref(null);

const canSubmit = computed(() => editingTitle.value.trim().length > 0);

watch(
  () => [props.modelValue, props.document],
  async ([open, doc]) => {
    if (open && doc) {
      editingTitle.value = doc.title || '';
      errorMsg.value = '';
      await nextTick();
      inputRef.value?.focus();
      inputRef.value?.select();
    }
  },
  { immediate: true },
);

function close() {
  emit('update:modelValue', false);
}

async function submit() {
  if (!canSubmit.value || !props.document) return;
  const newTitle = editingTitle.value.trim();
  if (newTitle === props.document.title) {
    close();
    return;
  }
  isSaving.value = true;
  errorMsg.value = '';
  const result = await documentStore.updateDocument(props.document.id, { title: newTitle });
  isSaving.value = false;
  if (result.success) {
    emit('changed');
    close();
  } else {
    errorMsg.value = 'No se pudo renombrar el documento.';
  }
}
</script>
