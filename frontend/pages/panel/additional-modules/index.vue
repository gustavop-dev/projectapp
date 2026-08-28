<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { get_request } from '~/stores/services/request_http'
import { useAdditionalModulesStore } from '~/stores/additional_modules'
import { usePanelNotify } from '~/composables/usePanelNotify'

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] })

const { locale, t } = useI18n()
const store = useAdditionalModulesStore()
const notify = usePanelNotify()

const moduleFormOpen = ref(false)
const editingModule = ref(null)
const moduleError = ref('')
const categoriesOpen = ref(false)
const categoryManager = ref(null)
const categoryError = ref('')
const orderOpen = ref(false)
const orderError = ref('')
const selectionOpen = ref(false)
const selectionMode = ref('share')
const selectionError = ref('')
const generatedUrl = ref('')
const historyOpen = ref(false)
const clients = ref([])
const detailOpen = ref(false)
const detailModule = ref(null)
const detailOpener = ref(null)

const isEnglish = computed(() => locale.value.startsWith('en'))
const orderedCategories = computed(() => [...store.categories].sort((a, b) => a.order - b.order))
const groupedModules = computed(() => orderedCategories.value.map((category) => ({
  ...category,
  modules: store.modules.filter((module) => module.category === category.id),
})).filter((category) => category.modules.length > 0))

const localized = (value, field) => value?.[`${field}_${isEnglish.value ? 'en' : 'es'}`] || ''

function humanError(errors, fallbackKey = 'additionalModules.saveError') {
  if (!errors) return t(fallbackKey)
  if (typeof errors === 'string') return errors
  if (errors.detail) return Array.isArray(errors.detail) ? errors.detail[0] : errors.detail
  const value = Object.values(errors)[0]
  if (Array.isArray(value)) return value[0]
  if (typeof value === 'object') return humanError(value, fallbackKey)
  return String(value || t(fallbackKey))
}

onMounted(async () => {
  await Promise.all([store.fetchCatalog(), store.fetchShareLinks()])
  try {
    const response = await get_request('proposals/client-profiles/?limit=100')
    clients.value = response.data.results || response.data
  } catch {
    clients.value = []
  }
})

async function retryCatalog() {
  await store.fetchCatalog()
}

function openCreateModule() {
  editingModule.value = null
  moduleError.value = ''
  moduleFormOpen.value = true
}

function openEditModule(module) {
  editingModule.value = module
  moduleError.value = ''
  moduleFormOpen.value = true
}

async function saveModule(payload) {
  moduleError.value = ''
  const result = await store.saveModule(editingModule.value?.id, payload)
  if (!result.success) {
    moduleError.value = humanError(result.errors)
    return
  }
  moduleFormOpen.value = false
  notify.success({ title: t('additionalModules.saveSuccess') })
}

async function changeModuleStatus(module) {
  const action = module.is_active ? 'retire' : 'restore'
  const result = await store.setModuleStatus(module.id, action)
  if (!result.success) {
    notify.error({ title: humanError(result.errors) })
    return
  }
  notify.success({ title: t('additionalModules.saveSuccess') })
}

async function saveCategory({ id, payload }) {
  categoryError.value = ''
  const result = await store.saveCategory(id, payload)
  if (!result.success) {
    categoryError.value = humanError(result.errors)
    return
  }
  categoryManager.value?.closeForm?.()
  notify.success({ title: t('additionalModules.saveSuccess') })
}

async function changeCategoryStatus({ category, action }) {
  categoryError.value = ''
  const result = await store.setCategoryStatus(category.id, action)
  if (!result.success) categoryError.value = humanError(result.errors)
}

async function saveOrder(payload) {
  orderError.value = ''
  const result = await store.reorderCatalog(payload)
  if (!result.success) {
    orderError.value = result.errors?.code === 'stale_catalog_revision'
      ? t('additionalModules.staleOrder')
      : humanError(result.errors)
    return
  }
  orderOpen.value = false
  notify.success({ title: t('additionalModules.saveSuccess') })
}

function openSelection(mode) {
  selectionMode.value = mode
  selectionError.value = ''
  generatedUrl.value = ''
  selectionOpen.value = true
}

async function submitSelection(payload) {
  selectionError.value = ''
  if (selectionMode.value === 'share') {
    const result = await store.createShareLink(payload)
    if (!result.success) {
      selectionError.value = humanError(result.errors)
      return
    }
    generatedUrl.value = `${window.location.origin}${result.data.public_path}`
    return
  }

  const result = await store.downloadPdf(payload)
  if (!result.success) {
    selectionError.value = humanError(result.errors)
    return
  }
  const objectUrl = URL.createObjectURL(new Blob([result.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = payload.language === 'en'
    ? 'additional-modules-catalog.pdf'
    : 'catalogo-modulos-adicionales.pdf'
  link.click()
  URL.revokeObjectURL(objectUrl)
  selectionOpen.value = false
}

async function openHistory() {
  await store.fetchShareLinks()
  historyOpen.value = true
}

async function changeShareStatus({ link, action }) {
  const result = await store.setShareLinkStatus(link.uuid, action)
  if (!result.success) notify.error({ title: humanError(result.errors) })
}

async function copyShare(link) {
  try {
    await navigator.clipboard.writeText(`${window.location.origin}${link.public_path}`)
    notify.success({ title: t('additionalModules.copied') })
  } catch {
    notify.error({ title: t('additionalModules.saveError') })
  }
}

function openDetail(module, event) {
  detailModule.value = module
  detailOpener.value = event?.currentTarget || null
  detailOpen.value = true
}

async function closeDetail() {
  detailOpen.value = false
  detailModule.value = null
  await nextTick()
  detailOpener.value?.focus?.()
}
</script>

<template>
  <BasePageShell width="panel">
    <header class="mb-7 flex flex-col gap-5 panel-portrait:flex-row panel-portrait:items-start panel-portrait:justify-between">
      <div class="min-w-0">
        <h1 class="text-2xl font-light text-text-default">{{ t('additionalModules.panelTitle') }}</h1>
        <p class="mt-1 max-w-3xl text-sm text-text-subtle">{{ t('additionalModules.panelDescription') }}</p>
        <p class="mt-2 text-xs font-medium text-text-brand">{{ t('additionalModules.noPriceNotice') }}</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <BaseButton size="sm" data-testid="additional-module-new" @click="openCreateModule">{{ t('additionalModules.addModule') }}</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="categoriesOpen = true">{{ t('additionalModules.manageCategories') }}</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="orderOpen = true">{{ t('additionalModules.reorder') }}</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="openSelection('share')">{{ t('additionalModules.createLink') }}</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="openSelection('pdf')">{{ t('additionalModules.downloadPdf') }}</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="openHistory">{{ t('additionalModules.shareHistory') }}</BaseButton>
      </div>
    </header>

    <div v-if="store.isLoading && !store.modules.length" class="flex min-h-64 items-center justify-center" role="status">
      <span class="h-8 w-8 animate-spin rounded-full border-2 border-border-default border-t-primary" />
    </div>

    <div
      v-else-if="store.error && !store.modules.length"
      class="rounded-xl border border-danger-strong/30 bg-danger-soft p-6 text-center"
      role="alert"
    >
      <p class="font-medium text-danger-strong">{{ t('additionalModules.loadError') }}</p>
      <BaseButton class="mt-4" variant="secondary" @click="retryCatalog">
        {{ t('additionalModules.retry') }}
      </BaseButton>
    </div>

    <BaseEmptyState
      v-else-if="!store.modules.length"
      :title="t('additionalModules.emptyTitle')"
      :description="t('additionalModules.emptyBody')"
    />

    <div v-else class="space-y-10">
      <nav class="flex gap-2 overflow-x-auto pb-2 panel-portrait:flex-wrap" :aria-label="t('additionalModules.title')">
        <a
          v-for="category in groupedModules"
          :key="category.id"
          :href="`#panel-additional-category-${category.slug}`"
          class="min-h-11 shrink-0 rounded-full border border-border-default bg-surface px-4 py-2.5 text-sm font-medium text-text-default hover:border-primary focus:outline-none focus:ring-2 focus:ring-focus-ring/40"
        >{{ localized(category, 'name') }}</a>
      </nav>

      <section
        v-for="category in groupedModules"
        :id="`panel-additional-category-${category.slug}`"
        :key="category.id"
        class="scroll-mt-20"
      >
        <div class="mb-4 flex flex-wrap items-center gap-2 border-b border-border-default pb-3">
          <h2 class="text-xl font-medium text-text-brand">{{ localized(category, 'name') }}</h2>
          <BaseBadge v-if="!category.is_active" variant="neutral">{{ t('additionalModules.retired') }}</BaseBadge>
          <span class="ml-auto text-sm text-text-muted">{{ category.modules.length }}</span>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          <article
            v-for="module in category.modules"
            :key="module.id"
            class="flex min-h-64 flex-col rounded-xl border border-border-default bg-surface p-5 shadow-card"
            :class="!module.is_active ? 'opacity-70' : ''"
            :data-testid="`additional-admin-module-${module.id}`"
          >
            <div class="flex items-start justify-between gap-3">
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-soft text-xl" aria-hidden="true">{{ module.icon || '＋' }}</span>
              <BaseBadge :variant="module.is_active ? 'success' : 'neutral'">
                {{ module.is_active ? t('additionalModules.active') : t('additionalModules.retired') }}
              </BaseBadge>
            </div>
            <h3 class="mt-4 text-lg font-medium leading-6 text-text-brand">{{ localized(module, 'name') }}</h3>
            <p class="mt-2 flex-1 text-sm leading-6 text-text-muted">{{ localized(module, 'summary') }}</p>
            <div class="mt-5 flex flex-wrap gap-2">
              <BaseButton variant="ghost" size="sm" @click="openDetail(module, $event)">{{ t('additionalModules.viewDetails') }}</BaseButton>
              <BaseButton variant="secondary" size="sm" @click="openEditModule(module)">{{ t('additionalModules.edit') }}</BaseButton>
              <BaseButton
                :variant="module.is_active ? 'danger-ghost' : 'secondary'"
                size="sm"
                @click="changeModuleStatus(module)"
              >
                {{ module.is_active ? t('additionalModules.retire') : t('additionalModules.restore') }}
              </BaseButton>
            </div>
          </article>
        </div>
      </section>
    </div>

    <AdditionalModulesModuleFormModal
      v-model="moduleFormOpen"
      :module="editingModule"
      :categories="store.categories"
      :saving="store.isUpdating"
      :error-message="moduleError"
      @save="saveModule"
    />
    <AdditionalModulesCategoryManagerModal
      ref="categoryManager"
      v-model="categoriesOpen"
      :categories="store.categories"
      :saving="store.isUpdating"
      :error-message="categoryError"
      @save="saveCategory"
      @status="changeCategoryStatus"
    />
    <AdditionalModulesCatalogOrderModal
      v-model="orderOpen"
      :categories="store.categories"
      :modules="store.modules"
      :saving="store.isUpdating"
      :error-message="orderError"
      @save="saveOrder"
    />
    <AdditionalModulesCatalogSelectionModal
      v-model="selectionOpen"
      :mode="selectionMode"
      :categories="store.categories"
      :modules="store.modules"
      :clients="clients"
      :saving="store.isUpdating"
      :error-message="selectionError"
      :generated-url="generatedUrl"
      @submit="submitSelection"
    />
    <AdditionalModulesShareHistoryModal
      v-model="historyOpen"
      :links="store.shareLinks"
      :saving="store.isUpdating"
      @status="changeShareStatus"
      @copy="copyShare"
    />

    <BaseModal v-model="detailOpen" kind="detail" padding="none" @close="closeDetail">
      <div v-if="detailModule" class="flex min-h-0 flex-col">
        <header class="flex items-start justify-between gap-4 border-b border-border-default px-5 py-5 sm:px-7">
          <div>
            <span class="text-2xl" aria-hidden="true">{{ detailModule.icon }}</span>
            <h2 class="mt-2 text-2xl font-light text-text-brand">{{ localized(detailModule, 'name') }}</h2>
            <p class="mt-2 text-sm leading-6 text-text-muted">{{ localized(detailModule, 'summary') }}</p>
          </div>
          <BaseActionButton
            action="close"
            :label="t('additionalModules.close')"
            @click="closeDetail"
          />
        </header>
        <div class="grid gap-4 overflow-y-auto p-5 sm:grid-cols-2 sm:p-7">
          <BaseCard><h3 class="font-medium text-text-brand">{{ t('additionalModules.whatIs') }}</h3><p class="mt-2 text-sm leading-6 text-text-muted">{{ localized(detailModule, 'what_is') }}</p></BaseCard>
          <BaseCard><h3 class="font-medium text-text-brand">{{ t('additionalModules.purpose') }}</h3><p class="mt-2 text-sm leading-6 text-text-muted">{{ localized(detailModule, 'purpose') }}</p></BaseCard>
          <BaseCard v-for="field in ['problems_solved', 'integrations', 'implementation_requirements']" :key="field" :class="field === 'implementation_requirements' ? 'sm:col-span-2' : ''">
            <h3 class="font-medium text-text-brand">{{ t(`additionalModules.${field === 'problems_solved' ? 'problemsSolved' : field === 'integrations' ? 'integrations' : 'requirements'}`) }}</h3>
            <ul class="mt-2 space-y-2 text-sm leading-6 text-text-muted">
              <li v-for="item in detailModule[`${field}_${isEnglish ? 'en' : 'es'}`]" :key="item" class="flex gap-2"><span aria-hidden="true">•</span><span>{{ item }}</span></li>
            </ul>
          </BaseCard>
        </div>
      </div>
    </BaseModal>
  </BasePageShell>
</template>
