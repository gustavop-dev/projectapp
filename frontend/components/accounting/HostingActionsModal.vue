<script setup>
import { computed } from 'vue'
import {
  ClockIcon,
  EnvelopeIcon,
  PaperAirplaneIcon,
  PencilSquareIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline'
import BaseButton from '~/components/base/BaseButton.vue'
import BaseModal from '~/components/base/BaseModal.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  billingBusy: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'cycles', 'send-billing', 'emails', 'edit', 'delete'])

const actions = computed(() => {
  const row = props.record
  if (!row) return []
  return [
    {
      id: 'cycles', label: 'Ciclos de pago', icon: ClockIcon, event: 'cycles',
      description: 'Registrar un pago o revisar el histórico.',
    },
    {
      id: 'send-billing', label: 'Enviar cuenta de cobro', icon: PaperAirplaneIcon,
      event: 'send-billing',
      disabled: !row.billing_email || props.billingBusy,
      description: row.billing_email
        ? `Enviar a ${row.billing_email}.`
        : 'Vincula un cliente con correo o agrega un email de facturación.',
    },
    {
      id: 'emails', label: 'Ver correos enviados', icon: EnvelopeIcon, event: 'emails',
    },
    { id: 'edit', label: 'Editar', icon: PencilSquareIcon, event: 'edit' },
    { id: 'delete', label: 'Eliminar', icon: TrashIcon, event: 'delete', danger: true },
  ]
})

function run(action) {
  if (action.disabled || !props.record) return
  emit(action.event, props.record)
  emit('close')
}
</script>

<template>
  <BaseModal
    :model-value="open"
    kind="confirm"
    title-id="hosting-actions-title"
    @close="emit('close')"
  >
    <div data-testid="hosting-actions-modal">
      <header class="border-b border-border-muted px-6 pb-4 pt-6">
        <h3 id="hosting-actions-title" class="text-base font-bold text-text-default">
          {{ record?.domain_url || record?.client_name || `Hosting #${record?.id}` }}
        </h3>
        <p class="mt-1 text-sm text-text-muted">
          {{ record?.client_name || 'Sin cliente' }}
        </p>
      </header>

      <ul class="py-2">
        <li v-for="action in actions" :key="action.id">
          <!-- design-tokens: allow-raw-button -- menu row, not a standalone CTA -->
          <button
            type="button"
            class="flex min-h-11 w-full items-start gap-3 px-6 py-3 text-left text-sm transition-colors"
            :class="[
              action.danger
                ? 'text-danger-strong hover:bg-danger-soft'
                : 'text-text-default hover:bg-surface-raised',
              action.disabled ? 'cursor-not-allowed opacity-50' : '',
            ]"
            :disabled="action.disabled"
            :data-testid="`hosting-${action.id}-${record?.id}`"
            @click="run(action)"
          >
            <component :is="action.icon" class="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <span class="min-w-0">
              <span class="block">{{ action.label }}</span>
              <span v-if="action.description" class="mt-0.5 block text-xs text-text-subtle">
                {{ action.description }}
              </span>
            </span>
          </button>
        </li>
      </ul>

      <div class="border-t border-border-muted px-6 py-4">
        <BaseButton class="w-full" variant="secondary" @click="emit('close')">
          Cerrar
        </BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
