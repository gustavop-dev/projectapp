<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue && document"
        class="fixed inset-0 z-[9990] flex items-end justify-center bg-black/40 p-0 backdrop-blur-sm panel-portrait:items-center panel-portrait:p-4"
        @click.self="close"
      >
        <div class="w-full rounded-t-2xl bg-surface shadow-2xl panel-portrait:max-w-sm panel-portrait:rounded-2xl">
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
              class="w-8 h-8 flex-shrink-0 ml-2 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-muted hover:bg-surface-raised transition-colors"
              @click="close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Actions list -->
          <div class="p-2" data-testid="document-actions-list">
            <component
              :is="action.newTab ? 'a' : 'button'"
              v-for="action in actions"
              :key="action.template ? `${action.event}-${action.template}` : action.event"
              v-bind="action.newTab
                ? { href: editTo, target: '_blank', rel: 'noopener noreferrer', 'data-testid': 'document-open-new-tab' }
                : { type: 'button' }"
              class="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-all active:scale-[0.98] hover:bg-surface-muted"
              :class="action.danger ? 'text-danger-strong hover:bg-danger-soft' : 'text-text-default'"
              @click="trigger(action)"
            >
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                :class="action.danger ? 'bg-danger-soft text-danger-strong' : 'bg-surface-raised text-text-subtle'"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="action.icon" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium">{{ action.label }}</div>
                <div v-if="action.description" class="text-xs text-text-subtle mt-0.5">{{ action.description }}</div>
              </div>
            </component>
          </div>

          <!-- Footer (mobile-only safe area + cancel) -->
          <div class="px-5 py-3 border-t border-border-muted">
            <BaseButton variant="ghost" size="md" class="w-full" @click="close">
              Cancelar
            </BaseButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  document: { type: Object, default: null },
  archived: { type: Boolean, default: false },
  // Dirección del editor, ya resuelta por la página. Llega como prop y no se
  // arma acá porque esta hoja es presentacional: sus specs la montan fuera del
  // contexto de Nuxt, donde `useLocalePath` no existe.
  editTo: { type: String, default: null },
});
const emit = defineEmits([
  'update:modelValue',
  'edit',
  'rename',
  'move',
  'download-pdf',
  'copy-markdown',
  'duplicate',
  'send-email',
  'archive',
  'unarchive',
  'delete',
]);

// La etiqueta de vuelta es "Restaurar", no "Desarchivar": es el término que ya
// usa el tablero de tareas, y además evita que un buscador por substring de
// "Archivar" matchee también la acción inversa.
const ARCHIVE_ACTION = {
  event: 'archive',
  label: 'Archivar',
  description: 'Lo saca de la lista y de los contadores; podrás restaurarlo',
  icon: 'M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4',
};

const UNARCHIVE_ACTION = {
  event: 'unarchive',
  label: 'Restaurar',
  description: 'Lo devuelve a su carpeta original',
  icon: 'M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-7 9V11m0 0l-2.5 2.5M12 11l2.5 2.5',
};

const BASE_ACTIONS = [
  {
    event: 'edit',
    label: 'Editar contenido',
    description: 'Abrir el editor del documento',
    icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
  },
  // Un <a> de verdad, no un botón que llame a window.open: así la acción existe
  // también en pantallas táctiles, donde ctrl+clic no está, y sigue siendo
  // copiable y abrible desde el menú contextual.
  {
    event: 'open-new-tab',
    newTab: true,
    label: 'Abrir en pestaña nueva',
    description: 'Abre el editor en otra pestaña, sin salir de la lista',
    icon: 'M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25',
  },
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
    event: 'download-pdf', template: 'friendly',
    label: 'Descargar PDF · Amigable',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
  },
  {
    event: 'download-pdf', template: 'professional',
    label: 'Descargar PDF · Profesional',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
  },
  {
    event: 'copy-markdown',
    label: 'Copiar markdown',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
  },
  {
    event: 'duplicate',
    label: 'Duplicar',
    icon: 'M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2',
  },
  ARCHIVE_ACTION,
  {
    event: 'delete',
    label: 'Eliminar',
    description: 'Esta acción no se puede deshacer',
    danger: true,
    icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16',
  },
];

const isArchived = computed(() => props.archived || !!props.document?.is_archived);

// Un documento archivado está fuera de circulación: editarlo, renombrarlo,
// moverlo, enviarlo por correo o duplicarlo sería incoherente. Queda lo que
// tiene sentido sobre algo guardado: consultarlo, restaurarlo o borrarlo.
const ARCHIVED_EVENTS = new Set(['download-pdf', 'copy-markdown', 'delete']);

const actions = computed(() => {
  if (isArchived.value) {
    return [
      UNARCHIVE_ACTION,
      ...BASE_ACTIONS.filter((a) => ARCHIVED_EVENTS.has(a.event)),
    ];
  }
  // Sin dirección no hay enlace: una acción que no lleva a ningún lado no se
  // ofrece.
  return BASE_ACTIONS.filter((a) => !a.newTab || props.editTo);
});

function close() {
  emit('update:modelValue', false);
}

function trigger(action) {
  // El enlace navega solo; la hoja únicamente se aparta.
  if (!action.newTab) emit(action.event, action.template);
  close();
}
</script>
