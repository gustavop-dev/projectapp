<script setup>
import { computed } from 'vue'
import BaseSegmented from '~/components/base/BaseSegmented.vue'

const props = defineProps({
  modelValue: { type: String, default: 'cards' },
  language: { type: String, default: 'es' },
})

const emit = defineEmits(['update:modelValue', 'change-language'])
const { t } = useI18n()

const viewOptions = computed(() => [
  { value: 'cards', label: t('additionalModules.cards'), testId: 'additional-view-cards' },
  { value: 'list', label: t('additionalModules.list'), testId: 'additional-view-list' },
  { value: 'accordion', label: t('additionalModules.accordion'), testId: 'additional-view-accordion' },
])

const languageOptions = computed(() => [
  { value: 'es', label: t('additionalModules.spanish'), testId: 'additional-language-es' },
  { value: 'en', label: t('additionalModules.english'), testId: 'additional-language-en' },
])
</script>

<template>
  <div class="flex flex-col gap-4 rounded-2xl border border-border-default bg-surface-raised p-4 sm:flex-row sm:items-end sm:justify-between">
    <div class="min-w-0">
      <p id="additional-modules-view-label" class="mb-2 text-xs font-medium uppercase tracking-wide text-text-muted">
        {{ t('additionalModules.displayMode') }}
      </p>
      <BaseSegmented
        :model-value="modelValue"
        :options="viewOptions"
        size="sm"
        aria-labelledby="additional-modules-view-label"
        @update:model-value="emit('update:modelValue', $event)"
      />
    </div>
    <div class="min-w-0">
      <p id="additional-modules-language-label" class="mb-2 text-xs font-medium uppercase tracking-wide text-text-muted">
        {{ t('additionalModules.language') }}
      </p>
      <BaseSegmented
        :model-value="language"
        :options="languageOptions"
        size="sm"
        aria-labelledby="additional-modules-language-label"
        @update:model-value="emit('change-language', $event)"
      />
    </div>
  </div>
</template>
