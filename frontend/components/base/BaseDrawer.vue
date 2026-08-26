<script setup>
import { computed, onBeforeUnmount, onMounted, ref, toRef, useId, watch } from 'vue'
import { useFocusTrap } from '~/composables/useFocusTrap'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  placement: { type: String, default: 'left' }, // left | right | bottom
  title: { type: String, default: '' },
  titleId: { type: String, default: '' },
  closeOnBackdrop: { type: Boolean, default: true },
  closeOnEsc: { type: Boolean, default: true },
  lockScroll: { type: Boolean, default: true },
  testId: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'close'])

const panelRef = ref(null)
const uid = useId()
const resolvedTitleId = computed(() => props.titleId || `${uid}-title`)

const panelClass = computed(() => {
  if (props.placement === 'right') {
    return 'inset-y-0 right-0 h-full w-[min(24rem,calc(100vw-2rem))] border-l'
  }
  if (props.placement === 'bottom') {
    return 'inset-x-0 bottom-0 max-h-[90dvh] w-full rounded-t-2xl border-t panel-portrait:left-1/2 panel-portrait:max-w-2xl panel-portrait:-translate-x-1/2 panel-portrait:rounded-2xl panel-portrait:border'
  }
  return 'inset-y-0 left-0 h-full w-[min(24rem,calc(100vw-2rem))] border-r'
})

const transitionName = computed(() => `base-drawer-${props.placement}`)

useFocusTrap(panelRef, { active: toRef(props, 'modelValue') })

const close = () => {
  emit('update:modelValue', false)
  emit('close')
}

const onBackdrop = () => {
  if (props.closeOnBackdrop) close()
}

const onKey = (event) => {
  if (event.key === 'Escape' && props.closeOnEsc && props.modelValue) close()
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  if (typeof document !== 'undefined') document.body.style.overflow = ''
})

watch(
  () => props.modelValue,
  (isOpen) => {
    if (!props.lockScroll || typeof document === 'undefined') return
    document.body.style.overflow = isOpen ? 'hidden' : ''
  },
  { immediate: true },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="base-drawer-overlay">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm"
        aria-hidden="true"
        @click="onBackdrop"
      />
    </Transition>

    <Transition :name="transitionName">
      <section
        v-if="modelValue"
        ref="panelRef"
        tabindex="-1"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="resolvedTitleId"
        :data-testid="testId || undefined"
        :class="[
          'fixed z-[9999] flex flex-col overflow-hidden border-border-default bg-surface shadow-overlay focus:outline-none',
          panelClass,
        ]"
      >
        <header class="flex min-h-16 shrink-0 items-center justify-between gap-3 border-b border-border-muted px-4 py-3 panel-portrait:px-6">
          <slot name="title">
            <h2 :id="resolvedTitleId" class="min-w-0 truncate text-lg font-semibold text-text-default">
              {{ title }}
            </h2>
          </slot>
          <BaseActionButton action="close" label="Cerrar" size="md" @click="close" />
        </header>

        <div class="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          <slot />
        </div>

        <footer v-if="$slots.footer" class="shrink-0 border-t border-border-muted bg-surface px-4 py-3 panel-portrait:px-6">
          <slot name="footer" />
        </footer>
      </section>
    </Transition>
  </Teleport>
</template>

<style scoped>
.base-drawer-overlay-enter-active,
.base-drawer-overlay-leave-active,
.base-drawer-left-enter-active,
.base-drawer-left-leave-active,
.base-drawer-right-enter-active,
.base-drawer-right-leave-active,
.base-drawer-bottom-enter-active,
.base-drawer-bottom-leave-active {
  transition-duration: 0.2s;
  transition-timing-function: ease;
}

.base-drawer-overlay-enter-from,
.base-drawer-overlay-leave-to {
  opacity: 0;
}

.base-drawer-left-enter-from,
.base-drawer-left-leave-to {
  transform: translateX(-100%);
}

.base-drawer-right-enter-from,
.base-drawer-right-leave-to {
  transform: translateX(100%);
}

.base-drawer-bottom-enter-from,
.base-drawer-bottom-leave-to {
  transform: translateY(100%);
}

@media (min-width: 600px) {
  .base-drawer-bottom-enter-from,
  .base-drawer-bottom-leave-to {
    transform: translate(-50%, 100%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .base-drawer-overlay-enter-active,
  .base-drawer-overlay-leave-active,
  .base-drawer-left-enter-active,
  .base-drawer-left-leave-active,
  .base-drawer-right-enter-active,
  .base-drawer-right-leave-active,
  .base-drawer-bottom-enter-active,
  .base-drawer-bottom-leave-active {
    transition: none;
  }
}
</style>
