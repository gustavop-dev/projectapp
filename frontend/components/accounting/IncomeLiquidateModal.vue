<script setup>
import { computed, ref, watch } from 'vue'
import PartnerSplitInput from './PartnerSplitInput.vue'
import { formatMoney } from '~/utils/formatMoney'

const props = defineProps({
  open: { type: Boolean, default: false },
  /** The expected income being settled. */
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])

const destinationOptions = [
  { value: 'pocket', label: 'Bolsillo ProjectApp' },
  { value: 'partners', label: 'Socios' },
]

const form = ref(defaultForm())
// Month is enough by default; the toggle records the exact payment day.
const exactDate = ref(false)

function defaultForm() {
  return {
    concept: '',
    period_date: '',
    destination: 'pocket',
    total_amount: '',
    gustavo_amount: '',
    carlos_amount: '',
    notes: '',
  }
}

const isPersonal = computed(() => props.record?.ledger !== 'company')

const pending = computed(() => Number(props.record?.pending_amount ?? 0))

const money = (value) => formatMoney(Number(value ?? 0), 'COP')

watch(
  () => [props.open, props.record],
  () => {
    if (!props.open || !props.record) return
    exactDate.value = false
    form.value = {
      ...defaultForm(),
      concept: props.record.concept ?? '',
      // Default to what is still owed, not the full projection: the whole
      // point of liquidating is that they often pay late and short. The
      // partner split stays empty on purpose — when neither amount is
      // sent, the server applies its canonical 50/50 (split_half).
      total_amount: props.record.pending_amount ?? props.record.total_amount,
    }
  },
  { immediate: true },
)

// Keep whatever was typed when flipping modes: 'YYYY-MM' ⇄ 'YYYY-MM-DD'.
watch(exactDate, (exact) => {
  const value = form.value.period_date
  if (!value) return
  form.value.period_date = exact ? `${value.slice(0, 7)}-01` : value.slice(0, 7)
})

function onSubmit() {
  const payload = {
    concept: form.value.concept,
    kind: 'liquid',
    period_date: form.value.period_date,
    destination: form.value.destination,
    ledger: props.record.ledger,
    total_amount: form.value.total_amount,
    expected_income: props.record.id,
  }
  const { gustavo_amount, carlos_amount } = form.value
  if (!isPersonal.value && gustavo_amount !== '' && carlos_amount !== '') {
    payload.gustavo_amount = gustavo_amount
    payload.carlos_amount = carlos_amount
  }
  payload.notes = form.value.notes
  emit('submit', payload)
}
</script>

<template>
  <BaseModal
    :model-value="open"
    size="lg"
    title-id="income-liquidate-title"
    @close="emit('close')"
  >
    <div class="px-6 pt-6 pb-2">
      <h3 id="income-liquidate-title" class="text-lg font-bold text-text-default">
        Liquidar ingreso esperado
      </h3>
      <p v-if="record" class="text-sm text-text-subtle mt-1">
        Se registrará un ingreso líquido nuevo enlazado a
        <span class="font-medium text-text-default">{{ record.concept }}</span>
        ({{ record.period_label }}, {{ money(record.total_amount) }}). El ingreso
        esperado se conserva.
      </p>
    </div>

    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <div
        v-if="record"
        class="rounded-lg bg-surface-raised px-4 py-3 text-sm text-text-muted"
        data-testid="income-liquidate-pending"
      >
        Pendiente por cobrar:
        <span class="font-medium text-text-default tabular-nums">
          {{ money(pending) }}
        </span>
      </div>

      <BaseFormField label="Concepto" required>
        <BaseInput v-model="form.concept" required />
      </BaseFormField>

      <BaseFormField
        :label="exactDate ? 'Fecha en que se pagó' : 'Mes en que se pagó'"
        required
      >
        <BaseInput
          v-model="form.period_date"
          :type="exactDate ? 'date' : 'month'"
          required
          data-testid="income-liquidate-period"
        />
        <label class="flex items-center gap-2 mt-2 text-xs text-text-subtle">
          <BaseToggle
            v-model="exactDate"
            aria-label="Registrar el día exacto de pago"
            data-testid="income-liquidate-exact-date"
          />
          Registrar el día exacto de pago
        </label>
      </BaseFormField>

      <BaseFormField v-if="!isPersonal" label="Destino">
        <BaseSegmented
          v-model="form.destination"
          :options="destinationOptions"
          full-width
        />
      </BaseFormField>

      <PartnerSplitInput
        v-if="!isPersonal"
        v-model:total="form.total_amount"
        v-model:gustavoAmount="form.gustavo_amount"
        v-model:carlosAmount="form.carlos_amount"
      />

      <BaseFormField v-else label="Valor pagado" required>
        <BaseCurrencyInput v-model="form.total_amount" required />
      </BaseFormField>

      <BaseFormField label="Notas">
        <BaseTextarea v-model="form.notes" :rows="2" />
      </BaseFormField>

      <div class="flex items-center justify-end gap-3 pt-2">
        <BaseButton type="button" variant="secondary" @click="emit('close')">
          Cancelar
        </BaseButton>
        <BaseButton
          type="submit"
          variant="primary"
          :disabled="saving"
          data-testid="income-liquidate-submit"
        >
          {{ saving ? 'Guardando...' : 'Liquidar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
