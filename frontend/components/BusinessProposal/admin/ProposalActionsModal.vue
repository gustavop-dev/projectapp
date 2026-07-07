<template>
  <BaseModal :model-value="visible" size="lg" @update:model-value="(open) => { if (!open) $emit('close') }">
    <div class="sticky top-0 bg-surface border-b border-border-muted px-6 py-4 rounded-t-2xl z-10 flex items-start justify-between">
      <div>
        <h2 class="text-lg font-semibold text-text-default">Acciones de la propuesta</h2>
        <p class="text-xs text-text-muted mt-1">
          Selecciona una acción para esta propuesta.
        </p>
      </div>
      <button
        type="button"
        class="w-11 h-11 -m-2 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-default hover:bg-surface-raised motion-safe:transition-colors motion-safe:duration-fast focus:outline-none focus:ring-2 focus:ring-focus-ring/40"
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
        :data-testid="'proposal-action-' + action.key"
        class="w-full flex items-start gap-3 p-3 rounded-xl border border-border-muted hover:bg-surface-raised motion-safe:transition-colors motion-safe:duration-fast text-left focus:outline-none focus:ring-2 focus:ring-focus-ring/40"
        @click="handleActionClick(action)"
      >
        <span :class="['inline-block w-2 h-2 mt-2 rounded-full flex-shrink-0', action.dotClass]"></span>
        <span class="flex-1 min-w-0">
          <span class="flex items-center gap-2 flex-wrap">
            <span class="text-sm font-medium text-text-default">{{ action.label }}</span>
            <span
              v-if="action.key === suggestedKey"
              class="text-2xs uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-primary-soft text-text-brand"
            >
              Sugerido
            </span>
          </span>
          <span class="block text-xs text-text-muted mt-0.5">
            {{ action.description }}
          </span>
        </span>
      </component>

      <p v-if="actions.length === 0" class="text-sm text-text-muted text-center py-6">
        No hay acciones disponibles para esta propuesta.
      </p>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed } from 'vue';
import BaseModal from '~/components/base/BaseModal.vue';
import { getProposalNextAction } from '~/utils/proposalNextAction';

const props = defineProps({
  visible: { type: Boolean, default: false },
  proposal: { type: Object, default: () => ({}) },
});

const emit = defineEmits([
  'send', 'send-multi', 'resend', 'negotiate', 'approve', 'launch', 'finish', 'reject',
  'discount-offer', 'close',
]);

const suggestedKey = computed(() => getProposalNextAction(props.proposal)?.key || null);

const actions = computed(() => {
  const p = props.proposal || {};
  const status = p.status;
  const transitions = p.available_transitions || [];
  const hasEmail = Boolean(p.client_email);
  const list = [];

  if (status === 'draft' && hasEmail) {
    list.push({
      key: 'send',
      label: 'Enviar al Cliente',
      description: 'Envía por email la propuesta al cliente.',
      dotClass: 'bg-info-strong',
    });
  }
  if (['sent', 'viewed'].includes(status) && hasEmail) {
    list.push({
      key: 'resend',
      label: 'Re-enviar al Cliente',
      description: 'Vuelve a enviar el email manteniendo la misma fecha de expiración.',
      dotClass: 'bg-info-strong',
    });
  }
  if (hasEmail) {
    list.push({
      key: 'send-multi',
      label: 'Enviar varias propuestas como un solo correo',
      description: 'Selecciona otras propuestas del mismo cliente y envíalas en un único email con sus PDFs.',
      dotClass: 'bg-info-strong',
    });
  }
  if (transitions.includes('negotiating')) {
    list.push({
      key: 'negotiate',
      label: 'Pasar a Negociación',
      description: 'Genera el contrato y mueve la propuesta al estado Negociación.',
      dotClass: 'bg-warning-strong',
    });
  }
  if (transitions.includes('accepted')) {
    list.push({
      key: 'approve',
      label: 'Aprobar',
      description: 'Marca la propuesta como aceptada por el cliente.',
      dotClass: 'bg-success-strong',
    });
  }
  if (['accepted', 'negotiating'].includes(status)) {
    list.push({
      key: 'launch',
      label: p.platform_onboarding_completed_at ? 'Re-lanzar a Plataforma' : 'Lanzar a Plataforma',
      description: 'Ejecuta el onboarding: crea proyecto, entregables y requerimientos.',
      dotClass: 'bg-primary',
    });
  }
  if (Number(p.discount_percent) > 0 && hasEmail) {
    list.push({
      key: 'discount-offer',
      label: 'Enviar oferta de descuento',
      description: `Ofrece el descuento del ${p.discount_percent}% al cliente, con previsualización antes de enviar.`,
      dotClass: 'bg-danger-strong',
    });
  }
  if (transitions.includes('finished')) {
    list.push({
      key: 'finish',
      label: 'Marcar como finalizada',
      description: 'Cierra la propuesta como finalizada y notifica al cliente.',
      dotClass: 'bg-primary',
    });
  }
  if (transitions.includes('rejected')) {
    list.push({
      key: 'reject',
      label: 'Rechazar',
      description: 'Registra que la propuesta fue rechazada.',
      dotClass: 'bg-danger-strong',
    });
  }
  if (p.uuid) {
    list.push({
      key: 'preview',
      label: 'Vista previa pública',
      description: 'Abre la propuesta en una nueva pestaña tal como la ve el cliente.',
      dotClass: 'bg-surface-raised border border-border-default',
      href: '/proposal/' + p.uuid + '?preview=1',
    });
  }

  return list;
});

function handleActionClick(action) {
  if (!action.href) emit(action.key);
  emit('close');
}
</script>
