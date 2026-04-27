<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/50" @click="$emit('close')" />

        <div class="relative bg-surface dark:bg-primary rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
          <div class="sticky top-0 bg-surface dark:bg-primary border-b border-border-muted dark:border-white/[0.06] px-6 py-4 rounded-t-2xl z-10 flex items-start justify-between">
            <div>
              <h2 class="text-lg font-semibold text-text-default dark:text-white">Acciones del diagnóstico</h2>
              <p class="text-xs text-text-muted dark:text-green-light/60 mt-1">
                Selecciona una acción para este diagnóstico.
              </p>
            </div>
            <button
              type="button"
              class="text-gray-400 hover:text-text-muted dark:hover:text-white text-sm px-2"
              aria-label="Cerrar"
              @click="$emit('close')"
            >
              ✕
            </button>
          </div>

          <div class="px-4 sm:px-6 py-4 space-y-2">
            <component
              v-for="action in actions"
              :key="action.key"
              :is="action.href ? 'a' : 'button'"
              :href="action.href || null"
              :target="action.href ? '_blank' : null"
              :rel="action.href ? 'noopener' : null"
              :type="action.href ? null : 'button'"
              :data-testid="'diagnostic-action-' + action.key"
              class="w-full flex items-start gap-3 p-3 rounded-xl border border-border-muted dark:border-white/[0.06] hover:bg-gray-50 dark:hover:bg-surface/[0.04] transition-colors text-left"
              @click="handleActionClick(action)"
            >
              <span :class="['inline-block w-2 h-2 mt-2 rounded-full flex-shrink-0', action.dotClass]"></span>
              <span class="flex-1 min-w-0">
                <span class="flex items-center gap-2 flex-wrap">
                  <span class="text-sm font-medium text-text-default dark:text-white">{{ action.label }}</span>
                  <span
                    v-if="action.key === suggestedKey"
                    class="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-primary-soft text-text-brand dark:bg-emerald-500/10 dark:text-emerald-300"
                  >
                    Sugerido
                  </span>
                </span>
                <span class="block text-xs text-text-muted dark:text-green-light/60 mt-0.5">
                  {{ action.description }}
                </span>
              </span>
            </component>

            <p v-if="actions.length === 0" class="text-sm text-text-muted dark:text-green-light/60 text-center py-6">
              No hay acciones disponibles para este diagnóstico.
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';
import { getDiagnosticNextAction } from '~/utils/diagnosticNextAction';

const props = defineProps({
  visible: { type: Boolean, default: false },
  diagnostic: { type: Object, default: () => ({}) },
});

const emit = defineEmits([
  'send', 'resend', 'analyze', 'send-final', 'delete', 'close',
]);

const suggestedKey = computed(() => getDiagnosticNextAction(props.diagnostic)?.key || null);

const TERMINAL = new Set(['accepted', 'rejected', 'finished']);

const actions = computed(() => {
  const d = props.diagnostic || {};
  const status = d.status;
  const transitions = d.available_transitions || [];
  const hasEmail = Boolean(d.client?.email);
  const list = [];

  if (status === 'draft' && hasEmail) {
    list.push({
      key: 'send',
      label: 'Enviar envío inicial',
      description: 'Envía por email el diagnóstico inicial al cliente.',
      dotClass: 'bg-blue-500',
    });
  }
  if (['sent', 'viewed'].includes(status) && hasEmail) {
    list.push({
      key: 'resend',
      label: 'Re-enviar al Cliente',
      description: 'Vuelve a enviar el email del diagnóstico inicial.',
      dotClass: 'bg-blue-500',
    });
  }
  if (transitions.includes('negotiating')) {
    list.push({
      key: 'analyze',
      label: 'Marcar en análisis',
      description: 'Confirma que el cliente autorizó y mueve a Negociación.',
      dotClass: 'bg-amber-500',
    });
  }
  if (status === 'negotiating' && !d.final_sent_at) {
    list.push({
      key: 'send-final',
      label: 'Enviar diagnóstico final',
      description: 'Envía por email el diagnóstico final con el análisis completo.',
      dotClass: 'bg-purple-500',
    });
  }
  if (d.public_url) {
    list.push({
      key: 'preview',
      label: 'Vista previa pública',
      description: 'Abre el diagnóstico en una nueva pestaña tal como lo ve el cliente.',
      dotClass: 'bg-gray-400',
      href: d.public_url,
    });
  }
  if (status && !TERMINAL.has(status)) {
    list.push({
      key: 'delete',
      label: 'Eliminar',
      description: 'Elimina el diagnóstico. Esta acción no se puede deshacer.',
      dotClass: 'bg-red-600',
    });
  }

  return list;
});

function handleActionClick(action) {
  if (!action.href) emit(action.key);
  emit('close');
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
