<template>
  <Teleport to="body">
    <Transition name="confirm-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        @click.self="handleCancel"
      >
        <div class="bg-white dark:bg-esmerald dark:border dark:border-white/[0.06] rounded-2xl shadow-2xl dark:shadow-black/40 w-full max-w-md overflow-hidden" @click.stop>
          <!-- Header -->
          <div class="px-6 pt-6 pb-2">
            <div class="flex items-start gap-4">
              <div
                class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
                :class="variantClasses.iconBg"
              >
                <component :is="variantIcon" class="w-5 h-5" :class="variantClasses.iconColor" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-lg font-bold text-esmerald dark:text-white">{{ title }}</h3>
                <p class="mt-1 text-sm text-esmerald/70 dark:text-green-light/60 leading-relaxed">{{ message }}</p>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end gap-3 px-6 py-4">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-esmerald/70 dark:text-green-light bg-esmerald-light/60 dark:bg-white/[0.06] hover:bg-esmerald-light dark:hover:bg-white/[0.10] rounded-xl transition-colors"
              @click="handleCancel"
            >
              {{ cancelText }}
            </button>
            <button
              type="button"
              class="px-4 py-2 text-sm font-bold rounded-xl transition-colors"
              :class="variantClasses.confirmBtn"
              @click="handleConfirm"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, watch, onMounted, onBeforeUnmount, h } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: 'Confirmar acción' },
  message: { type: String, default: '¿Estás seguro de que deseas continuar?' },
  confirmText: { type: String, default: 'Confirmar' },
  cancelText: { type: String, default: 'Cancelar' },
  variant: {
    type: String,
    default: 'warning',
    validator: v => ['warning', 'danger', 'info'].includes(v),
  },
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const variantClasses = computed(() => {
  const map = {
    warning: {
      iconBg: 'bg-lemon/30 dark:bg-lemon/20',
      iconColor: 'text-esmerald dark:text-lemon',
      confirmBtn: 'bg-esmerald text-white hover:bg-esmerald-dark dark:bg-lemon dark:text-esmerald-dark dark:hover:bg-lemon/90',
    },
    danger: {
      iconBg: 'bg-red-50 dark:bg-red-500/10',
      iconColor: 'text-red-600 dark:text-red-400',
      confirmBtn: 'bg-red-600 text-white hover:bg-red-700',
    },
    info: {
      iconBg: 'bg-esmerald-light dark:bg-white/[0.06]',
      iconColor: 'text-esmerald dark:text-lemon',
      confirmBtn: 'bg-esmerald text-white hover:bg-esmerald-dark dark:bg-lemon dark:text-esmerald-dark dark:hover:bg-lemon/90',
    },
  }
  return map[props.variant] || map.warning
})

const WarningIcon = {
  render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', 'stroke-width': '2' }, [
    h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z' }),
  ]),
}

const DangerIcon = {
  render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', 'stroke-width': '2' }, [
    h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M12 9v3.75m0 3.75h.007v.008H12v-.008zM21 12a9 9 0 11-18 0 9 9 0 0118 0z' }),
  ]),
}

const InfoIcon = {
  render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', 'stroke-width': '2' }, [
    h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z' }),
  ]),
}

const variantIcon = computed(() => {
  const map = { warning: WarningIcon, danger: DangerIcon, info: InfoIcon }
  return map[props.variant] || WarningIcon
})

function handleConfirm() {
  emit('confirm')
  emit('update:modelValue', false)
}

function handleCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}

function handleEscape(e) {
  if (e.key === 'Escape' && props.modelValue) handleCancel()
}

watch(() => props.modelValue, (val) => {
  if (val) document.body.style.overflow = 'hidden'
  else document.body.style.overflow = ''
})

onMounted(() => document.addEventListener('keydown', handleEscape))
onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleEscape)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.confirm-modal-enter-active,
.confirm-modal-leave-active {
  transition: opacity 0.2s ease;
}
.confirm-modal-enter-active > div,
.confirm-modal-leave-active > div {
  transition: transform 0.2s ease;
}
.confirm-modal-enter-from,
.confirm-modal-leave-to {
  opacity: 0;
}
.confirm-modal-enter-from > div {
  transform: scale(0.95) translateY(10px);
}
.confirm-modal-leave-to > div {
  transform: scale(0.95) translateY(10px);
}
</style>
