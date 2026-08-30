<script setup>
import BaseButton from '~/components/base/BaseButton.vue'

defineProps({
  module: { type: Object, required: true },
})

const emit = defineEmits(['detail', 'edit', 'status'])
const { t } = useI18n()
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <BaseButton variant="ghost" size="sm" @click="emit('detail', $event)">
      {{ t('additionalModules.viewDetails') }}
    </BaseButton>
    <BaseButton variant="secondary" size="sm" @click="emit('edit')">
      {{ t('additionalModules.edit') }}
    </BaseButton>
    <BaseButton
      :variant="module.is_active ? 'danger-ghost' : 'secondary'"
      size="sm"
      @click="emit('status')"
    >
      {{ module.is_active ? t('additionalModules.retire') : t('additionalModules.restore') }}
    </BaseButton>
  </div>
</template>
