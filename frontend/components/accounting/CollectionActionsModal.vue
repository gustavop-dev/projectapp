<script setup>
import { computed } from 'vue'
import {
  ChatBubbleBottomCenterTextIcon,
  CheckCircleIcon,
  DocumentArrowDownIcon,
  EnvelopeIcon,
  EyeIcon,
  NoSymbolIcon,
  PaperAirplaneIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline'
import BaseButton from '~/components/base/BaseButton.vue'
import BaseModal from '~/components/base/BaseModal.vue'
import { formatMoney } from '~/utils/formatMoney'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  busy: { type: Boolean, default: false },
})

const emit = defineEmits([
  'close', 'detail', 'notes', 'download', 'emails', 'resend',
  'mark-paid', 'cancel', 'delete',
])

const actions = computed(() => {
  const row = props.record
  if (!row) return []

  const list = [
    { id: 'view-detail', label: 'Ver detalle', icon: EyeIcon, event: 'detail' },
  ]

  if (row.notes) {
    list.push({
      id: 'notes', label: 'Ver notas internas', icon: ChatBubbleBottomCenterTextIcon,
      event: 'notes',
    })
  }

  list.push(
    {
      id: 'download-pdf', label: 'Descargar PDF', icon: DocumentArrowDownIcon,
      event: 'download',
    },
    {
      id: 'emails', label: 'Ver correos enviados', icon: EnvelopeIcon,
      event: 'emails',
    },
  )

  if (['issued', 'paid'].includes(row.commercial_status)) {
    list.push({
      id: 'resend', label: 'Reenviar al cliente', icon: PaperAirplaneIcon,
      event: 'resend',
    })
  }

  if (row.commercial_status === 'issued') {
    list.push({
      id: 'mark-paid',
      label: row.income_kind === 'expected' ? 'Registrar pago (liquidar)' : 'Marcar pagada',
      icon: CheckCircleIcon,
      event: 'mark-paid',
    })
  }

  if (['draft', 'issued'].includes(row.commercial_status)) {
    list.push({
      id: 'cancel', label: 'Anular', icon: NoSymbolIcon, event: 'cancel', danger: true,
    })
  }

  if (row.can_delete) {
    list.push({
      id: 'delete', label: 'Eliminar', icon: TrashIcon, event: 'delete', danger: true,
    })
  }

  return list
})

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP')
}

function run(action) {
  if (props.busy || !props.record) return
  emit(action.event, props.record)
  emit('close')
}
</script>

<template>
  <BaseModal
    :model-value="open"
    kind="confirm"
    title-id="collection-actions-title"
    @close="emit('close')"
  >
    <div data-testid="collection-actions-modal">
      <header class="border-b border-border-muted px-6 pb-4 pt-6">
        <h3 id="collection-actions-title" class="text-base font-bold text-text-default">
          {{ record?.public_number || `Cuenta #${record?.id}` }}
        </h3>
        <p class="mt-1 text-sm text-text-muted">
          {{ record?.client_display_name || record?.customer_name || 'Sin cliente' }}
          · <span class="tabular-nums">{{ money(record?.total) }}</span>
        </p>
      </header>

      <ul class="py-2">
        <li v-for="action in actions" :key="action.id">
          <!-- design-tokens: allow-raw-button -- menu row, not a standalone CTA -->
          <button
            type="button"
            class="flex min-h-11 w-full items-center gap-3 px-6 py-3 text-left text-sm transition-colors"
            :class="action.danger
              ? 'text-danger-strong hover:bg-danger-soft'
              : 'text-text-default hover:bg-surface-raised'"
            :disabled="busy"
            :data-testid="`collection-${action.id}-${record?.id}`"
            @click="run(action)"
          >
            <component :is="action.icon" class="h-5 w-5 shrink-0" aria-hidden="true" />
            <span>{{ action.label }}</span>
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
