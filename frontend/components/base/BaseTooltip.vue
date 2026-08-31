<template>
  <div ref="rootEl" :class="[floating ? '' : 'relative', rootClass]">
    <div
      ref="triggerEl"
      data-base-tooltip-trigger
      @pointerenter="handlePointerEnter"
      @pointerleave="handlePointerLeave"
      @focusin="handleFocusIn"
      @focusout="handleFocusOut"
      @click="handleClick"
      @keydown.esc="showTooltip = false"
      :class="triggerClass"
    >
      <slot name="trigger" :tooltip-id="tooltipId">
        <QuestionMarkCircleIcon class="w-5 h-5 text-text-subtle" />
      </slot>
    </div>

    <Teleport to="body" :disabled="!floating">
      <transition
        enter-active-class="transition duration-200 ease-out motion-reduce:transition-none"
        enter-from-class="transform scale-95 opacity-0 motion-reduce:transform-none"
        enter-to-class="transform scale-100 opacity-100 motion-reduce:transform-none"
        leave-active-class="transition duration-150 ease-in motion-reduce:transition-none"
        leave-from-class="transform scale-100 opacity-100 motion-reduce:transform-none"
        leave-to-class="transform scale-95 opacity-0 motion-reduce:transform-none"
      >
        <div
          v-if="tooltipVisible"
          :id="tooltipId"
          ref="tooltipEl"
          role="tooltip"
          :class="[
            'pointer-events-none px-3 py-2 text-sm rounded-lg shadow-raised',
            floating
              ? 'fixed z-[70] max-w-[calc(100vw-1rem)]'
              : 'absolute z-10 break-words',
            backgroundColor,
            textColor,
            width,
            minWidth,
            contentClass,
            floating ? '' : positionClasses,
          ]"
          :style="floating ? floatingStyle : undefined"
        >
          <slot>{{ text }}</slot>
          <div
            :class="[
              'absolute w-2 h-2 transform rotate-45',
              floating ? floatingArrowClasses : arrowPositionClasses,
              backgroundColor,
            ]"
            :style="floating ? floatingArrowStyle : undefined"
          />
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import {
  computed, nextTick, onBeforeUnmount, ref, useId, watch,
} from 'vue'
import { QuestionMarkCircleIcon } from '@heroicons/vue/24/outline'
import { onClickOutside } from '@vueuse/core'
import { oneOf } from './propValidators'

const TOOLTIP_OFFSET = 8
const ARROW_EDGE_OFFSET = -4
const ARROW_CROSS_AXIS_PADDING = 12
const OPPOSITE_POSITION = {
  top: 'bottom',
  bottom: 'top',
  left: 'right',
  right: 'left',
}

const props = defineProps({
  position: {
    type: String,
    default: 'top',
    validator: oneOf(['top', 'bottom', 'left', 'right']),
  },
  backgroundColor: {
    // Brand-dark surface: legible over both washes and consistent with the
    // tooltip spec (bg-primary-strong + text-white). Override per-consumer
    // only for genuinely branded tooltips.
    type: String,
    default: 'bg-primary-strong',
  },
  textColor: {
    type: String,
    default: 'text-white',
  },
  width: {
    type: String,
    default: 'max-w-2xl',
  },
  minWidth: {
    type: String,
    default: 'min-w-[260px] sm:min-w-[420px] lg:min-w-[560px]',
  },
  contentClass: {
    type: String,
    default: 'whitespace-normal [overflow-wrap:anywhere]',
  },
  text: { type: String, default: '' },
  rootClass: { type: [String, Array, Object], default: 'inline-block' },
  triggerClass: { type: String, default: 'cursor-help' },
  toggleOnClick: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
  /** Keep the same viewport-aware tooltip visible while a transient action
   * status is active. Hover/focus behavior resumes when the status clears. */
  forceOpen: { type: Boolean, default: false },
  floating: { type: Boolean, default: false },
  viewportPadding: { type: Number, default: 8 },
})

const showTooltip = ref(false)
const tooltipVisible = computed(() => !props.disabled && (props.forceOpen || showTooltip.value))
const rootEl = ref(null)
const triggerEl = ref(null)
const tooltipEl = ref(null)
const touchActive = ref(false)
const tooltipId = useId()
const resolvedPosition = ref(props.position)
const floatingStyle = ref({ top: '0px', left: '0px', visibility: 'hidden' })
const floatingArrowStyle = ref({})
let floatingListenersActive = false

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), Math.max(min, max))
}

function spaceFor(position, triggerRect, viewportWidth, viewportHeight) {
  if (position === 'top') return triggerRect.top
  if (position === 'bottom') return viewportHeight - triggerRect.bottom
  if (position === 'left') return triggerRect.left
  return viewportWidth - triggerRect.right
}

function requiredSpace(position, tooltipRect) {
  return (position === 'top' || position === 'bottom')
    ? tooltipRect.height + TOOLTIP_OFFSET
    : tooltipRect.width + TOOLTIP_OFFSET
}

function resolvePosition(triggerRect, tooltipRect, viewportWidth, viewportHeight) {
  const preferred = props.position
  const opposite = OPPOSITE_POSITION[preferred]
  const padding = Math.max(0, props.viewportPadding)
  const preferredSpace = spaceFor(preferred, triggerRect, viewportWidth, viewportHeight) - padding
  const oppositeSpace = spaceFor(opposite, triggerRect, viewportWidth, viewportHeight) - padding
  const preferredFits = preferredSpace >= requiredSpace(preferred, tooltipRect)
  const oppositeFits = oppositeSpace >= requiredSpace(opposite, tooltipRect)

  if (preferredFits || (!oppositeFits && preferredSpace >= oppositeSpace)) return preferred
  return opposite
}

function updateFloatingPosition() {
  if (!props.floating || !tooltipVisible.value || typeof window === 'undefined') return
  const trigger = triggerEl.value
  const tooltip = tooltipEl.value
  if (!trigger || !tooltip) return

  const triggerRect = trigger.getBoundingClientRect()
  const tooltipRect = tooltip.getBoundingClientRect()
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight
  const padding = Math.max(0, props.viewportPadding)
  const position = resolvePosition(triggerRect, tooltipRect, viewportWidth, viewportHeight)
  resolvedPosition.value = position

  let top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
  let left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
  if (position === 'top') top = triggerRect.top - tooltipRect.height - TOOLTIP_OFFSET
  else if (position === 'bottom') top = triggerRect.bottom + TOOLTIP_OFFSET
  else if (position === 'left') left = triggerRect.left - tooltipRect.width - TOOLTIP_OFFSET
  else left = triggerRect.right + TOOLTIP_OFFSET

  left = clamp(left, padding, viewportWidth - tooltipRect.width - padding)
  top = clamp(top, padding, viewportHeight - tooltipRect.height - padding)

  floatingStyle.value = {
    top: `${Math.round(top)}px`,
    left: `${Math.round(left)}px`,
    visibility: 'visible',
  }

  if (position === 'top' || position === 'bottom') {
    const triggerCenter = triggerRect.left + triggerRect.width / 2
    const arrowLeft = clamp(
      triggerCenter - left,
      ARROW_CROSS_AXIS_PADDING,
      tooltipRect.width - ARROW_CROSS_AXIS_PADDING,
    )
    floatingArrowStyle.value = {
      left: `${Math.round(arrowLeft)}px`,
      [position === 'top' ? 'bottom' : 'top']: `${ARROW_EDGE_OFFSET}px`,
    }
    return
  }

  const triggerCenter = triggerRect.top + triggerRect.height / 2
  const arrowTop = clamp(
    triggerCenter - top,
    ARROW_CROSS_AXIS_PADDING,
    tooltipRect.height - ARROW_CROSS_AXIS_PADDING,
  )
  floatingArrowStyle.value = {
    top: `${Math.round(arrowTop)}px`,
    [position === 'left' ? 'right' : 'left']: `${ARROW_EDGE_OFFSET}px`,
  }
}

function stopFloatingListeners() {
  if (!floatingListenersActive || typeof window === 'undefined') return
  window.removeEventListener('resize', updateFloatingPosition)
  window.removeEventListener('scroll', updateFloatingPosition, true)
  floatingListenersActive = false
}

function startFloatingListeners() {
  if (floatingListenersActive || typeof window === 'undefined') return
  window.addEventListener('resize', updateFloatingPosition)
  window.addEventListener('scroll', updateFloatingPosition, true)
  floatingListenersActive = true
}

const handlePointerEnter = (e) => {
  if (props.disabled) return
  if (e.pointerType !== 'touch' && !touchActive.value) showTooltip.value = true
}

const handlePointerLeave = (e) => {
  if (props.disabled) return
  if (e.pointerType !== 'touch' && !touchActive.value) showTooltip.value = false
}

const handleClick = (event) => {
  if (props.disabled || !props.toggleOnClick) return
  event.stopPropagation()
  if (touchActive.value && showTooltip.value) {
    showTooltip.value = false
    touchActive.value = false
    return
  }
  touchActive.value = true
  showTooltip.value = true
}

const handleFocusIn = () => {
  if (!props.disabled) showTooltip.value = true
}

const handleFocusOut = (event) => {
  if (props.disabled) return
  if (!rootEl.value?.contains(event.relatedTarget)) {
    showTooltip.value = false
    touchActive.value = false
  }
}

onClickOutside(rootEl, () => {
  if (showTooltip.value) {
    showTooltip.value = false
  }
  touchActive.value = false
})

watch(() => props.disabled, (disabled) => {
  if (!disabled) return
  showTooltip.value = false
  touchActive.value = false
})

watch(
  [tooltipVisible, () => props.floating, () => props.position, () => props.text],
  async ([visible, floating]) => {
    stopFloatingListeners()
    if (!visible || !floating || props.disabled) return
    floatingStyle.value = { top: '0px', left: '0px', visibility: 'hidden' }
    await nextTick()
    if (!tooltipVisible.value || !props.floating) return
    updateFloatingPosition()
    startFloatingListeners()
  },
  { immediate: true },
)

onBeforeUnmount(stopFloatingListeners)

const positionClasses = computed(() => {
  switch (props.position) {
    case 'top':
      return 'bottom-full mb-2 left-1/2 -translate-x-1/2'
    case 'bottom':
      return 'top-full mt-2 left-1/2 -translate-x-1/2'
    case 'left':
      return 'right-full mr-2 top-1/2 -translate-y-1/2'
    case 'right':
      return 'left-full ml-2 top-1/2 -translate-y-1/2'
    default:
      return ''
  }
})

const arrowPositionClasses = computed(() => {
  switch (props.position) {
    case 'top':
      return 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2'
    case 'bottom':
      return 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2'
    case 'left':
      return 'right-0 top-1/2 -translate-y-1/2 translate-x-1/2'
    case 'right':
      return 'left-0 top-1/2 -translate-y-1/2 -translate-x-1/2'
    default:
      return ''
  }
})

const floatingArrowClasses = computed(() => (
  resolvedPosition.value === 'top' || resolvedPosition.value === 'bottom'
    ? '-translate-x-1/2'
    : '-translate-y-1/2'
))
</script>
