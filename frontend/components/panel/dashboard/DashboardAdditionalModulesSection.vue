<script setup>
import { computed } from 'vue'
import AdditionalModulesQuickAccess from '~/components/AdditionalModules/QuickAccess.vue'

defineProps({
  summary: { type: Object, default: null },
})

const { locale } = useI18n()
const localePath = useLocalePath()
const language = computed(() => (locale.value.startsWith('en') ? 'en' : 'es'))

function openCatalog(action = '') {
  const path = localePath('/panel/additional-modules')
  return navigateTo(action ? { path, query: { action } } : path)
}
</script>

<template>
  <AdditionalModulesQuickAccess
    v-if="summary"
    compact
    :language="language"
    :stats="summary"
    data-testid="dashboard-additional-modules-section"
    @share="openCatalog('share')"
    @customize-pdf="openCatalog('pdf')"
    @tracking="openCatalog('tracking')"
    @manage="openCatalog()"
  />
</template>
