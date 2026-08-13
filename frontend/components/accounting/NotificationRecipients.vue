<script setup>
import { computed, onMounted, ref } from 'vue'
import { TrashIcon, PlusIcon } from '@heroicons/vue/24/outline'
import ConfirmModal from '~/components/ConfirmModal.vue'
import { useConfirmModal } from '~/composables/useConfirmModal'
import { usePanelNotify } from '~/composables/usePanelNotify'
import { useAccountingStore } from '~/stores/accounting'
import { formatDate } from '~/utils/formatDate'

const props = defineProps({
  /**
   * Master switch state (AccountingSettings.notifications_enabled). Owned by
   * the parent page; this component only reads it to warn that the list is
   * moot while everything is paused.
   */
  notificationsEnabled: { type: Boolean, default: true },
})

const store = useAccountingStore()
const notify = usePanelNotify()
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal()

// Draft address being added; `newEmailError` shows serializer feedback
// (bad format, duplicate) inline instead of as a toast that scrolls away.
const newEmail = ref('')
const newEmailError = ref('')
const isAdding = ref(false)
const togglingId = ref(null)

const recipients = computed(() => store.notificationRecipients)
const activeCount = computed(
  () => recipients.value.filter((row) => row.is_active).length,
)

onMounted(() => store.fetchRecords('notificationRecipients'))

async function addRecipient() {
  const email = newEmail.value.trim()
  if (!email) {
    newEmailError.value = 'Escribe un correo.'
    return
  }
  isAdding.value = true
  newEmailError.value = ''
  const result = await store.createRecord('notificationRecipients', { email })
  isAdding.value = false
  if (result.success) {
    newEmail.value = ''
    notify.success('Destinatario agregado.')
    return
  }
  newEmailError.value = result.fieldErrors?.email || result.message
}

async function toggleRecipient(row) {
  togglingId.value = row.id
  const result = await store.updateRecord('notificationRecipients', row.id, {
    is_active: !row.is_active,
  })
  togglingId.value = null
  if (result.success) {
    notify.success(
      result.data.is_active
        ? `${row.email} vuelve a recibir los avisos.`
        : `${row.email} queda pausado: no recibirá avisos.`,
    )
  } else {
    notify.error({
      title: 'No se pudo cambiar el estado',
      detail: result.message,
    })
  }
}

function requestDelete(row) {
  requestConfirm({
    title: 'Quitar destinatario',
    message:
      `¿Quitar ${row.email} de la lista? Dejará de recibir los avisos de ` +
      'cambios contables, la deuda de tarjetas, los extractos, el calendario ' +
      'de cobros y pagos y los pagos de hosting. ' +
      'Si es una pausa temporal, usa el interruptor en vez de quitarlo.',
    variant: 'danger',
    confirmText: 'Quitar',
    onConfirm: async () => {
      const result = await store.deleteRecord('notificationRecipients', row.id)
      if (result.success) {
        notify.success('Destinatario eliminado.')
      } else {
        notify.error({
          title: 'No se pudo eliminar el destinatario',
          detail: result.message,
        })
      }
    },
  })
}
</script>

<template>
  <div>
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />

    <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">
      Destinatarios
    </p>

    <!-- The two ways the automation ends up reaching nobody, told apart so
         the fix is obvious: turn the master switch back on, or activate
         someone. -->
    <BaseAlert
      v-if="!props.notificationsEnabled"
      variant="warning"
      class="mb-3"
      data-testid="recipients-master-off-warning"
    >
      Las notificaciones están desactivadas: no sale ningún correo del módulo,
      sin importar quién esté activo en esta lista.
    </BaseAlert>
    <BaseAlert
      v-else-if="activeCount === 0"
      variant="warning"
      class="mb-3"
      data-testid="recipients-none-active-warning"
    >
      Ningún destinatario activo: la automatización está apagada de hecho y
      nadie se entera de nada. Activa al menos un correo.
    </BaseAlert>

    <p
      v-if="recipients.length === 0"
      class="text-sm text-text-subtle mb-3"
      data-testid="recipients-empty"
    >
      Sin destinatarios registrados.
    </p>
    <ul v-else class="space-y-2 mb-4">
      <li
        v-for="row in recipients"
        :key="row.id"
        class="flex items-center justify-between gap-3 rounded-lg border border-border-muted px-3 py-2"
        :data-testid="`recipients-row-${row.id}`"
      >
        <div class="min-w-0">
          <p
            class="text-sm text-text-default truncate"
            :class="{ 'opacity-60': !row.is_active }"
            :data-testid="`recipients-email-${row.id}`"
          >
            {{ row.email }}
          </p>
          <p class="text-xs text-text-subtle">
            <span :data-testid="`recipients-state-${row.id}`">
              {{ row.is_active ? 'Activo' : 'Pausado' }}
            </span>
            · Alta {{ formatDate(row.created_at) }}
          </p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <BaseToggle
            :model-value="row.is_active"
            :disabled="togglingId === row.id"
            :aria-label="`Enviar avisos a ${row.email}`"
            :data-testid="`recipients-toggle-${row.id}`"
            @update:model-value="toggleRecipient(row)"
          />
          <BaseButton
            variant="danger-ghost"
            size="sm"
            :aria-label="`Quitar ${row.email}`"
            :data-testid="`recipients-remove-${row.id}`"
            @click="requestDelete(row)"
          >
            <TrashIcon class="w-4 h-4" />
          </BaseButton>
        </div>
      </li>
    </ul>

    <BaseFormField label="Agregar correo" :error="newEmailError">
      <div class="flex items-start gap-2">
        <BaseInput
          v-model="newEmail"
          type="email"
          placeholder="correo@dominio.com"
          class="flex-1"
          :error="Boolean(newEmailError)"
          data-testid="recipients-new-email"
          @keyup.enter="addRecipient"
        />
        <BaseButton
          variant="secondary"
          size="md"
          :disabled="isAdding"
          data-testid="recipients-add"
          @click="addRecipient"
        >
          <PlusIcon class="w-4 h-4" />
          <span>{{ isAdding ? 'Agregando...' : 'Agregar' }}</span>
        </BaseButton>
      </div>
    </BaseFormField>
  </div>
</template>
