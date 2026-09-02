<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { usePanelNotify } from '~/composables/usePanelNotify'
import { get_request } from '~/stores/services/request_http'

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] })

const { locale, t } = useI18n()
const switchLocalePath = useSwitchLocalePath()
const notify = usePanelNotify()
const isEnglish = computed(() => locale.value.startsWith('en'))
const language = computed(() => (isEnglish.value ? 'en' : 'es'))
const program = ref(null)
const isLoading = ref(false)
const loadError = ref(false)

const publicPath = computed(() => (
  isEnglish.value ? '/en-us/financing' : '/es-co/financing'
))
const publicUrl = computed(() => `https://projectapp.co${publicPath.value}`)
const pdfUrl = computed(() => `/api/financing/public/pdf/?lang=${language.value}`)

async function loadProgram() {
  isLoading.value = true
  loadError.value = false
  try {
    const response = await get_request(`financing/public/?lang=${language.value}`)
    program.value = response.data
  } catch {
    loadError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(loadProgram)
watch(language, loadProgram)

async function copyPublicUrl() {
  try {
    await navigator.clipboard.writeText(publicUrl.value)
    notify.success({ title: t('financing.copiedPublicUrl') })
  } catch {
    notify.error({ title: t('financing.shareFailed') })
  }
}

async function changeLanguage(nextLanguage) {
  if (nextLanguage === language.value) return
  const path = switchLocalePath(nextLanguage === 'en' ? 'en-us' : 'es-co')
  if (path) await navigateTo(path)
}
</script>

<template>
  <BasePageShell width="panel">
    <header class="mb-7">
      <h1 class="text-2xl font-light text-text-default">{{ t('financing.panelTitle') }}</h1>
      <p class="mt-2 max-w-3xl text-sm leading-6 text-text-subtle">{{ t('financing.panelDescription') }}</p>
    </header>

    <section class="rounded-2xl border border-border-default bg-surface p-5 shadow-card sm:p-6" aria-labelledby="financing-distribution-title">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <h2 id="financing-distribution-title" class="text-xl font-medium text-text-brand">{{ t('financing.distributionTitle') }}</h2>
            <BaseBadge variant="success">{{ t('financing.publicBadge') }}</BaseBadge>
            <BaseBadge variant="neutral">{{ t('financing.indexableBadge') }}</BaseBadge>
          </div>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-text-muted">{{ t('financing.distributionDescription') }}</p>
          <label class="mt-5 block text-sm font-medium text-text-default" for="financing-public-url">
            {{ t('financing.publicUrlLabel') }}
          </label>
          <BaseInput
            id="financing-public-url"
            class="mt-2"
            :model-value="publicUrl"
            readonly
            data-testid="financing-public-url"
          />
        </div>
        <div class="flex flex-wrap gap-2">
          <BaseButton variant="secondary" data-testid="financing-copy-public-url" @click="copyPublicUrl">
            {{ t('financing.copyPublicUrl') }}
          </BaseButton>
          <BaseButton as="NuxtLink" :to="publicPath" target="_blank" data-testid="financing-open-public">
            {{ t('financing.openPublicView') }}
          </BaseButton>
          <BaseButton as="a" :to="pdfUrl" variant="secondary" data-testid="financing-panel-download-pdf">
            {{ t('financing.downloadPdf') }}
          </BaseButton>
        </div>
      </div>
    </section>

    <BaseAlert
      v-if="program && !program.package.catalog_synced"
      class="mt-5"
      variant="warning"
      data-testid="financing-package-warning"
    >
      <p class="font-medium">{{ t('financing.catalogWarningTitle') }}</p>
      <p class="mt-1 text-sm">{{ t('financing.catalogWarningBody') }}</p>
    </BaseAlert>

    <div v-if="isLoading && !program" class="flex min-h-64 items-center justify-center" role="status">
      <span class="h-8 w-8 animate-spin rounded-full border-2 border-border-default border-t-primary" />
    </div>
    <div v-else-if="loadError && !program" class="mt-6 rounded-xl border border-danger-strong/30 bg-danger-soft p-6 text-center" role="alert">
      <p class="font-medium text-danger-strong">{{ t('financing.loadError') }}</p>
      <BaseButton class="mt-4" variant="secondary" @click="loadProgram">{{ t('financing.retry') }}</BaseButton>
    </div>
    <section v-else-if="program" class="mt-8 overflow-hidden rounded-2xl border border-border-default" aria-labelledby="financing-preview-title">
      <h2 id="financing-preview-title" class="border-b border-border-default bg-surface px-5 py-4 text-lg font-medium text-text-brand">
        {{ t('financing.previewTitle') }}
      </h2>
      <FinancingProgramView
        :program="program"
        :download-url="pdfUrl"
        :language="language"
        :floating-actions="false"
        @change-language="changeLanguage"
      />
    </section>
  </BasePageShell>
</template>
