<script setup>
import { onMounted, ref } from 'vue'
import { TrashIcon, PlusIcon } from '@heroicons/vue/24/outline'
import ConfirmModal from '~/components/ConfirmModal.vue'
import { useConfirmModal } from '~/composables/useConfirmModal'
import { usePanelNotify } from '~/composables/usePanelNotify'
import { useAccountingStore } from '~/stores/accounting'

const store = useAccountingStore()
const notify = usePanelNotify()
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal()

// Editable copies of the catalog rows; `id: null` marks an unsaved card.
const rows = ref([])
const savingId = ref(null)
let draftKey = 0

function toRow(record) {
  return {
    id: record.id,
    key: `card-${record.id}`,
    name: record.name,
    credit_limit: record.credit_limit != null ? Number(record.credit_limit) : null,
    is_active: Boolean(record.is_active),
    statements_since: record.statements_since
      ? String(record.statements_since).slice(0, 7)
      : '',
  }
}

function syncRows() {
  rows.value = store.creditCards.map(toRow)
}

async function load() {
  const result = await store.fetchRecords('creditCards')
  if (result.success) syncRows()
}

onMounted(load)

function addRow() {
  rows.value.push({
    id: null,
    key: `draft-${++draftKey}`,
    name: '',
    credit_limit: null,
    is_active: true,
    statements_since: '',
  })
}

function removeDraft(row) {
  rows.value = rows.value.filter((item) => item.key !== row.key)
}

function buildPayload(row) {
  return {
    name: row.name.trim(),
    credit_limit: row.credit_limit,
    is_active: row.is_active,
    statements_since: row.statements_since || null,
  }
}

async function saveRow(row) {
  if (!row.name.trim() || !row.credit_limit || Number(row.credit_limit) <= 0) {
    notify.error('La tarjeta necesita nombre y un cupo mayor a cero.')
    return
  }
  savingId.value = row.key
  const payload = buildPayload(row)
  const result = row.id
    ? await store.updateRecord('creditCards', row.id, payload)
    : await store.createRecord('creditCards', payload)
  savingId.value = null
  if (result.success) {
    notify.success(row.id ? 'Tarjeta actualizada.' : 'Tarjeta agregada.')
    syncRows()
  } else {
    notify.error({
      title: 'No se pudo guardar la tarjeta',
      detail: result.message,
    })
  }
}

function requestDelete(row) {
  if (!row.id) {
    removeDraft(row)
    return
  }
  requestConfirm({
    title: 'Eliminar tarjeta',
    message: `¿Eliminar "${row.name}" del catálogo? Si tiene registros o extractos asociados, el sistema pedirá desactivarla en su lugar.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const result = await store.deleteRecord('creditCards', row.id)
      if (result.success) {
        notify.success('Tarjeta eliminada.')
        syncRows()
      } else {
        notify.error({
          title: 'No se pudo eliminar la tarjeta',
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

    <p v-if="rows.length === 0" class="text-sm text-text-subtle mb-3">
      No hay tarjetas en el catálogo.
    </p>
    <div v-else class="space-y-3 mb-3">
      <div
        v-for="row in rows"
        :key="row.key"
        class="rounded-lg border border-border-muted p-3 space-y-3"
        :data-testid="`card-catalog-row-${row.key}`"
      >
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <BaseFormField label="Nombre" required>
            <BaseInput
              v-model="row.name"
              placeholder="T.C 0064"
              :data-testid="`card-catalog-name-${row.key}`"
            />
          </BaseFormField>
          <BaseFormField label="Cupo" required>
            <BaseCurrencyInput
              v-model="row.credit_limit"
              :data-testid="`card-catalog-limit-${row.key}`"
            />
          </BaseFormField>
          <BaseFormField label="Extractos desde">
            <BaseInput
              v-model="row.statements_since"
              type="month"
              :data-testid="`card-catalog-since-${row.key}`"
            />
          </BaseFormField>
        </div>
        <div class="flex items-center justify-between gap-3">
          <label class="flex items-center gap-2 text-sm text-text-default">
            <BaseToggle
              v-model="row.is_active"
              :aria-label="`Tarjeta ${row.name || 'nueva'} activa`"
            />
            Activa
          </label>
          <div class="flex items-center gap-2">
            <button
              type="button"
              :aria-label="`Eliminar tarjeta ${row.name || 'nueva'}`"
              class="p-2 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors"
              :data-testid="`card-catalog-delete-${row.key}`"
              @click="requestDelete(row)"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
            <BaseButton
              variant="primary"
              size="sm"
              :disabled="savingId === row.key"
              :data-testid="`card-catalog-save-${row.key}`"
              @click="saveRow(row)"
            >
              {{ savingId === row.key ? 'Guardando...' : 'Guardar' }}
            </BaseButton>
          </div>
        </div>
      </div>
    </div>

    <BaseButton
      variant="secondary"
      size="sm"
      data-testid="card-catalog-add"
      @click="addRow"
    >
      <PlusIcon class="w-4 h-4" />
      <span>Agregar tarjeta</span>
    </BaseButton>
  </div>
</template>
