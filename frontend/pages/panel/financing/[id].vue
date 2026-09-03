<script setup>
import { computed, onMounted, ref } from 'vue'

import ConfirmModal from '~/components/ConfirmModal.vue'
import InstallmentScheduleEditor from '~/components/Financing/InstallmentScheduleEditor.vue'
import { useConfirmModal } from '~/composables/useConfirmModal'
import { usePanelNotify } from '~/composables/usePanelNotify'
import { useFinancingAgreementsStore } from '~/stores/financing_agreements'

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] })

const route = useRoute()
const localePath = useLocalePath()
const store = useFinancingAgreementsStore()
const notify = usePanelNotify()
const { locale, t } = useI18n()
const errors = ref({})
const actionMode = ref('')
const actionNote = ref('')
const signedFile = ref(null)
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal()

const agreement = computed(() => store.currentAgreement)
const actions = computed(() => new Set(agreement.value?.allowed_actions || []))
const draftPdfUrl = computed(() => `/api/financing/agreements/${route.params.id}/draft-pdf/`)
const signedPdfUrl = computed(() => `/api/financing/agreements/${route.params.id}/signed-pdf/`)
const usesOutdatedPolicy = computed(() => (
  agreement.value
  && store.currentPolicy
  && agreement.value.policy_version !== store.currentPolicy.version
))

onMounted(async () => {
  await Promise.all([
    store.fetchAgreement(route.params.id),
    store.fetchTemplates(),
    store.fetchSettings(),
  ])
})

function firstError(payload) {
  if (!payload || typeof payload !== 'object') return t('financing.agreement.detail.genericError')
  if (payload.detail) return payload.detail
  for (const value of Object.values(payload)) {
    if (Array.isArray(value) && value[0]) return value[0]
    if (typeof value === 'string' && value) return value
  }
  return t('financing.agreement.detail.reviewData')
}

async function saveAgreement(payload) {
  errors.value = {}
  const result = await store.updateAgreement(agreement.value.id, payload)
  if (!result.success) {
    errors.value = result.errors || {}
    notify.error({ title: firstError(result.errors) })
    return
  }
  notify.success({ title: t('financing.agreement.detail.saved') })
}

async function runAction(action, payload = {}) {
  errors.value = {}
  const result = await store.runAction(agreement.value.id, action, payload)
  if (!result.success) {
    errors.value = result.errors || {}
    notify.error({ title: firstError(result.errors) })
    return null
  }
  actionMode.value = ''
  actionNote.value = ''
  notify.success({ title: t('financing.agreement.detail.statusUpdated') })
  return result.data
}

async function simpleAction(action) {
  const messages = {
    'mark-ready': t('financing.agreement.detail.confirmReady'),
    reopen: t('financing.agreement.detail.confirmReopen'),
    archive: t('financing.agreement.detail.confirmArchive'),
    restore: t('financing.agreement.detail.confirmRestore'),
    'create-second-cycle': t('financing.agreement.detail.confirmSecondCycle'),
    'apply-current-policy': t('financing.agreement.detail.confirmApplyPolicy'),
  }
  if (messages[action]) {
    const confirmed = await requestConfirm({
      title: t('financing.agreement.detail.confirmActionTitle'),
      message: messages[action],
      confirmText: t('financing.agreement.detail.confirm'),
      cancelText: t('financing.agreement.detail.cancelConfirmation'),
      variant: 'warning',
    })
    if (!confirmed) return
  }
  const result = await runAction(action)
  if (action === 'create-second-cycle' && result?.id) {
    await navigateTo(localePath(`/panel/financing/${result.id}`))
  }
}

function onFile(event) {
  signedFile.value = event.target.files?.[0] || null
}

async function uploadSigned() {
  if (!signedFile.value) {
    errors.value = { signed_document: [t('financing.agreement.detail.selectSignedPdf')] }
    return
  }
  const result = await store.uploadSigned(agreement.value.id, signedFile.value)
  if (!result.success) {
    errors.value = result.errors || {}
    notify.error({ title: firstError(result.errors) })
    return
  }
  signedFile.value = null
  actionMode.value = ''
  notify.success({ title: t('financing.agreement.detail.signedActivated') })
}

async function submitNoteAction() {
  if (actionMode.value === 'complete') {
    await runAction('complete', { completion_note: actionNote.value })
  } else if (actionMode.value === 'cancel') {
    await runAction('cancel', { cancellation_reason: actionNote.value })
  }
}

function formatMoney(value, currency = 'COP') {
  return new Intl.NumberFormat(locale.value.startsWith('en') ? 'en-US' : 'es-CO', {
    style: 'currency', currency, maximumFractionDigits: 2,
  }).format(Number(value || 0))
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value.startsWith('en') ? 'en-US' : 'es-CO', { dateStyle: 'long' }).format(new Date(value.includes('T') ? value : `${value}T12:00:00`))
}

const knownEventTypes = new Set([
  'created', 'updated', 'marked_ready', 'reopened', 'signed_pdf_registered',
  'completed', 'cancelled', 'archived', 'restored', 'second_cycle_approved',
  'created_second_cycle',
  'policy_revision_applied',
])
const knownHostingPeriods = new Set(['monthly', 'quarterly', 'semiannual', 'annual'])

function eventLabel(eventType) {
  return knownEventTypes.has(eventType)
    ? t(`financing.agreement.events.${eventType}`)
    : eventType
}

function hostingPeriodLabel(period) {
  return knownHostingPeriods.has(period)
    ? t(`financing.agreement.form.hostingPeriods.${period}`)
    : period
}

function modalityLabel(value, fallback = '') {
  if (value === 'five_year') return t('financing.agreement.fiveYearLabel')
  if (value === 'three_year') return t('financing.agreement.threeYearLabel')
  return fallback || value
}
</script>

<template>
  <BasePageShell width="content">
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
    <div v-if="store.isLoading && !agreement" class="flex min-h-80 items-center justify-center" role="status"><span class="h-8 w-8 animate-spin rounded-full border-2 border-border-default border-t-primary" /></div>
    <div v-else-if="store.error && !agreement" class="rounded-xl bg-danger-soft p-6 text-danger-strong" role="alert">{{ t('financing.agreement.detail.loadError') }}</div>
    <template v-else-if="agreement">
      <header class="mb-6">
        <NuxtLink :to="localePath('/panel/financing?tab=agreements')" class="text-sm text-text-brand hover:underline">{{ t('financing.agreement.detail.back') }}</NuxtLink>
        <div class="mt-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h1 class="text-2xl font-light text-text-default">{{ agreement.number || t('financing.agreement.unnumberedDraft') }}</h1>
              <FinancingAgreementStatusBadge :status="agreement.status" :label="agreement.status_label" :archived="agreement.is_archived" />
              <BaseBadge variant="neutral">{{ t('financing.agreement.cycle', { number: agreement.cycle_number }) }}</BaseBadge>
            </div>
            <p class="mt-2 text-sm text-text-subtle">{{ agreement.client_full_name }} · {{ agreement.project_name }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <BaseButton v-if="actions.has('download_draft')" as="a" :to="draftPdfUrl" variant="secondary" data-testid="financing-download-draft">{{ t('financing.agreement.detail.downloadDraft') }}</BaseButton>
            <BaseButton v-if="actions.has('download_signed')" as="a" :to="signedPdfUrl" variant="secondary" data-testid="financing-download-signed">{{ t('financing.agreement.detail.downloadSigned') }}</BaseButton>
          </div>
        </div>
      </header>

      <BaseAlert v-if="Object.keys(errors).length" class="mb-5" variant="danger" role="alert">
        <p class="font-medium">{{ t('financing.agreement.detail.operationReview') }}</p>
        <p class="mt-1 text-sm">{{ firstError(errors) }}</p>
      </BaseAlert>

      <BaseAlert
        class="mb-5"
        :variant="usesOutdatedPolicy ? 'warning' : 'info'"
        data-testid="financing-agreement-policy"
      >
        <p class="font-medium">
          {{ usesOutdatedPolicy
            ? t('financing.agreement.detail.outdatedPolicyTitle', { version: agreement.policy_version, current: store.currentPolicy?.version })
            : t('financing.agreement.detail.policyTitle', { version: agreement.policy_version }) }}
        </p>
        <p class="mt-1 text-sm">
          {{ usesOutdatedPolicy
            ? t('financing.agreement.detail.outdatedPolicyBody')
            : t('financing.agreement.detail.policyBody') }}
        </p>
      </BaseAlert>

      <section class="mb-6 rounded-2xl border border-border-default bg-surface p-4 sm:p-5" :aria-label="t('financing.agreement.detail.actionsLabel')">
        <div class="flex flex-wrap gap-2">
          <BaseButton v-if="actions.has('mark_ready')" data-testid="financing-mark-ready" @click="simpleAction('mark-ready')">{{ t('financing.agreement.detail.markReady') }}</BaseButton>
          <BaseButton v-if="actions.has('reopen')" variant="secondary" data-testid="financing-reopen" @click="simpleAction('reopen')">{{ t('financing.agreement.detail.reopen') }}</BaseButton>
          <BaseButton v-if="actions.has('upload_signed')" data-testid="financing-open-upload" @click="actionMode = 'upload'">{{ t('financing.agreement.detail.registerSigned') }}</BaseButton>
          <BaseButton v-if="actions.has('complete')" data-testid="financing-open-complete" @click="actionMode = 'complete'">{{ t('financing.agreement.detail.complete') }}</BaseButton>
          <BaseButton v-if="actions.has('create_second_cycle')" data-testid="financing-create-second-cycle" @click="simpleAction('create-second-cycle')">{{ t('financing.agreement.detail.approveSecondCycle') }}</BaseButton>
          <BaseButton v-if="actions.has('apply_current_policy')" variant="secondary" data-testid="financing-apply-current-policy" @click="simpleAction('apply-current-policy')">{{ t('financing.agreement.detail.applyCurrentPolicy') }}</BaseButton>
          <BaseButton v-if="actions.has('cancel')" variant="danger" data-testid="financing-open-cancel" @click="actionMode = 'cancel'">{{ t('financing.agreement.detail.cancelAgreement') }}</BaseButton>
          <BaseButton v-if="actions.has('archive')" variant="secondary" data-testid="financing-archive" @click="simpleAction('archive')">{{ t('financing.agreement.detail.archive') }}</BaseButton>
          <BaseButton v-if="actions.has('restore')" variant="secondary" data-testid="financing-restore" @click="simpleAction('restore')">{{ t('financing.agreement.detail.restore') }}</BaseButton>
        </div>

        <div v-if="actionMode === 'upload'" class="mt-4 rounded-xl border border-border-default bg-surface-raised p-4" data-testid="financing-upload-panel">
          <BaseFormField :label="t('financing.agreement.detail.signedPdf')" required :error="errors.signed_document?.[0] || ''">
            <input type="file" accept="application/pdf,.pdf" class="block w-full text-sm text-text-default" data-testid="financing-signed-file" @change="onFile">
          </BaseFormField>
          <p class="mt-2 text-xs text-text-subtle">{{ t('financing.agreement.detail.privatePdfHelp') }}</p>
          <div class="mt-4 flex justify-end gap-2"><BaseButton variant="secondary" size="sm" @click="actionMode = ''">{{ t('financing.agreement.detail.close') }}</BaseButton><BaseButton size="sm" :loading="store.isSaving" data-testid="financing-upload-signed" @click="uploadSigned">{{ t('financing.agreement.detail.registerAndActivate') }}</BaseButton></div>
        </div>

        <div v-if="actionMode === 'complete' || actionMode === 'cancel'" class="mt-4 rounded-xl border border-border-default bg-surface-raised p-4">
          <BaseFormField :label="actionMode === 'complete' ? t('financing.agreement.detail.completionLabel') : t('financing.agreement.detail.cancellationLabel')" required :error="errors.completion_note?.[0] || errors.cancellation_reason?.[0] || ''">
            <BaseTextarea v-model="actionNote" rows="3" :placeholder="actionMode === 'complete' ? t('financing.agreement.detail.completionPlaceholder') : t('financing.agreement.detail.cancellationPlaceholder')" data-testid="financing-action-note" />
          </BaseFormField>
          <div class="mt-4 flex justify-end gap-2"><BaseButton variant="secondary" size="sm" @click="actionMode = ''">{{ t('financing.agreement.detail.close') }}</BaseButton><BaseButton :variant="actionMode === 'cancel' ? 'danger' : 'primary'" size="sm" :loading="store.isSaving" data-testid="financing-confirm-note-action" @click="submitNoteAction">{{ t('financing.agreement.detail.confirm') }}</BaseButton></div>
        </div>
      </section>

      <FinancingAgreementForm
        v-if="actions.has('edit')"
        :agreement="agreement"
        :templates="store.templates"
        :policy="store.currentPolicy"
        :exchange-rate="store.financingSettings?.usd_exchange_rate"
        :saving="store.isSaving"
        :errors="errors"
        @submit="saveAgreement"
        @cancel="navigateTo(localePath('/panel/financing?tab=agreements'))"
      />

      <div v-else class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div class="space-y-6">
          <section class="rounded-2xl border border-border-default bg-surface p-5 sm:p-6">
            <h2 class="text-lg font-medium text-text-default">{{ t('financing.agreement.detail.summaryTitle') }}</h2>
            <dl class="mt-5 grid gap-4 sm:grid-cols-2">
              <div><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.originalContract') }}</dt><dd class="mt-1 text-sm text-text-default">{{ agreement.original_contract_reference }} · {{ formatDate(agreement.original_contract_date) }}</dd></div>
              <div><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.modality') }}</dt><dd class="mt-1 text-sm text-text-default">{{ modalityLabel(agreement.modality, agreement.modality_label) }}</dd></div>
              <div><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.term') }}</dt><dd class="mt-1 text-sm text-text-default">{{ formatDate(agreement.partnership_start_date) }} – {{ formatDate(agreement.partnership_end_date) }}</dd></div>
              <div><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.financedBalance') }}</dt><dd class="mt-1 text-sm font-medium text-text-brand">{{ formatMoney(agreement.financed_balance, agreement.currency) }}</dd></div>
              <div><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.initialPayment') }}</dt><dd class="mt-1 text-sm text-text-default">{{ formatMoney(agreement.initial_payment, agreement.currency) }}</dd></div>
              <div><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.totalValue') }}</dt><dd class="mt-1 text-sm text-text-default">{{ formatMoney(agreement.total_value, agreement.currency) }}</dd></div>
              <div v-if="agreement.currency === 'USD'"><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.eligibilityEquivalent') }}</dt><dd class="mt-1 text-sm text-text-default">{{ formatMoney(agreement.equivalent_total_cop, 'COP') }} · {{ t('financing.agreement.detail.rate', { rate: formatMoney(agreement.eligibility_exchange_rate, 'COP') }) }}</dd></div>
              <div><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.currentHosting') }}</dt><dd class="mt-1 text-sm text-text-default">{{ formatMoney(agreement.hosting_value, agreement.currency) }} · {{ hostingPeriodLabel(agreement.hosting_period) }}</dd></div>
              <div><dt class="text-xs text-text-subtle">{{ t('financing.agreement.detail.frozenTemplate') }}</dt><dd class="mt-1 text-sm text-text-default">{{ agreement.template_name }} · v{{ agreement.template_version }}</dd></div>
            </dl>
            <div class="mt-5"><p class="text-xs text-text-subtle">{{ t('financing.agreement.detail.financedScope') }}</p><p class="mt-1 whitespace-pre-line text-sm leading-6 text-text-default">{{ agreement.financed_scope }}</p></div>
          </section>
          <InstallmentScheduleEditor
            :model-value="agreement.installment_schedule"
            :currency="agreement.currency"
            :months="agreement.policy?.financing_months || 12"
            :due-day-start="agreement.policy?.installment_due_day_start || 1"
            :due-day-end="agreement.policy?.installment_due_day_end || 5"
            disabled
          />
        </div>

        <aside class="rounded-2xl border border-border-default bg-surface p-5 lg:sticky lg:top-6 lg:self-start" aria-labelledby="financing-history-title">
          <h2 id="financing-history-title" class="text-base font-medium text-text-default">{{ t('financing.agreement.detail.auditHistory') }}</h2>
          <ol class="mt-5 space-y-5">
            <li v-for="event in agreement.events" :key="event.id" class="relative border-l border-border-default pl-4">
              <span class="absolute -left-1.5 top-1 h-3 w-3 rounded-full bg-primary" />
              <p class="text-sm font-medium text-text-default">{{ eventLabel(event.event_type) }}</p>
              <p class="mt-1 text-xs text-text-subtle">{{ event.actor_name }} · {{ formatDate(event.created_at) }}</p>
            </li>
          </ol>
        </aside>
      </div>
    </template>
  </BasePageShell>
</template>
