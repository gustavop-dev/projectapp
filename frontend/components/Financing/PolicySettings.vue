<script setup>
import { computed, ref, watch } from 'vue'

import ConfirmModal from '~/components/ConfirmModal.vue'
import { useConfirmModal } from '~/composables/useConfirmModal'
import { usePanelNotify } from '~/composables/usePanelNotify'
import { useFinancingAgreementsStore } from '~/stores/financing_agreements'

const props = defineProps({
  settings: { type: Object, default: null },
})
const emit = defineEmits(['published'])

const { locale, t } = useI18n()
const store = useFinancingAgreementsStore()
const notify = usePanelNotify()
const errors = ref({})
const form = ref({})
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal()

function resetForm() {
  const policy = props.settings?.current
  if (!policy) return
  form.value = {
    minimum_project_value_cop: String(policy.minimum_project_value_cop),
    maximum_project_value_cop: String(policy.maximum_project_value_cop),
    financing_months: String(policy.financing_months),
    maximum_financed_percent: String(policy.maximum_financed_percent),
    late_hosting_increase_percent: String(policy.late_hosting_increase_percent),
    installment_due_day_start: String(policy.installment_due_day_start),
    installment_due_day_end: String(policy.installment_due_day_end),
  }
  errors.value = {}
}

watch(() => props.settings?.current, resetForm, { immediate: true })

const minimumInitialPercent = computed(() => {
  const financed = Number(form.value.maximum_financed_percent)
  return Number.isFinite(financed) ? Math.max(100 - financed, 0) : 0
})

function fieldError(field) {
  const value = errors.value[field]
  return Array.isArray(value) ? value[0] : (value || '')
}

function validate() {
  const next = {}
  const minimum = Number(form.value.minimum_project_value_cop)
  const maximum = Number(form.value.maximum_project_value_cop)
  const months = Number(form.value.financing_months)
  const financed = Number(form.value.maximum_financed_percent)
  const surcharge = Number(form.value.late_hosting_increase_percent)
  const dueStart = Number(form.value.installment_due_day_start)
  const dueEnd = Number(form.value.installment_due_day_end)
  if (!(minimum > 0)) next.minimum_project_value_cop = t('financing.settings.validation.minimum')
  if (!(maximum > minimum)) next.maximum_project_value_cop = t('financing.settings.validation.maximum')
  if (!Number.isInteger(months) || months < 1 || months > 36) next.financing_months = t('financing.settings.validation.months')
  if (!(financed >= 1 && financed <= 99)) next.maximum_financed_percent = t('financing.settings.validation.financedPercent')
  if (!(surcharge >= 0 && surcharge <= 100)) next.late_hosting_increase_percent = t('financing.settings.validation.surcharge')
  if (!Number.isInteger(dueStart) || dueStart < 1 || dueStart > 28) next.installment_due_day_start = t('financing.settings.validation.dueStart')
  if (!Number.isInteger(dueEnd) || dueEnd < dueStart || dueEnd > 28) next.installment_due_day_end = t('financing.settings.validation.dueEnd')
  errors.value = next
  return Object.keys(next).length === 0
}

async function publish() {
  if (!validate()) return
  const confirmed = await requestConfirm({
    title: t('financing.settings.confirmTitle'),
    message: t('financing.settings.confirmBody'),
    confirmText: t('financing.settings.publish'),
    cancelText: t('financing.settings.cancel'),
    variant: 'warning',
  })
  if (!confirmed) return
  const result = await store.publishSettings({ ...form.value })
  if (!result.success) {
    errors.value = result.errors || {}
    notify.error({ title: result.errors?.detail || t('financing.settings.publishError') })
    return
  }
  notify.success({ title: t('financing.settings.publishSuccess', { version: result.data.current.version }) })
  emit('published', result.data)
}

function formatMoney(value) {
  return new Intl.NumberFormat(locale.value.startsWith('en') ? 'en-US' : 'es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  }).format(Number(value || 0))
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value.startsWith('en') ? 'en-US' : 'es-CO', {
    dateStyle: 'medium', timeStyle: 'short',
  }).format(new Date(value))
}
</script>

<template>
  <div class="mt-6 space-y-6" data-testid="financing-settings-panel">
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

    <BaseAlert variant="info">
      <p class="font-medium">{{ t('financing.settings.revisionNoticeTitle') }}</p>
      <p class="mt-1 text-sm">{{ t('financing.settings.revisionNoticeBody') }}</p>
    </BaseAlert>

    <section v-if="settings?.current" class="rounded-2xl border border-border-default bg-surface p-5 sm:p-6">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest text-text-brand">{{ t('financing.settings.eyebrow') }}</p>
          <h2 class="mt-1 text-lg font-medium text-text-default">{{ t('financing.settings.title') }}</h2>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-text-subtle">{{ t('financing.settings.description') }}</p>
        </div>
        <BaseBadge variant="success">{{ t('financing.settings.currentVersion', { version: settings.current.version }) }}</BaseBadge>
      </div>

      <form class="mt-6" novalidate @submit.prevent="publish">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <BaseFormField :label="t('financing.settings.minimumValue')" required :error="fieldError('minimum_project_value_cop')">
            <BaseInput v-model="form.minimum_project_value_cop" type="number" min="0" step="1" data-testid="financing-settings-minimum" />
          </BaseFormField>
          <BaseFormField :label="t('financing.settings.maximumValue')" required :error="fieldError('maximum_project_value_cop')">
            <BaseInput v-model="form.maximum_project_value_cop" type="number" min="0" step="1" data-testid="financing-settings-maximum" />
          </BaseFormField>
          <BaseFormField :label="t('financing.settings.months')" required :error="fieldError('financing_months')">
            <BaseInput v-model="form.financing_months" type="number" min="1" max="36" step="1" data-testid="financing-settings-months" />
          </BaseFormField>
          <BaseFormField :label="t('financing.settings.maximumFinanced')" required :error="fieldError('maximum_financed_percent')">
            <BaseInput v-model="form.maximum_financed_percent" type="number" min="1" max="99" step="0.01" data-testid="financing-settings-financed-percent" />
          </BaseFormField>
          <BaseFormField :label="t('financing.settings.minimumInitial')" :hint="t('financing.settings.derivedField')">
            <BaseInput :model-value="`${minimumInitialPercent.toFixed(2)}%`" readonly data-testid="financing-settings-minimum-initial" />
          </BaseFormField>
          <BaseFormField :label="t('financing.settings.lateSurcharge')" required :error="fieldError('late_hosting_increase_percent')">
            <BaseInput v-model="form.late_hosting_increase_percent" type="number" min="0" max="100" step="0.01" data-testid="financing-settings-surcharge" />
          </BaseFormField>
          <BaseFormField :label="t('financing.settings.dueStart')" required :error="fieldError('installment_due_day_start')">
            <BaseInput v-model="form.installment_due_day_start" type="number" min="1" max="28" step="1" data-testid="financing-settings-due-start" />
          </BaseFormField>
          <BaseFormField :label="t('financing.settings.dueEnd')" required :error="fieldError('installment_due_day_end')">
            <BaseInput v-model="form.installment_due_day_end" type="number" min="1" max="28" step="1" data-testid="financing-settings-due-end" />
          </BaseFormField>
          <BaseFormField :label="t('financing.settings.usdRate')" :hint="t('financing.settings.usdRateHint')">
            <BaseInput :model-value="formatMoney(settings.usd_exchange_rate)" readonly data-testid="financing-settings-usd-rate" />
          </BaseFormField>
        </div>

        <BaseAlert v-if="errors.non_field_errors" class="mt-5" variant="danger" role="alert">
          {{ fieldError('non_field_errors') }}
        </BaseAlert>

        <div class="mt-6 flex flex-wrap justify-end gap-2">
          <BaseButton type="button" variant="secondary" @click="resetForm">{{ t('financing.settings.reset') }}</BaseButton>
          <BaseButton type="submit" :loading="store.isSaving" data-testid="financing-settings-publish">{{ t('financing.settings.publish') }}</BaseButton>
        </div>
      </form>
    </section>

    <section class="grid gap-4 md:grid-cols-2">
      <article class="rounded-2xl border border-border-default bg-surface p-5">
        <h2 class="text-base font-medium text-text-default">{{ t('financing.settings.fixedTitle') }}</h2>
        <ul class="mt-4 space-y-2 text-sm leading-6 text-text-subtle">
          <li>{{ t('financing.settings.fixedInterest') }}</li>
          <li>{{ t('financing.settings.fixedFiveYear') }}</li>
          <li>{{ t('financing.settings.fixedThreeYear') }}</li>
          <li>{{ t('financing.settings.fixedPackage') }}</li>
        </ul>
      </article>
      <article class="rounded-2xl border border-border-default bg-surface p-5">
        <h2 class="text-base font-medium text-text-default">{{ t('financing.settings.impactTitle') }}</h2>
        <p class="mt-3 text-sm leading-6 text-text-subtle">{{ t('financing.settings.impactBody') }}</p>
      </article>
    </section>

    <section class="rounded-2xl border border-border-default bg-surface p-5 sm:p-6">
      <h2 class="text-lg font-medium text-text-default">{{ t('financing.settings.historyTitle') }}</h2>
      <p class="mt-1 text-sm text-text-subtle">{{ t('financing.settings.historyDescription') }}</p>
      <div class="mt-5 overflow-x-auto">
        <table class="min-w-full divide-y divide-border-default text-left text-sm">
          <thead class="text-xs uppercase tracking-wide text-text-subtle">
            <tr>
              <th class="px-3 py-2">{{ t('financing.settings.historyVersion') }}</th>
              <th class="px-3 py-2">{{ t('financing.settings.historyRange') }}</th>
              <th class="px-3 py-2">{{ t('financing.settings.historyTerms') }}</th>
              <th class="px-3 py-2">{{ t('financing.settings.historyPublished') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border-muted">
            <tr v-for="revision in settings?.history || []" :key="revision.id">
              <td class="px-3 py-3 font-medium text-text-brand">v{{ revision.version }}</td>
              <td class="px-3 py-3 text-text-default">{{ formatMoney(revision.minimum_project_value_cop) }} – {{ formatMoney(revision.maximum_project_value_cop) }}</td>
              <td class="px-3 py-3 text-text-subtle">{{ t('financing.settings.historyTermsValue', { months: revision.financing_months, financed: Number(revision.maximum_financed_percent), surcharge: Number(revision.late_hosting_increase_percent), start: revision.installment_due_day_start, end: revision.installment_due_day_end }) }}</td>
              <td class="px-3 py-3 text-text-subtle">{{ revision.created_by_name }} · {{ formatDate(revision.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
