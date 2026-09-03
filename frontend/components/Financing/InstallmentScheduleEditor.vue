<script setup>
import { computed } from 'vue'

const { locale, t } = useI18n()

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  currency: { type: String, default: 'COP' },
  disabled: { type: Boolean, default: false },
  error: { type: [String, Array], default: '' },
  months: { type: Number, default: 12 },
  dueDayStart: { type: Number, default: 1 },
  dueDayEnd: { type: Number, default: 5 },
})

const emit = defineEmits(['update:modelValue'])

const total = computed(() => props.modelValue.reduce(
  (sum, row) => sum + (Number(row.amount) || 0),
  0,
))

const errorText = computed(() => (
  Array.isArray(props.error) ? props.error[0] : props.error
))

function updateRow(index, field, value) {
  const next = props.modelValue.map((row, rowIndex) => (
    rowIndex === index ? { ...row, [field]: value } : row
  ))
  emit('update:modelValue', next)
}

function formatMoney(value) {
  return new Intl.NumberFormat(locale.value.startsWith('en') ? 'en-US' : 'es-CO', {
    style: 'currency',
    currency: props.currency,
    maximumFractionDigits: 2,
  }).format(value || 0)
}
</script>

<template>
  <section class="rounded-2xl border border-border-default bg-surface p-4 sm:p-5" aria-labelledby="financing-schedule-title">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h3 id="financing-schedule-title" class="text-base font-medium text-text-default">{{ t('financing.agreement.schedule.title', { count: months }) }}</h3>
        <p class="mt-1 text-xs leading-5 text-text-subtle">
          {{ t('financing.agreement.schedule.help', { start: dueDayStart, end: dueDayEnd }) }}
        </p>
      </div>
      <p class="shrink-0 text-sm font-medium text-text-brand" data-testid="financing-schedule-total">
        {{ t('financing.agreement.schedule.total', { amount: formatMoney(total) }) }}
      </p>
    </div>

    <p v-if="errorText" class="mt-3 rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger-strong" role="alert">
      {{ errorText }}
    </p>

    <div class="mt-4 space-y-2">
      <div
        v-for="(row, index) in modelValue"
        :key="row.number || index"
        class="grid grid-cols-[2.25rem_minmax(0,1fr)] gap-2 rounded-xl border border-border-muted bg-surface-raised p-3 sm:grid-cols-[2.5rem_minmax(9rem,1fr)_minmax(9rem,1fr)] sm:items-end"
        :data-testid="`financing-installment-${index + 1}`"
      >
        <span class="row-span-2 flex h-9 w-9 items-center justify-center rounded-full bg-primary-soft text-xs font-semibold text-text-brand sm:row-span-1">
          {{ index + 1 }}
        </span>
        <BaseFormField :label="t('financing.agreement.schedule.dueDate')" size="sm">
          <BaseInput
            :model-value="row.due_date"
            type="date"
            size="sm"
            :disabled="disabled"
            :data-testid="`financing-installment-date-${index + 1}`"
            @update:model-value="updateRow(index, 'due_date', $event)"
          />
        </BaseFormField>
        <BaseFormField :label="t('financing.agreement.schedule.amount')" size="sm">
          <BaseInput
            :model-value="row.amount"
            type="number"
            min="0.01"
            step="0.01"
            size="sm"
            :disabled="disabled"
            :data-testid="`financing-installment-amount-${index + 1}`"
            @update:model-value="updateRow(index, 'amount', $event)"
          />
        </BaseFormField>
      </div>
    </div>
  </section>
</template>
