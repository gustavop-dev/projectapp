<script setup>
import { computed, useAttrs } from 'vue'
import BaseActionIcon from './BaseActionIcon.vue'
import BaseButton from './BaseButton.vue'
import BaseTooltip from './BaseTooltip.vue'
import { getPanelAction } from '~/config/panelActions'
import { oneOf } from './propValidators'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  action: { type: String, required: true },
  label: { type: String, default: '' },
  tooltip: { type: String, default: '' },
  statusLabel: { type: String, default: '' },
  statusTone: {
    type: String,
    default: 'info',
    validator: oneOf(['info', 'success', 'danger']),
  },
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
const displayedTooltip = computed(() => props.statusLabel || tooltipLabel.value)
const displayedAction = computed(() => (
  props.action === 'copy' && props.statusLabel && props.statusTone === 'success'
    ? 'complete'
    : props.action
))
const statusColors = {
  info: { background: 'bg-info-soft', text: 'text-info-strong' },
  success: { background: 'bg-success-soft', text: 'text-success-strong' },
  danger: { background: 'bg-danger-soft', text: 'text-danger-strong' },
}
const tooltipBackground = computed(() => (
  props.statusLabel ? statusColors[props.statusTone].background : 'bg-primary-strong'
))
const tooltipTextColor = computed(() => (
  props.statusLabel ? statusColors[props.statusTone].text : 'text-white'
))
</script>

<template>
  <BaseTooltip
    :text="displayedTooltip"
    :position="tooltipPosition"
    :background-color="tooltipBackground"
    :text-color="tooltipTextColor"
    width="w-max max-w-xs"
    min-width="min-w-0"
    content-class="whitespace-nowrap [overflow-wrap:normal]"
    trigger-class=""
    :toggle-on-click="disabled"
    :force-open="Boolean(statusLabel)"
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
          :data-displayed-action="displayedAction"
          :data-action-status="statusLabel ? statusTone : undefined"
          @click="emit('click', $event)"
        >
          <BaseActionIcon v-if="!loading" :action="displayedAction" />
        </BaseButton>
        <span v-if="statusLabel" class="sr-only" role="status" aria-live="polite">
          {{ statusLabel }}
        </span>
      </span>
    </template>
  </BaseTooltip>
</template>
