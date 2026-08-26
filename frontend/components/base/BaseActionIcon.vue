<script setup>
import { computed } from 'vue'
import { getPanelAction } from '~/config/panelActions'

const props = defineProps({
  action: { type: String, required: true },
})

const definition = computed(() => getPanelAction(props.action))
</script>

<template>
  <component
    :is="definition.icon"
    class="base-action-icon !h-4 !w-4 shrink-0"
    aria-hidden="true"
    focusable="false"
    :data-panel-action="action"
  />
</template>
