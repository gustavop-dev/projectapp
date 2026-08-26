<script setup>
import {
  computed, getCurrentInstance, nextTick, onBeforeUnmount, onMounted, ref, watch,
} from 'vue'
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/vue/24/outline'
import BaseButton from '~/components/base/BaseButton.vue'
import BaseRowLink from '~/components/base/BaseRowLink.vue'

const props = defineProps({
  text: { type: String, default: '' },
  to: { type: [String, Object], default: null },
  lines: { type: Number, default: 1, validator: (value) => [1, 2].includes(value) },
  stretch: { type: Boolean, default: false },
  expandable: { type: Boolean, default: true },
  testId: { type: String, default: '' },
  contentClasses: { type: [String, Array, Object], default: '' },
})

const rootEl = ref(null)
const expanded = ref(false)
const hasOverflow = ref(false)
const contentId = `overflow-text-${getCurrentInstance()?.uid ?? 'content'}`
let observer = null
let observedWidth = null

const clampClass = computed(() => {
  if (expanded.value) return 'block whitespace-normal break-words'
  return props.lines === 2 ? 'line-clamp-2 break-words' : 'block truncate'
})

const tooltip = computed(() => (
  hasOverflow.value && !expanded.value ? props.text : undefined
))

function element() {
  return rootEl.value?.querySelector?.('[data-overflow-content]') || null
}

function measure() {
  if (expanded.value) return
  const el = element()
  if (!el) return
  hasOverflow.value = el.scrollWidth > el.clientWidth + 1
    || el.scrollHeight > el.clientHeight + 1
}

function observeText() {
  observer?.disconnect()
  const el = element()
  if (!el || typeof ResizeObserver === 'undefined') return
  observedWidth = el.getBoundingClientRect?.().width ?? el.clientWidth
  observer = new ResizeObserver((entries) => {
    const nextWidth = entries[0]?.contentRect?.width
    if (nextWidth === observedWidth) return
    observedWidth = nextWidth
    expanded.value = false
    nextTick(measure)
  })
  observer.observe(el)
}

function toggleExpanded() {
  expanded.value = !expanded.value
}

function onWindowResize() {
  expanded.value = false
  nextTick(measure)
}

watch(() => [props.text, props.lines], async () => {
  expanded.value = false
  await nextTick()
  measure()
  observeText()
})

onMounted(async () => {
  await nextTick()
  measure()
  observeText()
  window.addEventListener('resize', onWindowResize)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  window.removeEventListener('resize', onWindowResize)
})
</script>

<template>
  <div ref="rootEl" class="flex min-w-0 flex-col items-start gap-1">
    <BaseRowLink
      :id="contentId"
      :to="to"
      :stretch="stretch"
      :title="tooltip"
      :data-testid="testId || undefined"
      data-overflow-content
      :class="[clampClass, contentClasses]"
    >
      {{ text }}
    </BaseRowLink>
    <BaseButton
      v-if="expandable && hasOverflow"
      variant="link"
      size="sm"
      draggable="false"
      class="relative z-20 min-h-6 gap-0.5 text-2xs [@media(pointer:coarse)]:min-h-11 [@media(pointer:coarse)]:px-2"
      :aria-expanded="expanded"
      :aria-controls="contentId"
      :aria-label="expanded ? `Contraer título ${text}` : `Mostrar título completo ${text}`"
      :data-testid="testId ? `${testId}-toggle` : undefined"
      @click.stop="toggleExpanded"
      @pointerdown.stop
      @dragstart.prevent.stop
    >
      <ChevronUpIcon v-if="expanded" class="h-3 w-3" aria-hidden="true" />
      <ChevronDownIcon v-else class="h-3 w-3" aria-hidden="true" />
      {{ expanded ? 'Contraer' : 'Ver completo' }}
    </BaseButton>
  </div>
</template>
