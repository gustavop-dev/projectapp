<script setup>
import BaseCard from '~/components/base/BaseCard.vue'

defineProps({
  module: { type: Object, required: true },
})

const { t } = useI18n()
</script>

<template>
  <div class="grid gap-4 sm:grid-cols-2">
    <BaseCard padding="md">
      <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">
        {{ t('additionalModules.whatIs') }}
      </h3>
      <p class="mt-3 break-words text-sm leading-6 text-text-muted">{{ module.what_is }}</p>
    </BaseCard>
    <BaseCard padding="md">
      <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">
        {{ t('additionalModules.purpose') }}
      </h3>
      <p class="mt-3 break-words text-sm leading-6 text-text-muted">{{ module.purpose }}</p>
    </BaseCard>
    <BaseCard padding="md">
      <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">
        {{ t('additionalModules.problemsSolved') }}
      </h3>
      <ul class="mt-3 space-y-2 text-sm leading-6 text-text-muted">
        <li v-for="item in module.problems_solved" :key="item" class="flex min-w-0 gap-2">
          <span aria-hidden="true" class="shrink-0 text-text-brand">•</span><span class="min-w-0 break-words">{{ item }}</span>
        </li>
      </ul>
    </BaseCard>
    <BaseCard padding="md">
      <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">
        {{ t('additionalModules.integrations') }}
      </h3>
      <ul class="mt-3 space-y-2 text-sm leading-6 text-text-muted">
        <li v-for="item in module.integrations" :key="item" class="flex min-w-0 gap-2">
          <span aria-hidden="true" class="shrink-0 text-text-brand">•</span><span class="min-w-0 break-words">{{ item }}</span>
        </li>
      </ul>
    </BaseCard>
    <BaseCard padding="md" class="sm:col-span-2">
      <h3 class="text-sm font-medium uppercase tracking-wide text-text-brand">
        {{ t('additionalModules.requirements') }}
      </h3>
      <ul class="mt-3 grid gap-2 text-sm leading-6 text-text-muted sm:grid-cols-2">
        <li v-for="item in module.implementation_requirements" :key="item" class="flex min-w-0 gap-2">
          <span aria-hidden="true" class="shrink-0 text-text-brand">•</span><span class="min-w-0 break-words">{{ item }}</span>
        </li>
      </ul>
    </BaseCard>
  </div>
</template>
