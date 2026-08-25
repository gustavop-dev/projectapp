<script setup>
import { computed, useAttrs } from 'vue'
import BaseActionIcon from './BaseActionIcon.vue'
import BaseButton from './BaseButton.vue'
import BaseTooltip from './BaseTooltip.vue'
import { getPanelAction } from '~/config/panelActions'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  action: { type: String, required: true },
  label: { type: String, default: '' },
  tooltip: { type: String, default: '' },
  statusLabel: { type: String, default: '' },
  tooltipPosition: { type: String, default: 'top' },
  variant: { type: String, default: 'ghost' },
  size: { type: String, default: 'sm' },
  type: { type: String, default: 'button' },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  as: { type: String, default: 'button' },
  to: { type: [String, Object], default: null },
})

const emit = defineEmits(['click'])
const attrs = useAttrs()
const definition = computed(() => getPanelAction(props.action))
const accessibleLabel = computed(() => (
  props.statusLabel || attrs['aria-label'] || props.label || definition.value.label
))
const tooltipLabel = computed(() => props.tooltip || accessibleLabel.value)
</script>

<template>
  <BaseTooltip
    :text="tooltipLabel"
    :position="tooltipPosition"
    width="max-w-xs"
    min-width="min-w-0"
    trigger-class=""
    :toggle-on-click="false"
  >
    <template #trigger="{ tooltipId }">
      <BaseButton
        v-bind="attrs"
        :variant="variant"
        :size="size"
        :type="type"
        :loading="loading"
        :disabled="disabled"
        :as="as"
        :to="to"
        icon-only
        :aria-label="accessibleLabel"
        :aria-describedby="tooltipId"
        :title="tooltipLabel"
        :data-panel-action="action"
        @click="emit('click', $event)"
      >
        <BaseActionIcon v-if="!loading" :action="action" />
      </BaseButton>
      <span v-if="statusLabel" class="sr-only" role="status" aria-live="polite">
        {{ statusLabel }}
      </span>
    </template>
  </BaseTooltip>
</template>
