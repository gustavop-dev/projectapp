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
  disabledReason: { type: String, default: '' },
  as: { type: String, default: 'button' },
  to: { type: [String, Object], default: null },
})

const emit = defineEmits(['click'])
const attrs = useAttrs()
const definition = computed(() => getPanelAction(props.action))
const accessibleLabel = computed(() => (
  props.statusLabel || attrs['aria-label'] || props.label || definition.value.label
))
const tooltipLabel = computed(() => (
  (props.disabled && (
    props.disabledReason || `${accessibleLabel.value}: operación en curso. Espera un momento.`
  )) || props.tooltip || definition.value.label || accessibleLabel.value
))
</script>

<template>
  <BaseTooltip
    :text="tooltipLabel"
    :position="tooltipPosition"
    width="w-max max-w-xs"
    min-width="min-w-0"
    content-class="whitespace-nowrap [overflow-wrap:normal]"
    trigger-class=""
    :toggle-on-click="disabled"
    floating
  >
    <template #trigger="{ tooltipId }">
      <span
        class="inline-flex"
        :tabindex="disabled ? 0 : undefined"
        :aria-label="disabled ? `${accessibleLabel}: ${tooltipLabel}` : undefined"
        :aria-describedby="disabled ? tooltipId : undefined"
        :data-disabled-action-proxy="disabled ? '' : undefined"
      >
        <BaseButton
          v-bind="attrs"
          :variant="variant"
          :size="size"
          :type="type"
          :loading="loading"
          :disabled="disabled"
          :disabled-reason="disabledReason"
          :as="as"
          :to="to"
          icon-only
          :native-title="false"
          :class="disabled ? 'pointer-events-none' : undefined"
          :aria-label="accessibleLabel"
          :aria-describedby="tooltipId"
          :data-panel-action="action"
          @click="emit('click', $event)"
        >
          <BaseActionIcon v-if="!loading" :action="action" />
        </BaseButton>
        <span v-if="statusLabel" class="sr-only" role="status" aria-live="polite">
          {{ statusLabel }}
        </span>
      </span>
    </template>
  </BaseTooltip>
</template>
