<script setup>
import { computed, ref } from 'vue'

import PublicGuidedTour from '~/components/PublicGuidedTour.vue'

const props = defineProps({
  isDark: { type: Boolean, default: false },
})

const emit = defineEmits(['complete'])
const { t } = useI18n()

const STORAGE_KEY = 'projectapp-financing-guide-seen'
const tour = ref(null)

const steps = computed(() => [
  {
    target: '.financing-explainer',
    title: t('financing.guideExplainerTitle'),
    description: t('financing.guideExplainerDescription'),
    prefer: 'bottom',
  },
  {
    target: '[data-testid="financing-option-five-year"]',
    title: t('financing.guideOptionsTitle'),
    description: t('financing.guideOptionsDescription'),
    prefer: 'bottom',
  },
  {
    target: '.financing-conditions-nav',
    title: t('financing.guideConditionsTitle'),
    description: t('financing.guideConditionsDescription'),
    prefer: 'bottom',
  },
  {
    target: '[data-testid="financing-calculator-input-output"]',
    title: t('financing.guideCalculatorTitle'),
    description: t('financing.guideCalculatorDescription'),
    prefer: 'top',
  },
  {
    target: '[data-testid="financing-package-facts"]',
    title: t('financing.guidePackageTitle'),
    description: t('financing.guidePackageDescription'),
    prefer: 'top',
  },
  {
    target: '.financing-terms',
    title: t('financing.guideTermsTitle'),
    description: t('financing.guideTermsDescription'),
    prefer: 'top',
  },
  {
    target: '[data-testid="financing-download-pdf-floating"]',
    title: t('financing.guideActionsTitle'),
    description: t('financing.guideActionsDescription'),
    prefer: 'left',
  },
  {
    target: '.financing-restart-guide',
    title: t('financing.guideRestartTitle'),
    description: t('financing.guideRestartDescription'),
    prefer: 'right',
  },
])

const labels = computed(() => ({
  skip: t('financing.guideSkip'),
  back: t('financing.guideBack'),
  next: t('financing.guideNext'),
  done: t('financing.guideDone'),
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
    test-id-prefix="financing-guide"
    :is-dark="props.isDark"
    @complete="emit('complete')"
  />
</template>
