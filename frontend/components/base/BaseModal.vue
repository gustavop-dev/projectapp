<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, toRef, useId, watch } from 'vue'
import { useFocusTrap } from '~/composables/useFocusTrap'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  size: { type: String, default: 'md' }, // sm | md | lg | xl | 2xl | 5xl | full
  closeOnBackdrop: { type: Boolean, default: true },
  closeOnEsc: { type: Boolean, default: true },
  padding: { type: String, default: 'none' }, // none | md
  lockScroll: { type: Boolean, default: true },
  /** Pins the panel to a fixed 90vh column that never scrolls itself, so the
   * slot can own its scroll regions (fixed header/footer + independently
   * scrolling panes). Off by default: the panel grows to its content and
   * scrolls as a whole, which is what every form modal wants. */
  fullHeight: { type: Boolean, default: false },
  /** id of the element that labels the dialog; when empty, the first
   * h1/h2/h3 found in the slot is auto-detected and used instead. */
  titleId: { type: String, default: '' },
  /** CSS selector (scoped to the panel) for the element to focus on open;
   * defaults to the panel itself to avoid scroll-jumps in long forms. */
  initialFocus: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'close'])

const sizes = {
  sm: 'max-w-none sm:max-w-sm',
  md: 'max-w-none sm:max-w-md',
  lg: 'max-w-none sm:max-w-2xl',
  xl: 'max-w-none sm:max-w-3xl',
  '2xl': 'max-w-none sm:max-w-4xl',
  '5xl': 'max-w-none sm:max-w-5xl',
  // Near-fullscreen, capped so it stops stretching on ultrawide monitors.
  full: 'max-w-none sm:max-w-[min(90vw,1600px)]',
}

const sizeClass = computed(() => sizes[props.size] || sizes.md)
const paddingClass = computed(() => (props.padding === 'md' ? 'p-4 sm:p-6' : ''))
const heightClass = computed(() => (props.fullHeight
  ? 'h-[100dvh] sm:h-[90vh] overflow-hidden flex flex-col'
  : 'h-[100dvh] max-h-none overflow-y-auto sm:h-auto sm:max-h-[90vh]'))

const panelRef = ref(null)
const autoTitleId = ref('')
const uid = useId()

const resolvedTitleId = computed(() => props.titleId || autoTitleId.value || undefined)

useFocusTrap(panelRef, {
  active: toRef(props, 'modelValue'),
  initialFocus: () => {
    if (!props.initialFocus || !panelRef.value) return null
    return panelRef.value.querySelector(props.initialFocus)
  },
})

watch(
  () => props.modelValue,
  async (open) => {
    if (!open || props.titleId) return
    await nextTick()
    const heading = panelRef.value?.querySelector('h1, h2, h3')
    if (!heading) {
      autoTitleId.value = ''
      return
    }
    if (!heading.id) heading.id = `${uid}-title`
    autoTitleId.value = heading.id
  },
  { immediate: true },
)

function close() {
  emit('update:modelValue', false)
  emit('close')
}

function onBackdrop() {
  if (props.closeOnBackdrop) close()
}

function onKey(e) {
  if (e.key === 'Escape' && props.closeOnEsc && props.modelValue) close()
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  if (typeof document !== 'undefined') document.body.style.overflow = ''
})

watch(
  () => props.modelValue,
  (open) => {
    if (!props.lockScroll || typeof document === 'undefined') return
    document.body.style.overflow = open ? 'hidden' : ''
  },
  { immediate: true },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="base-modal-fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9999] flex items-center justify-center p-0 sm:p-4"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="resolvedTitleId"
      >
        <div class="absolute inset-0 bg-black/50" @click="onBackdrop" />
        <div
          ref="panelRef"
          tabindex="-1"
          class="relative w-full bg-surface rounded-none border-0 shadow-overlay focus:outline-none sm:rounded-2xl sm:border sm:border-border-default"
          :class="[sizeClass, paddingClass, heightClass]"
        >
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.base-modal-fade-enter-active,
.base-modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.base-modal-fade-enter-from,
.base-modal-fade-leave-to {
  opacity: 0;
}
@media (prefers-reduced-motion: reduce) {
  .base-modal-fade-enter-active,
  .base-modal-fade-leave-active {
    transition: none;
  }
}
</style>
