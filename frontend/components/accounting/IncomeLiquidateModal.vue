<script setup>
import { computed, ref, watch } from 'vue'
import PartnerSplitInput from './PartnerSplitInput.vue'
import PeriodDateField from './PeriodDateField.vue'
import { DEDUCTION_TYPE_OPTIONS as deductionOptions } from '~/utils/accountingDeductions'
import { formatMoney } from '~/utils/formatMoney'
import { todayISO } from '~/utils/periodDates'

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
const deductions = ref([])
const followUps = ref([])
const deductionsOpen = ref(false)
const followUpsOpen = ref(false)
// The exact payment day is the default; the toggle downgrades to
// month-only when only the month is known.
const exactDate = ref(true)

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

const sumAmounts = (rows) =>
  rows.reduce((total, row) => total + Number(row.amount || 0), 0)

/** What was invoiced but did not arrive with this payment. */
const shortfall = computed(() =>
  Math.max(pending.value - Number(form.value.total_amount || 0), 0),
)
// An auto-added row the user never touched must not block the submit nor
// reach the payload — otherwise "leave the rest pending" (no allocation)
// would require deleting the row the auto-expand just created.
const isPristineDeduction = (row) =>
  !(Number(row.amount) > 0) && !row.detail.trim() && row.type === 'gateway_fee'

const activeDeductions = computed(() =>
  deductions.value.filter((row) => !isPristineDeduction(row)),
)

const allocated = computed(
  () => sumAmounts(activeDeductions.value) + sumAmounts(followUps.value),
)
/** Left over after allocating; stays pending on the expected income. */
const unassigned = computed(() => shortfall.value - allocated.value)
const overAllocated = computed(() => unassigned.value < 0)

const hasIncompleteRow = computed(() => {
  const badDeduction = activeDeductions.value.some(
    (row) => !(Number(row.amount) > 0)
      || (row.type === 'other' && !row.detail.trim()),
  )
  const badFollowUp = followUps.value.some(
    (row) => !(Number(row.amount) > 0)
      || !row.concept.trim()
      || !row.period_date,
  )
  return badDeduction || badFollowUp
})

const canSubmit = computed(() => !overAllocated.value && !hasIncompleteRow.value)

function addDeduction() {
  deductions.value.push({ type: 'gateway_fee', detail: '', amount: null })
}

function addFollowUp() {
  followUps.value.push({
    concept: `${props.record?.concept ?? ''} - saldo`,
    period_date: '',
    amount: null,
  })
}

// Opening an empty section with no row to fill reads as broken.
watch(deductionsOpen, (open) => {
  if (open && !deductions.value.length) addDeduction()
})
watch(followUpsOpen, (open) => {
  if (open && !followUps.value.length) addFollowUp()
})

// Reveal the resolution path the moment a shortfall appears — the section
// used to materialize with both groups collapsed, which read as "the
// option is not there". One-shot per modal open, so a user who collapses
// the group and keeps editing the amount stays in control.
const autoExpanded = ref(false)
watch(shortfall, (value) => {
  if (value > 0 && !autoExpanded.value) {
    autoExpanded.value = true
    deductionsOpen.value = true
  }
})

watch(
  () => [props.open, props.record],
  () => {
    if (!props.open || !props.record) return
    exactDate.value = true
    deductions.value = []
    followUps.value = []
    deductionsOpen.value = false
    followUpsOpen.value = false
    autoExpanded.value = false
    form.value = {
      ...defaultForm(),
      concept: props.record.concept ?? '',
      // Liquidating records a payment that just happened, so today beats
      // the expected period (which is exactly the stale value).
      period_date: todayISO(),
      // Default to what is still owed, not the full projection: the whole
      // point of liquidating is that they often pay late and short. The
      // partner split stays empty on purpose — when neither amount is
      // sent, the server applies its canonical 50/50 (split_half).
      total_amount: props.record.pending_amount ?? props.record.total_amount,
    }
  },
  { immediate: true },
)

function onSubmit() {
  if (!canSubmit.value) return
  // A cleared BaseCurrencyInput emits null; the server expects 0 for a
  // residual-only settlement (nothing received, shortfall fully allocated).
  const amount = form.value.total_amount
  const payload = {
    concept: form.value.concept,
    period_date: form.value.period_date,
    destination: form.value.destination,
    total_amount: amount === '' || amount == null ? 0 : amount,
    // Empty arrays make the backend behave exactly like a plain liquidation.
    deductions: activeDeductions.value.map((row) => ({
      type: row.type,
      detail: row.type === 'other' ? row.detail.trim() : '',
      amount: row.amount,
    })),
    expected_incomes: followUps.value.map((row) => ({
      concept: row.concept.trim(),
      period_date: row.period_date,
      amount: row.amount,
    })),
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

      <p
        v-if="record && shortfall <= 0"
        class="text-xs text-text-subtle"
        data-testid="income-liquidate-shortfall-hint"
      >
        ¿Recibiste menos? Escribe el monto real: la diferencia podrás
        registrarla como deducción (comisión o retención) o como un nuevo
        ingreso esperado.
      </p>

      <BaseFormField label="Concepto" required>
        <BaseInput v-model="form.concept" required />
      </BaseFormField>

      <PeriodDateField
        v-model="form.period_date"
        v-model:exact="exactDate"
        label-exact="Fecha en que se pagó"
        label-month="Mes en que se pagó"
        toggle-label="Registrar el día exacto de pago"
        required
        input-testid="income-liquidate-period"
        toggle-testid="income-liquidate-exact-date"
      />

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

      <!-- Shortfall: the money that was invoiced but did not arrive. -->
      <section
        v-if="shortfall > 0"
        class="rounded-lg border border-border-muted p-4 space-y-3"
        data-testid="income-liquidate-shortfall"
      >
        <div class="flex items-baseline justify-between gap-3">
          <h4 class="text-sm font-medium text-text-default">Saldo por resolver</h4>
          <span class="text-sm font-medium text-text-default tabular-nums">
            {{ money(shortfall) }}
          </span>
        </div>
        <p class="text-xs text-text-subtle">
          Si el faltante fue una comisión o una retención, regístralo como gasto.
          Si sí lo vas a cobrar después, crea un ingreso esperado nuevo.
        </p>

        <!-- Deduction rows -->
        <button
          type="button"
          class="flex w-full items-center gap-2 text-sm font-medium text-text-default hover:text-text-brand transition-colors"
          :aria-expanded="deductionsOpen"
          aria-controls="liquidate-deductions"
          data-testid="income-liquidate-deductions-toggle"
          @click="deductionsOpen = !deductionsOpen"
        >
          <span class="text-text-subtle">{{ deductionsOpen ? '−' : '+' }}</span>
          No es un cobro pendiente, es un gasto
        </button>
        <BaseCollapse id="liquidate-deductions" :open="deductionsOpen">
          <div class="space-y-2 pt-1">
            <div
              v-for="(row, index) in deductions"
              :key="`deduction-${index}`"
              class="space-y-2 rounded-lg bg-surface-raised p-3"
              :data-testid="`income-liquidate-deduction-${index}`"
            >
              <div class="flex items-start gap-2">
                <BaseSelect
                  v-model="row.type"
                  :options="deductionOptions"
                  class="flex-1"
                  aria-label="Concepto del gasto"
                  :data-testid="`deduction-type-${index}`"
                />
                <BaseCurrencyInput
                  v-model="row.amount"
                  class="w-36"
                  placeholder="Monto"
                  aria-label="Monto del gasto"
                  :data-testid="`deduction-amount-${index}`"
                />
                <BaseButton
                  type="button"
                  variant="ghost"
                  size="sm"
                  aria-label="Quitar gasto"
                  @click="deductions.splice(index, 1)"
                >
                  Quitar
                </BaseButton>
              </div>
              <BaseInput
                v-if="row.type === 'other'"
                v-model="row.detail"
                placeholder="¿Cuál concepto?"
                aria-label="Concepto del gasto"
                :data-testid="`deduction-detail-${index}`"
              />
            </div>
            <BaseButton
              type="button"
              variant="secondary"
              size="sm"
              data-testid="income-liquidate-add-deduction"
              @click="addDeduction"
            >
              Agregar gasto
            </BaseButton>
          </div>
        </BaseCollapse>

        <!-- Follow-up expected incomes -->
        <button
          type="button"
          class="flex w-full items-center gap-2 text-sm font-medium text-text-default hover:text-text-brand transition-colors"
          :aria-expanded="followUpsOpen"
          aria-controls="liquidate-follow-ups"
          data-testid="income-liquidate-followups-toggle"
          @click="followUpsOpen = !followUpsOpen"
        >
          <span class="text-text-subtle">{{ followUpsOpen ? '−' : '+' }}</span>
          Sí lo voy a cobrar: crear ingreso esperado
        </button>
        <BaseCollapse id="liquidate-follow-ups" :open="followUpsOpen">
          <div class="space-y-2 pt-1">
            <div
              v-for="(row, index) in followUps"
              :key="`follow-up-${index}`"
              class="space-y-2 rounded-lg bg-surface-raised p-3"
              :data-testid="`income-liquidate-followup-${index}`"
            >
              <BaseInput
                v-model="row.concept"
                placeholder="Concepto"
                aria-label="Concepto del ingreso esperado"
                :data-testid="`followup-concept-${index}`"
              />
              <div class="flex items-start gap-2">
                <BaseInput
                  v-model="row.period_date"
                  type="month"
                  class="flex-1"
                  aria-label="Mes esperado de cobro"
                  :data-testid="`followup-period-${index}`"
                />
                <BaseCurrencyInput
                  v-model="row.amount"
                  class="w-36"
                  placeholder="Monto"
                  aria-label="Monto esperado"
                  :data-testid="`followup-amount-${index}`"
                />
                <BaseButton
                  type="button"
                  variant="ghost"
                  size="sm"
                  aria-label="Quitar ingreso esperado"
                  @click="followUps.splice(index, 1)"
                >
                  Quitar
                </BaseButton>
              </div>
            </div>
            <BaseButton
              type="button"
              variant="secondary"
              size="sm"
              data-testid="income-liquidate-add-followup"
              @click="addFollowUp"
            >
              Agregar ingreso esperado
            </BaseButton>
          </div>
        </BaseCollapse>

        <p
          class="text-xs tabular-nums"
          :class="overAllocated ? 'text-danger-strong' : 'text-text-subtle'"
          data-testid="income-liquidate-remaining"
        >
          <template v-if="overAllocated">
            Te pasaste por {{ money(-unassigned) }} del saldo disponible.
          </template>
          <template v-else-if="unassigned > 0">
            Sin asignar: {{ money(unassigned) }} — quedará pendiente en este ingreso.
          </template>
          <template v-else>
            Saldo resuelto por completo: el ingreso esperado queda cerrado.
          </template>
        </p>
      </section>

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
          :disabled="saving || !canSubmit"
          data-testid="income-liquidate-submit"
        >
          {{ saving ? 'Guardando...' : 'Liquidar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
