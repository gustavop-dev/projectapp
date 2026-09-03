<script setup>
import DOMPurify from 'dompurify'
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import ClientFormFields from '~/components/clients/ClientFormFields.vue'
import InstallmentScheduleEditor from '~/components/Financing/InstallmentScheduleEditor.vue'
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue'
import { useMarkdownPreview } from '~/composables/useMarkdownPreview'
import { useFinancingAgreementsStore } from '~/stores/financing_agreements'
import { useProposalClientsStore } from '~/stores/proposal_clients'
import { clientFormPayload, emptyClientForm } from '~/utils/billingCode'

const props = defineProps({
  agreement: { type: Object, default: null },
  templates: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
  errors: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['submit', 'cancel'])
const agreementStore = useFinancingAgreementsStore()
const clientsStore = useProposalClientsStore()
const { parseMarkdown } = useMarkdownPreview()
const { t } = useI18n()

const inlineClientOpen = ref(false)
const inlineClient = ref(emptyClientForm())
const inlineClientErrors = ref({})
const creatingClient = ref(false)
const showTemplate = ref(false)
const showPreview = ref(false)
const debouncedMarkdown = ref('')
let markdownTimer = null

function todayIso() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}

function nextInstallmentIso() {
  const now = new Date()
  const next = new Date(now.getFullYear(), now.getMonth() + 1, 5)
  return `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}-05`
}

function emptyForm() {
  const defaultTemplate = props.templates.find((item) => item.is_default) || props.templates[0]
  return {
    client_id: null,
    client_label: '',
    client_full_name: '',
    client_company: '',
    client_id_type: '',
    client_id_number: '',
    client_email: '',
    client_phone: '',
    source_proposal_id: '',
    source_project_id: '',
    original_contract_reference: '',
    original_contract_date: todayIso(),
    project_name: '',
    financed_scope: '',
    modality: 'five_year',
    partnership_start_date: todayIso(),
    currency: 'COP',
    total_value: '',
    initial_payment: '0.00',
    hosting_value: '',
    hosting_period: 'monthly',
    first_installment_date: nextInstallmentIso(),
    installment_schedule: [],
    template_id: defaultTemplate?.id || '',
    contract_markdown: defaultTemplate?.content_markdown || '',
  }
}

const form = ref(emptyForm())

watch(
  () => [props.agreement, props.templates],
  () => {
    if (props.agreement) {
      form.value = {
        ...emptyForm(),
        ...props.agreement,
        client_id: props.agreement.client,
        client_label: props.agreement.client_full_name,
        source_proposal_id: props.agreement.source_proposal || '',
        source_project_id: props.agreement.source_project || '',
        template_id: props.agreement.template?.id || '',
        installment_schedule: (props.agreement.installment_schedule || []).map((row) => ({ ...row })),
      }
      agreementStore.fetchClientContext(props.agreement.client)
    } else {
      form.value = emptyForm()
    }
  },
  { immediate: true, deep: false },
)

watch(() => form.value.contract_markdown, (value) => {
  clearTimeout(markdownTimer)
  markdownTimer = setTimeout(() => { debouncedMarkdown.value = value || '' }, 180)
}, { immediate: true })
onBeforeUnmount(() => clearTimeout(markdownTimer))

const templateOptions = computed(() => props.templates.map((item) => ({
  value: item.id,
  label: `${item.name} · v${item.version}${item.is_default ? ` · ${t('financing.agreement.form.defaultTemplate')}` : ''}`,
})))
const proposalOptions = computed(() => [
  { value: '', label: t('financing.agreement.form.noProposal') },
  ...(agreementStore.clientContext?.proposals || []).map((item) => ({ value: item.id, label: item.title })),
])
const projectOptions = computed(() => [
  { value: '', label: t('financing.agreement.form.noProject') },
  ...(agreementStore.clientContext?.projects || []).map((item) => ({ value: item.id, label: item.name })),
])
const modalityOptions = computed(() => [
  { value: 'five_year', label: t('financing.agreement.form.fiveYearOption'), testId: 'financing-modality-five' },
  { value: 'three_year', label: t('financing.agreement.form.threeYearOption'), testId: 'financing-modality-three' },
])
const hostingPeriodOptions = computed(() => [
  { value: 'monthly', label: t('financing.agreement.form.hostingPeriods.monthly') },
  { value: 'quarterly', label: t('financing.agreement.form.hostingPeriods.quarterly') },
  { value: 'semiannual', label: t('financing.agreement.form.hostingPeriods.semiannual') },
  { value: 'annual', label: t('financing.agreement.form.hostingPeriods.annual') },
])
const financedBalance = computed(() => Math.max(
  Number(form.value.total_value || 0) - Number(form.value.initial_payment || 0),
  0,
))
const previewHtml = computed(() => DOMPurify.sanitize(parseMarkdown(debouncedMarkdown.value)))

function errorFor(field) {
  const value = props.errors?.[field]
  return Array.isArray(value) ? value[0] : (value || '')
}

async function onClientSelect(client) {
  form.value.client_id = client?.id || null
  form.value.client_label = client?.name || ''
  form.value.source_proposal_id = ''
  form.value.source_project_id = ''
  if (!client?.id) {
    agreementStore.clientContext = null
    return
  }
  const result = await agreementStore.fetchClientContext(client.id)
  if (!result.success) return
  const snapshot = result.data.client
  Object.assign(form.value, {
    client_full_name: snapshot.name || '',
    client_company: snapshot.company || '',
    client_id_type: snapshot.id_type || '',
    client_id_number: snapshot.id_number || '',
    client_email: snapshot.email || '',
    client_phone: snapshot.phone || '',
  })
}

function openInlineClient(typedName) {
  inlineClient.value = { ...emptyClientForm(), name: typedName || '' }
  inlineClientErrors.value = {}
  inlineClientOpen.value = true
}

async function createInlineClient() {
  if (!inlineClient.value.name.trim()) {
    inlineClientErrors.value = { name: t('financing.agreement.form.clientNameRequired') }
    return
  }
  creatingClient.value = true
  const result = await clientsStore.createClient(clientFormPayload(inlineClient.value))
  creatingClient.value = false
  if (!result.success) {
    inlineClientErrors.value = result.errors || {}
    return
  }
  inlineClientOpen.value = false
  await onClientSelect(result.data)
}

function chooseTemplate(templateId) {
  form.value.template_id = templateId
  const template = props.templates.find((item) => item.id === Number(templateId))
  if (template && !props.agreement) form.value.contract_markdown = template.content_markdown
}

function chooseProject(projectId) {
  form.value.source_project_id = projectId
  const project = agreementStore.clientContext?.projects?.find((item) => item.id === Number(projectId))
  if (project && !form.value.project_name.trim()) form.value.project_name = project.name
}

function chooseProposal(proposalId) {
  form.value.source_proposal_id = proposalId
  const proposal = agreementStore.clientContext?.proposals?.find((item) => item.id === Number(proposalId))
  if (!proposal) return
  if (!form.value.project_name.trim()) form.value.project_name = proposal.title
  if (!form.value.total_value) form.value.total_value = proposal.total_investment
  if (proposal.currency) form.value.currency = proposal.currency
}

function submit() {
  const payload = {
    client_id: form.value.client_id,
    client_full_name: form.value.client_full_name.trim(),
    client_company: form.value.client_company.trim(),
    client_id_type: form.value.client_id_type.trim(),
    client_id_number: form.value.client_id_number.trim(),
    client_email: form.value.client_email.trim(),
    client_phone: form.value.client_phone.trim(),
    source_proposal_id: form.value.source_proposal_id || null,
    source_project_id: form.value.source_project_id || null,
    original_contract_reference: form.value.original_contract_reference.trim(),
    original_contract_date: form.value.original_contract_date,
    project_name: form.value.project_name.trim(),
    financed_scope: form.value.financed_scope.trim(),
    modality: form.value.modality,
    partnership_start_date: form.value.partnership_start_date,
    currency: form.value.currency,
    total_value: form.value.total_value,
    initial_payment: form.value.initial_payment || '0.00',
    hosting_value: form.value.hosting_value,
    hosting_period: form.value.hosting_period,
    template_id: form.value.template_id || undefined,
    contract_markdown: form.value.contract_markdown,
  }
  if (form.value.installment_schedule.length) {
    payload.installment_schedule = form.value.installment_schedule
  } else {
    payload.first_installment_date = form.value.first_installment_date
  }
  emit('submit', payload)
}
</script>

<template>
  <form class="space-y-6" novalidate @submit.prevent="submit">
    <section class="rounded-2xl border border-border-default bg-surface p-5 sm:p-6">
      <div class="mb-5">
        <p class="text-xs font-semibold uppercase tracking-widest text-text-brand">{{ t('financing.agreement.form.partiesEyebrow') }}</p>
        <h2 class="mt-1 text-lg font-medium text-text-default">{{ t('financing.agreement.form.partiesTitle') }}</h2>
      </div>
      <BaseFormField v-slot="{ invalid, errorId }" :label="t('financing.agreement.form.client')" required :error="errorFor('client_id')">
        <ClientAutocomplete
          v-model="form.client_id"
          :initial-label="form.client_label"
          :placeholder="t('financing.agreement.form.clientSearchPlaceholder')"
          :clear-label="t('financing.agreement.form.clearClient')"
          test-id="financing-agreement-client"
          allow-create
          :error="invalid"
          :error-described-by="errorId"
          @select="onClientSelect"
          @create-new="openInlineClient"
        />
      </BaseFormField>

      <div v-if="inlineClientOpen" class="mt-4 space-y-4 rounded-xl border border-border-default bg-surface-raised p-4" data-testid="financing-inline-client">
        <p class="text-sm font-medium text-text-default">{{ t('financing.agreement.form.inlineClientTitle') }}</p>
        <ClientFormFields v-model="inlineClient" testid-prefix="financing-inline-client" dense :errors="inlineClientErrors" />
        <div class="flex justify-end gap-2">
          <BaseButton type="button" variant="secondary" size="sm" @click="inlineClientOpen = false">{{ t('financing.agreement.form.cancel') }}</BaseButton>
          <BaseButton type="button" size="sm" :loading="creatingClient" data-testid="financing-inline-client-save" @click="createInlineClient">{{ t('financing.agreement.form.createAndSelect') }}</BaseButton>
        </div>
      </div>

      <div class="mt-5 grid gap-4 sm:grid-cols-2">
        <BaseFormField :label="t('financing.agreement.form.legalName')" required :error="errorFor('client_full_name')"><BaseInput v-model="form.client_full_name" data-testid="financing-client-legal-name" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.company')" :error="errorFor('client_company')"><BaseInput v-model="form.client_company" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.idType')" required :error="errorFor('client_id_type')"><BaseInput v-model="form.client_id_type" :placeholder="t('financing.agreement.form.idTypePlaceholder')" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.idNumber')" required :error="errorFor('client_id_number')"><BaseInput v-model="form.client_id_number" data-testid="financing-client-id-number" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.email')" required :error="errorFor('client_email')"><BaseInput v-model="form.client_email" type="email" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.phone')" :error="errorFor('client_phone')"><BaseInput v-model="form.client_phone" type="tel" /></BaseFormField>
      </div>
    </section>

    <section class="rounded-2xl border border-border-default bg-surface p-5 sm:p-6">
      <p class="text-xs font-semibold uppercase tracking-widest text-text-brand">{{ t('financing.agreement.form.scopeEyebrow') }}</p>
      <h2 class="mt-1 text-lg font-medium text-text-default">{{ t('financing.agreement.form.scopeTitle') }}</h2>
      <div class="mt-5 grid gap-4 sm:grid-cols-2">
        <BaseFormField :label="t('financing.agreement.form.originalContract')" required :error="errorFor('original_contract_reference')"><BaseInput v-model="form.original_contract_reference" :placeholder="t('financing.agreement.form.originalContractPlaceholder')" data-testid="financing-original-contract" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.originalContractDate')" required :error="errorFor('original_contract_date')"><BaseInput v-model="form.original_contract_date" type="date" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.linkedProposal')" :hint="t('financing.agreement.form.optional')"><BaseSelect :model-value="form.source_proposal_id" :options="proposalOptions" @update:model-value="chooseProposal" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.linkedProject')" :hint="t('financing.agreement.form.optional')"><BaseSelect :model-value="form.source_project_id" :options="projectOptions" @update:model-value="chooseProject" /></BaseFormField>
        <BaseFormField class="sm:col-span-2" :label="t('financing.agreement.form.projectName')" required :error="errorFor('project_name')"><BaseInput v-model="form.project_name" data-testid="financing-project-name" /></BaseFormField>
        <BaseFormField class="sm:col-span-2" :label="t('financing.agreement.form.financedScope')" required :error="errorFor('financed_scope')"><BaseTextarea v-model="form.financed_scope" rows="4" :placeholder="t('financing.agreement.form.financedScopePlaceholder')" data-testid="financing-scope" /></BaseFormField>
      </div>
    </section>

    <section class="rounded-2xl border border-border-default bg-surface p-5 sm:p-6">
      <p class="text-xs font-semibold uppercase tracking-widest text-text-brand">{{ t('financing.agreement.form.modalityEyebrow') }}</p>
      <h2 class="mt-1 text-lg font-medium text-text-default">{{ t('financing.agreement.form.modalityTitle') }}</h2>
      <BaseSegmented
        v-if="agreement?.cycle_number !== 2"
        v-model="form.modality"
        class="mt-5"
        :options="modalityOptions"
      />
      <BaseAlert v-else class="mt-5" variant="info">
        {{ t('financing.agreement.form.secondCycleNotice') }}
      </BaseAlert>
      <BaseAlert class="mt-4" :variant="form.modality === 'five_year' ? 'success' : 'info'">
        <p v-if="form.modality === 'five_year'" class="text-sm">{{ t('financing.agreement.form.fiveYearBenefits') }}</p>
        <p v-else class="text-sm">{{ t('financing.agreement.form.threeYearBenefits') }}</p>
      </BaseAlert>
      <div class="mt-4 max-w-sm"><BaseFormField :label="t('financing.agreement.form.partnershipStart')" required :error="errorFor('partnership_start_date')"><BaseInput v-model="form.partnership_start_date" type="date" :disabled="agreement?.cycle_number === 2" /></BaseFormField></div>
    </section>

    <section class="rounded-2xl border border-border-default bg-surface p-5 sm:p-6">
      <p class="text-xs font-semibold uppercase tracking-widest text-text-brand">{{ t('financing.agreement.form.financingEyebrow') }}</p>
      <h2 class="mt-1 text-lg font-medium text-text-default">{{ t('financing.agreement.form.financingTitle') }}</h2>
      <div class="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <BaseFormField :label="t('financing.agreement.form.currency')" required><BaseSelect v-model="form.currency" :options="[{ value: 'COP', label: 'COP' }, { value: 'USD', label: 'USD' }]" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.totalValue')" required :error="errorFor('total_value')"><BaseInput v-model="form.total_value" type="number" min="0" step="0.01" data-testid="financing-total-value" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.initialPayment')" :error="errorFor('initial_payment')"><BaseInput v-model="form.initial_payment" type="number" min="0" step="0.01" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.financedBalance')"><BaseInput :model-value="financedBalance.toFixed(2)" readonly data-testid="financing-balance" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.hostingValue')" required :error="errorFor('hosting_value')"><BaseInput v-model="form.hosting_value" type="number" min="0" step="0.01" data-testid="financing-hosting-value" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.hostingPeriod')"><BaseSelect v-model="form.hosting_period" :options="hostingPeriodOptions" /></BaseFormField>
        <BaseFormField v-if="!form.installment_schedule.length" :label="t('financing.agreement.form.firstInstallment')" required :error="errorFor('first_installment_date')"><BaseInput v-model="form.first_installment_date" type="date" data-testid="financing-first-installment" /></BaseFormField>
      </div>
      <BaseAlert class="mt-5" variant="warning" data-testid="financing-late-payment-rule">
        <p class="font-medium">{{ t('financing.agreement.form.latePaymentTitle') }}</p>
        <p class="mt-1 text-sm">{{ t('financing.agreement.form.latePaymentBody') }}</p>
      </BaseAlert>
    </section>

    <InstallmentScheduleEditor
      v-if="form.installment_schedule.length"
      v-model="form.installment_schedule"
      :currency="form.currency"
      :error="props.errors?.installment_schedule"
    />

    <section class="rounded-2xl border border-border-default bg-surface p-5 sm:p-6">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest text-text-brand">{{ t('financing.agreement.form.documentEyebrow') }}</p>
          <h2 class="mt-1 text-lg font-medium text-text-default">{{ t('financing.agreement.form.documentTitle') }}</h2>
          <p class="mt-1 text-sm text-text-subtle">{{ t('financing.agreement.form.documentHint') }}</p>
        </div>
        <BaseButton type="button" variant="secondary" size="sm" @click="showTemplate = !showTemplate">{{ showTemplate ? t('financing.agreement.form.hideEditing') : t('financing.agreement.form.editClauses') }}</BaseButton>
      </div>
      <div v-if="showTemplate" class="mt-5 space-y-4">
        <BaseFormField :label="t('financing.agreement.form.baseVersion')"><BaseSelect :model-value="form.template_id" :options="templateOptions" @update:model-value="chooseTemplate" /></BaseFormField>
        <BaseFormField :label="t('financing.agreement.form.markdownContent')" :error="errorFor('contract_markdown')"><BaseTextarea v-model="form.contract_markdown" rows="20" data-testid="financing-contract-markdown" /></BaseFormField>
        <div class="flex justify-end"><BaseButton type="button" variant="ghost" size="sm" @click="showPreview = !showPreview">{{ showPreview ? t('financing.agreement.form.hidePreview') : t('financing.agreement.form.previewText') }}</BaseButton></div>
        <div v-if="showPreview" class="prose prose-sm max-w-none rounded-xl border border-border-default bg-surface-raised p-5 text-text-default" data-testid="financing-markdown-preview" v-html="previewHtml" />
      </div>
    </section>

    <div class="sticky bottom-4 z-10 flex flex-col-reverse gap-2 rounded-2xl border border-border-default bg-surface/95 p-3 shadow-card backdrop-blur sm:flex-row sm:justify-end">
      <BaseButton type="button" variant="secondary" @click="emit('cancel')">{{ t('financing.agreement.form.cancel') }}</BaseButton>
      <BaseButton type="submit" :loading="saving" data-testid="financing-agreement-save">{{ agreement ? t('financing.agreement.form.saveChanges') : t('financing.agreement.form.createDraft') }}</BaseButton>
    </div>
  </form>
</template>
