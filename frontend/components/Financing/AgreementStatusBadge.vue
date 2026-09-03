<script setup>
import { computed } from 'vue'

const { t } = useI18n()

const props = defineProps({
  status: { type: String, required: true },
  label: { type: String, default: '' },
  archived: { type: Boolean, default: false },
})

const variants = {
  draft: 'neutral',
  ready: 'warning',
  active: 'info',
  completed: 'success',
  cancelled: 'danger',
}

const badgeLabel = computed(() => {
  if (props.archived) return t('financing.agreement.status.archived')
  const knownStatuses = new Set(['draft', 'ready', 'active', 'completed', 'cancelled'])
  return knownStatuses.has(props.status)
    ? t(`financing.agreement.status.${props.status}`)
    : (props.label || props.status)
})
const badgeVariant = computed(() => (props.archived ? 'neutral' : (variants[props.status] || 'neutral')))
</script>

<template>
  <BaseBadge :variant="badgeVariant" data-testid="financing-agreement-status">
    {{ badgeLabel }}
  </BaseBadge>
</template>
