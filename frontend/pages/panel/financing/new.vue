<script setup>
import { onMounted, ref } from 'vue'

import { usePanelNotify } from '~/composables/usePanelNotify'
import { useFinancingAgreementsStore } from '~/stores/financing_agreements'

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] })

const store = useFinancingAgreementsStore()
const notify = usePanelNotify()
const localePath = useLocalePath()
const { t } = useI18n()
const errors = ref({})

onMounted(() => Promise.all([store.fetchTemplates(), store.fetchSettings()]))

async function createAgreement(payload) {
  errors.value = {}
  const result = await store.createAgreement(payload)
  if (!result.success) {
    errors.value = result.errors || {}
    notify.error({ title: result.errors?.detail || t('financing.agreement.newPage.reviewData') })
    return
  }
  notify.success({ title: t('financing.agreement.newPage.createSuccess') })
  await navigateTo(localePath(`/panel/financing/${result.data.id}`))
}
</script>

<template>
  <BasePageShell width="content">
    <header class="mb-6">
      <NuxtLink :to="localePath('/panel/financing?tab=agreements')" class="text-sm text-text-brand hover:underline">{{ t('financing.agreement.newPage.back') }}</NuxtLink>
      <p class="mt-6 text-xs font-semibold uppercase tracking-widest text-text-brand">{{ t('financing.agreement.newPage.eyebrow') }}</p>
      <h1 class="mt-1 text-2xl font-light text-text-default">{{ t('financing.agreement.newPage.title') }}</h1>
      <p class="mt-2 max-w-3xl text-sm leading-6 text-text-subtle">
        {{ t('financing.agreement.newPage.description') }}
      </p>
    </header>

    <BaseAlert v-if="errors.code" class="mb-5" variant="danger" role="alert">
      {{ t('financing.agreement.newPage.createError') }}
    </BaseAlert>

    <FinancingAgreementForm
      :templates="store.templates"
      :policy="store.currentPolicy"
      :exchange-rate="store.financingSettings?.usd_exchange_rate"
      :saving="store.isSaving"
      :errors="errors"
      @submit="createAgreement"
      @cancel="navigateTo(localePath('/panel/financing?tab=agreements'))"
    />
  </BasePageShell>
</template>
