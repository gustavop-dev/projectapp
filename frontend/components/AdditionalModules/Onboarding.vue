<script setup>
import { computed, ref } from 'vue'

import PublicGuidedTour from '~/components/PublicGuidedTour.vue'

const props = defineProps({
  isDark: { type: Boolean, default: false },
})

const emit = defineEmits(['complete'])
const { t } = useI18n()

const STORAGE_KEY = 'projectapp-additional-modules-guide-seen'
const tour = ref(null)

const steps = computed(() => [
  {
    target: '.additional-modules-explainer',
    title: t('additionalModules.guideExplainerTitle'),
    description: t('additionalModules.guideExplainerDescription'),
    prefer: 'bottom',
  },
  {
    target: '.additional-modules-theme-toggle',
    title: t('additionalModules.guideThemeTitle'),
    description: t('additionalModules.guideThemeDescription'),
    prefer: 'right',
  },
  {
    target: '.additional-modules-controls',
    title: t('additionalModules.guideViewTitle'),
    description: t('additionalModules.guideViewDescription'),
    prefer: 'bottom',
  },
  {
    target: '.additional-modules-category-nav',
    title: t('additionalModules.guideCategoriesTitle'),
    description: t('additionalModules.guideCategoriesDescription'),
    prefer: 'bottom',
  },
  {
    target: '.additional-module-entry',
    title: t('additionalModules.guideDetailsTitle'),
    description: t('additionalModules.guideDetailsDescription'),
    prefer: 'bottom',
  },
  {
    target: '.additional-modules-share-btn',
    title: t('additionalModules.guideShareTitle'),
    description: t('additionalModules.guideShareDescription'),
    prefer: 'left',
  },
  {
    target: '.additional-modules-pdf-fab',
    title: t('additionalModules.guidePdfTitle'),
    description: t('additionalModules.guidePdfDescription'),
    prefer: 'left',
  },
  {
    target: '.additional-modules-restart-guide',
    title: t('additionalModules.guideRestartTitle'),
    description: t('additionalModules.guideRestartDescription'),
    prefer: 'right',
  },
])

const labels = computed(() => ({
  skip: t('additionalModules.guideSkip'),
  back: t('additionalModules.guideBack'),
  next: t('additionalModules.guideNext'),
  done: t('additionalModules.guideDone'),
}))

defineExpose({
  start: () => tour.value?.start(),
  forceStart: () => tour.value?.forceStart(),
})
</script>

<template>
  <PublicGuidedTour
    ref="tour"
    :steps="steps"
    :labels="labels"
    :storage-key="STORAGE_KEY"
    test-id-prefix="additional-modules-guide"
    :is-dark="props.isDark"
    @complete="emit('complete')"
  />
</template>
