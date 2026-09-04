<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

/**
 * Shared spotlight tour for public module views (catalog, financing, …).
 * Each view passes its own steps, copy and storage key; the tour only shows
 * steps whose target exists in the current DOM, remembers completion per
 * browser and can be restarted on demand through `forceStart()`.
 */
const props = defineProps({
  /** [{ target: 'CSS selector', title, description, prefer: 'top|bottom|left|right' }] */
  steps: { type: Array, required: true },
  storageKey: { type: String, required: true },
  /** Prefix for data-testid hooks: `<prefix>`, `<prefix>-progress`, `<prefix>-next`, `<prefix>-done`. */
  testIdPrefix: { type: String, required: true },
  /** { skip, back, next, done } already translated by the owning view. */
  labels: { type: Object, required: true },
  isDark: { type: Boolean, default: false },
})

const emit = defineEmits(['complete'])

const VIEWPORT_PADDING = 12
const TARGET_GAP = 14
const TOOLTIP_MAX_WIDTH = 320
const TOOLTIP_ESTIMATED_HEIGHT = 230

const visible = ref(false)
const currentStep = ref(0)
const activeTargets = ref([])
const spotlightRect = ref(null)
const tooltipStyle = ref({})
const tooltipRef = ref(null)
let scrollTimer = null
let animationFrame = null

const activeSteps = computed(() => activeTargets.value
  .map((target) => props.steps.find((step) => step.target === target))
  .filter(Boolean))
const totalSteps = computed(() => activeSteps.value.length)
const currentStepData = computed(() => activeSteps.value[currentStep.value] || props.steps[0] || {})
const isLastStep = computed(() => currentStep.value === totalSteps.value - 1)
const spotlightStyle = computed(() => {
  if (!spotlightRect.value) return { display: 'none' }
  const padding = 5
  return {
    top: `${spotlightRect.value.top - padding}px`,
    left: `${spotlightRect.value.left - padding}px`,
    width: `${spotlightRect.value.width + (padding * 2)}px`,
    height: `${spotlightRect.value.height + (padding * 2)}px`,
  }
})

function getTargetRect(target) {
  const element = document.querySelector(target)
  if (!element) return null
  const rect = element.getBoundingClientRect()
  return {
    element,
    top: rect.top,
    right: rect.right,
    bottom: rect.bottom,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  }
}

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value))
}

function positionForSide(side, rect, tooltipWidth, tooltipHeight) {
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const centerX = rect.left + (rect.width / 2)
  const centerY = rect.top + (rect.height / 2)
  let top
  let left

  if (side === 'right') {
    top = clamp(centerY - (tooltipHeight / 2), VIEWPORT_PADDING, viewportHeight - tooltipHeight - VIEWPORT_PADDING)
    left = rect.right + TARGET_GAP
  } else if (side === 'left') {
    top = clamp(centerY - (tooltipHeight / 2), VIEWPORT_PADDING, viewportHeight - tooltipHeight - VIEWPORT_PADDING)
    left = rect.left - tooltipWidth - TARGET_GAP
  } else if (side === 'top') {
    top = rect.top - tooltipHeight - TARGET_GAP
    left = clamp(centerX - (tooltipWidth / 2), VIEWPORT_PADDING, viewportWidth - tooltipWidth - VIEWPORT_PADDING)
  } else {
    top = rect.bottom + TARGET_GAP
    left = clamp(centerX - (tooltipWidth / 2), VIEWPORT_PADDING, viewportWidth - tooltipWidth - VIEWPORT_PADDING)
  }

  const fits = top >= VIEWPORT_PADDING
    && left >= VIEWPORT_PADDING
    && top + tooltipHeight <= viewportHeight - VIEWPORT_PADDING
    && left + tooltipWidth <= viewportWidth - VIEWPORT_PADDING

  return fits ? { top: `${top}px`, left: `${left}px` } : null
}

function setTooltipPosition(rect, preferredSide) {
  const tooltipWidth = Math.min(
    tooltipRef.value?.offsetWidth || TOOLTIP_MAX_WIDTH,
    window.innerWidth - (VIEWPORT_PADDING * 2),
  )
  const tooltipHeight = tooltipRef.value?.offsetHeight || TOOLTIP_ESTIMATED_HEIGHT
  const sides = [...new Set([preferredSide, 'bottom', 'top', 'right', 'left'])]

  for (const side of sides) {
    const position = positionForSide(side, rect, tooltipWidth, tooltipHeight)
    if (position) {
      tooltipStyle.value = position
      return
    }
  }

  tooltipStyle.value = {
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
  }
}

function clearScheduledPosition() {
  if (scrollTimer !== null) {
    window.clearTimeout(scrollTimer)
    scrollTimer = null
  }
  if (animationFrame !== null) {
    window.cancelAnimationFrame(animationFrame)
    animationFrame = null
  }
}

function finishPositioning(step) {
  const rect = getTargetRect(step.target)
  if (!rect) {
    spotlightRect.value = null
    tooltipStyle.value = {
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    }
    return
  }

  spotlightRect.value = rect
  setTooltipPosition(rect, step.prefer)
}

function positionCurrentStep({ allowScroll = true } = {}) {
  clearScheduledPosition()
  const step = currentStepData.value
  if (!step?.target) return
  const rect = getTargetRect(step.target)
  if (!rect) return

  const isOutsideViewport = rect.bottom < VIEWPORT_PADDING
    || rect.top > window.innerHeight - VIEWPORT_PADDING

  if (allowScroll && isOutsideViewport && typeof rect.element.scrollIntoView === 'function') {
    spotlightRect.value = null
    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    rect.element.scrollIntoView({
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
      block: 'center',
    })
    scrollTimer = window.setTimeout(() => {
      scrollTimer = null
      finishPositioning(step)
    }, prefersReducedMotion ? 0 : 300)
    return
  }

  finishPositioning(step)
}

function schedulePosition() {
  if (!visible.value || animationFrame !== null) return
  animationFrame = window.requestAnimationFrame(() => {
    animationFrame = null
    positionCurrentStep({ allowScroll: false })
  })
}

async function begin() {
  activeTargets.value = props.steps
    .filter((step) => document.querySelector(step.target))
    .map((step) => step.target)
  if (!activeTargets.value.length) return

  currentStep.value = 0
  visible.value = true
  await nextTick()
  positionCurrentStep()
}

function start() {
  try {
    if (window.localStorage.getItem(props.storageKey)) return
  } catch {
    // Storage can be unavailable in privacy-restricted browsers.
  }
  void begin()
}

function forceStart() {
  try {
    window.localStorage.removeItem(props.storageKey)
  } catch {
    // The guide can still restart for this visit without persistence.
  }
  void begin()
}

function dismiss() {
  clearScheduledPosition()
  visible.value = false
  spotlightRect.value = null
  try {
    window.localStorage.setItem(props.storageKey, 'true')
  } catch {
    // The guide still closes when persistence is unavailable.
  }
  emit('complete')
}

async function next() {
  if (isLastStep.value) {
    dismiss()
    return
  }
  currentStep.value += 1
  await nextTick()
  positionCurrentStep()
}

async function previous() {
  if (currentStep.value === 0) return
  currentStep.value -= 1
  await nextTick()
  positionCurrentStep()
}

function onKeydown(event) {
  if (visible.value && event.key === 'Escape') dismiss()
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', schedulePosition)
  window.addEventListener('scroll', schedulePosition, true)
})

onBeforeUnmount(() => {
  clearScheduledPosition()
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', schedulePosition)
  window.removeEventListener('scroll', schedulePosition, true)
})

defineExpose({ start, forceStart })
</script>

<template>
  <Teleport to="body">
    <Transition name="guide-fade">
      <div
        v-if="visible && spotlightRect"
        class="public-guided-tour__spotlight pointer-events-none fixed z-[9998] rounded-2xl ring-2 ring-focus-ring"
        :style="spotlightStyle"
        aria-hidden="true"
      />
    </Transition>

    <Transition name="guide-pop" mode="out-in">
      <section
        v-if="visible"
        :key="currentStep"
        ref="tooltipRef"
        :data-theme="props.isDark ? 'dark' : 'light'"
        :style="tooltipStyle"
        class="fixed z-[10000] w-[calc(100vw-1.5rem)] max-w-xs rounded-2xl border border-border-default bg-surface p-5 shadow-overlay"
        role="dialog"
        :aria-labelledby="`${testIdPrefix}-title-${currentStep}`"
        :data-testid="testIdPrefix"
      >
        <div class="mb-3 flex items-center gap-1.5" aria-hidden="true">
          <span
            v-for="stepNumber in totalSteps"
            :key="stepNumber"
            class="h-1.5 rounded-full transition-all"
            :class="stepNumber - 1 === currentStep ? 'w-5 bg-primary' : 'w-1.5 bg-border-default'"
          />
          <span class="ml-auto text-xs font-medium tabular-nums text-text-subtle" :data-testid="`${testIdPrefix}-progress`">
            {{ currentStep + 1 }}/{{ totalSteps }}
          </span>
        </div>

        <h2
          :id="`${testIdPrefix}-title-${currentStep}`"
          class="text-base font-semibold text-text-default"
        >
          {{ currentStepData.title }}
        </h2>
        <p class="mt-2 text-sm leading-6 text-text-muted">
          {{ currentStepData.description }}
        </p>

        <div class="mt-5 flex items-center justify-between gap-3">
          <BaseButton variant="ghost" size="sm" type="button" @click="dismiss">
            {{ labels.skip }}
          </BaseButton>
          <div class="flex items-center gap-2">
            <BaseButton
              v-if="currentStep > 0"
              variant="ghost"
              size="sm"
              type="button"
              @click="previous"
            >
              {{ labels.back }}
            </BaseButton>
            <BaseButton
              size="sm"
              type="button"
              :data-testid="isLastStep ? `${testIdPrefix}-done` : `${testIdPrefix}-next`"
              @click="next"
            >
              {{ isLastStep ? labels.done : labels.next }}
            </BaseButton>
          </div>
        </div>
      </section>
    </Transition>
  </Teleport>
</template>

<style scoped>
.public-guided-tour__spotlight {
  box-shadow: 0 0 0 9999px rgb(0 0 0 / 0.52);
}

.guide-fade-enter-active,
.guide-fade-leave-active {
  transition: opacity 0.2s ease;
}
.guide-fade-enter-from,
.guide-fade-leave-to {
  opacity: 0;
}

.guide-pop-enter-active,
.guide-pop-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.guide-pop-enter-from,
.guide-pop-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
