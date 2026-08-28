<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  totalModules: { type: Number, default: 0 },
  downloadUrl: { type: String, default: '' },
  showHeader: { type: Boolean, default: true },
  isShared: { type: Boolean, default: false },
})

const { t } = useI18n()
const selectedModule = ref(null)
const detailOpen = ref(false)
const opener = ref(null)
const isDownloading = ref(false)
const downloadError = ref(false)

const hasModules = computed(() => props.totalModules > 0 && props.categories.length > 0)

function openModule(module, event) {
  selectedModule.value = module
  opener.value = event?.currentTarget || null
  detailOpen.value = true
}

function closeDetail() {
  detailOpen.value = false
}

function responseFilename(response) {
  const disposition = response.headers.get('content-disposition') || ''
  const match = disposition.match(/filename="?([^";]+)"?/i)
  return match?.[1] || 'additional-modules-catalog.pdf'
}

async function downloadPdf() {
  if (!props.downloadUrl || isDownloading.value) return
  isDownloading.value = true
  downloadError.value = false
  try {
    const response = await fetch(props.downloadUrl, { credentials: 'same-origin' })
    if (!response.ok) throw new Error(`PDF request failed: ${response.status}`)
    const objectUrl = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = responseFilename(response)
    link.click()
    URL.revokeObjectURL(objectUrl)
  } catch {
    downloadError.value = true
  } finally {
    isDownloading.value = false
  }
}

watch(detailOpen, async (isOpen) => {
  if (isOpen) return
  selectedModule.value = null
  await nextTick()
  opener.value?.focus?.()
})
</script>

<template>
  <div class="w-full">
    <header v-if="showHeader" class="px-4 pb-12 pt-28 sm:px-6 sm:pb-16 sm:pt-36">
      <div class="mx-auto max-w-[1400px] text-center">
        <p class="mb-3 text-sm font-medium uppercase tracking-[0.18em] text-text-brand">
          {{ t('additionalModules.eyebrow') }}
        </p>
        <h1 class="text-balance text-4xl font-light tracking-tight text-text-brand sm:text-6xl lg:text-7xl">
          {{ t('additionalModules.title') }}
        </h1>
        <p class="mx-auto mt-5 max-w-3xl text-base leading-7 text-text-muted sm:text-lg">
          {{ t('additionalModules.subtitle') }}
        </p>
        <p
          v-if="isShared"
          class="mx-auto mt-5 w-fit rounded-full border border-border-default bg-surface px-4 py-2 text-sm text-text-muted"
        >
          {{ t('additionalModules.sharedNotice') }}
        </p>
        <div v-if="hasModules" class="mt-7 flex flex-wrap items-center justify-center gap-3">
          <span class="text-sm font-medium text-text-muted">
            {{ t('additionalModules.moduleCount', { count: totalModules }) }}
          </span>
          <BaseButton
            v-if="downloadUrl"
            variant="secondary"
            :loading="isDownloading"
            data-testid="additional-modules-download-pdf"
            @click="downloadPdf"
          >
            {{ t('additionalModules.downloadPdf') }}
          </BaseButton>
        </div>
        <BaseAlert
          v-if="downloadError"
          class="mx-auto mt-4 max-w-xl text-left"
          variant="danger"
        >
          {{ t('additionalModules.pdfError') }}
        </BaseAlert>
      </div>
    </header>

    <div v-if="hasModules" class="mx-auto w-full max-w-[1400px] px-4 pb-20 sm:px-6">
      <nav
        class="mb-10 flex snap-x gap-2 overflow-x-auto pb-2 sm:flex-wrap sm:justify-center sm:overflow-visible"
        :aria-label="t('additionalModules.title')"
      >
        <a
          v-for="category in categories"
          :key="category.slug"
          :href="`#category-${category.slug}`"
          class="min-h-11 shrink-0 snap-start rounded-full border border-border-default bg-surface px-4 py-2.5 text-sm font-medium text-text-default transition-colors hover:border-primary hover:text-text-brand focus:outline-none focus:ring-2 focus:ring-focus-ring/40"
        >
          {{ category.name }}
        </a>
      </nav>

      <section
        v-for="category in categories"
        :id="`category-${category.slug}`"
        :key="category.slug"
        class="scroll-mt-24 pb-14"
        :aria-labelledby="`category-title-${category.slug}`"
      >
        <div class="mb-6 flex items-end justify-between gap-4 border-b border-border-default pb-4">
          <h2
            :id="`category-title-${category.slug}`"
            class="text-2xl font-light text-text-brand sm:text-3xl"
          >
            {{ category.name }}
          </h2>
          <span class="shrink-0 text-sm text-text-muted">{{ category.modules.length }}</span>
        </div>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <button
            v-for="module in category.modules"
            :id="`module-${module.slug}`"
            :key="module.slug"
            type="button"
            class="group min-h-52 rounded-2xl border border-border-default bg-surface p-5 text-left shadow-card transition duration-200 hover:-translate-y-0.5 hover:border-primary hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-focus-ring/40"
            :aria-label="t('additionalModules.openDetail', { name: module.name })"
            :data-testid="`additional-module-card-${module.slug}`"
            @click="openModule(module, $event)"
          >
            <span class="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-soft text-2xl" aria-hidden="true">
              {{ module.icon || '＋' }}
            </span>
            <span class="block text-lg font-medium leading-6 text-text-brand">
              {{ module.name }}
            </span>
            <span class="mt-3 block text-sm leading-6 text-text-muted">
              {{ module.summary }}
            </span>
            <span class="mt-5 inline-flex items-center gap-2 text-sm font-medium text-text-brand">
              {{ t('additionalModules.viewDetails') }}
              <span aria-hidden="true" class="transition-transform group-hover:translate-x-1">→</span>
            </span>
          </button>
        </div>
      </section>
    </div>

    <div v-else class="mx-auto max-w-2xl px-4 py-24 text-center sm:px-6">
      <h2 class="text-2xl font-medium text-text-brand">{{ t('additionalModules.emptyTitle') }}</h2>
      <p class="mt-3 text-text-muted">{{ t('additionalModules.emptyBody') }}</p>
    </div>

    <BaseModal
      v-model="detailOpen"
      kind="detail"
      padding="none"
      data-testid="additional-module-detail-modal"
      @close="closeDetail"
    >
      <div v-if="selectedModule" class="flex min-h-0 flex-col">
        <header class="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-border-default bg-surface px-5 py-5 sm:px-7">
          <div class="min-w-0">
            <span class="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-primary-soft text-2xl" aria-hidden="true">
              {{ selectedModule.icon || '＋' }}
            </span>
            <h2 class="text-balance text-2xl font-light text-text-brand sm:text-3xl">
              {{ selectedModule.name }}
            </h2>
            <p class="mt-2 max-w-3xl text-sm leading-6 text-text-muted sm:text-base">
              {{ selectedModule.summary }}
            </p>
          </div>
          <BaseButton
            variant="ghost"
            icon-only
            :aria-label="t('additionalModules.close')"
            @click="closeDetail"
          >
            <span aria-hidden="true" class="text-xl">×</span>
          </BaseButton>
        </header>

        <div class="grid gap-4 overflow-y-auto p-5 sm:grid-cols-2 sm:p-7">
          <BaseCard padding="md" class="sm:col-span-1">
            <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">{{ t('additionalModules.whatIs') }}</h3>
            <p class="mt-3 text-sm leading-6 text-text-muted">{{ selectedModule.what_is }}</p>
          </BaseCard>
          <BaseCard padding="md" class="sm:col-span-1">
            <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">{{ t('additionalModules.purpose') }}</h3>
            <p class="mt-3 text-sm leading-6 text-text-muted">{{ selectedModule.purpose }}</p>
          </BaseCard>
          <BaseCard padding="md">
            <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">{{ t('additionalModules.problemsSolved') }}</h3>
            <ul class="mt-3 space-y-2 text-sm leading-6 text-text-muted">
              <li v-for="item in selectedModule.problems_solved" :key="item" class="flex gap-2">
                <span aria-hidden="true" class="text-text-brand">•</span><span>{{ item }}</span>
              </li>
            </ul>
          </BaseCard>
          <BaseCard padding="md">
            <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">{{ t('additionalModules.integrations') }}</h3>
            <ul class="mt-3 space-y-2 text-sm leading-6 text-text-muted">
              <li v-for="item in selectedModule.integrations" :key="item" class="flex gap-2">
                <span aria-hidden="true" class="text-text-brand">•</span><span>{{ item }}</span>
              </li>
            </ul>
          </BaseCard>
          <BaseCard padding="md" class="sm:col-span-2">
            <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">{{ t('additionalModules.requirements') }}</h3>
            <ul class="mt-3 grid gap-2 text-sm leading-6 text-text-muted sm:grid-cols-2">
              <li v-for="item in selectedModule.implementation_requirements" :key="item" class="flex gap-2">
                <span aria-hidden="true" class="text-text-brand">•</span><span>{{ item }}</span>
              </li>
            </ul>
          </BaseCard>
        </div>
      </div>
    </BaseModal>
  </div>
</template>
