<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue && document"
        class="fixed inset-0 z-[9990] flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm p-0 sm:p-4"
        @click.self="close"
      >
        <div class="bg-surface w-full sm:max-w-sm rounded-t-2xl sm:rounded-2xl shadow-2xl">
          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-4 border-b border-border-muted">
            <div class="min-w-0">
              <h3 class="text-sm font-semibold text-text-default truncate">{{ document.title }}</h3>
              <p v-if="document.client_name" class="text-xs text-text-subtle mt-0.5 truncate">
                {{ document.client_name }}
              </p>
            </div>
            <button
              type="button"
              class="w-8 h-8 flex-shrink-0 ml-2 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-muted hover:bg-surface-raised dark:hover:bg-gray-700 transition-colors"
              @click="close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Actions list -->
          <div class="p-2">
            <button
              v-for="action in actions"
              :key="action.event"
              type="button"
              class="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-colors hover:bg-surface-muted dark:hover:bg-gray-700/50"
              :class="action.danger ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20' : 'text-text-default'"
              @click="trigger(action.event)"
            >
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                :class="action.danger ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400' : 'bg-surface-raised text-text-subtle'"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="action.icon" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium">{{ action.label }}</div>
                <div v-if="action.description" class="text-xs text-text-subtle mt-0.5">{{ action.description }}</div>
              </div>
            </button>
          </div>

          <!-- Footer (mobile-only safe area + cancel) -->
          <div class="px-5 py-3 border-t border-border-muted">
            <button
              type="button"
              class="w-full px-4 py-2 text-sm font-medium text-text-muted hover:text-text-default hover:bg-surface-raised dark:hover:bg-gray-700 rounded-lg transition-colors"
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
defineProps({
  modelValue: { type: Boolean, default: false },
  document: { type: Object, default: null },
});
const emit = defineEmits([
  'update:modelValue',
  'rename',
  'move',
  'download-pdf',
  'copy-markdown',
  'duplicate',
  'send-email',
  'delete',
]);

const actions = [
  {
    event: 'rename',
    label: 'Renombrar',
    description: 'Cambiar el nombre del documento',
    icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
  },
  {
    event: 'move',
    label: 'Mover a carpeta',
    description: 'Cambiar la carpeta',
    icon: 'M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7zm13 1l3 3-3 3',
  },
  {
    event: 'send-email',
    label: 'Enviar por correo',
    description: 'Componer y enviar correo con el documento',
    icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
  },
  {
    event: 'download-pdf',
    label: 'Descargar PDF',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
  },
  {
    event: 'copy-markdown',
    label: 'Copiar markdown',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
  },
  {
    event: 'duplicate',
    label: 'Duplicar',
    icon: 'M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z',
  },
  {
    event: 'delete',
    label: 'Eliminar',
    description: 'Esta acción no se puede deshacer',
    danger: true,
    icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16',
  },
];

function close() {
  emit('update:modelValue', false);
}

function trigger(eventName) {
  emit(eventName);
  close();
}
</script>
