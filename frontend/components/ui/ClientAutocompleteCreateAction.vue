<script setup>
import { computed } from 'vue'
import BaseActionIcon from '~/components/base/BaseActionIcon.vue'
import BaseButton from '~/components/base/BaseButton.vue'

const props = defineProps({
  inputText: { type: String, default: '' },
})

defineEmits(['create'])

const typedName = computed(() => props.inputText.trim())
</script>

<template>
  <BaseButton
    variant="ghost"
    size="sm"
    textPolicy="wrap"
    class="w-full !justify-start !bg-primary-soft text-left !text-text-brand hover:opacity-90"
    data-testid="client-autocomplete-create-new"
    @click="$emit('create')"
  >
    <BaseActionIcon action="create" />
    <span>{{ typedName
      ? `Crear nuevo cliente "${typedName}"`
      : 'Crear un cliente' }}</span>
  </BaseButton>
</template>
