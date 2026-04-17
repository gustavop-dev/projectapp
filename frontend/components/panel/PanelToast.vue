<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="opacity-0 translate-y-4"
      leave-to-class="opacity-0 translate-y-4"
    >
      <div
        v-if="toastMsg"
        class="fixed bottom-6 right-6 z-[9999] max-w-sm w-full px-4 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-3"
        :class="toastMsg.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'"
      >
        <span class="flex-1">{{ toastMsg.text }}</span>
        <button type="button" class="opacity-70 hover:opacity-100 transition-opacity" @click="clearToast">✕</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { usePanelToast } from '~/composables/usePanelToast';

const { toastMsg, clearToast } = usePanelToast();
</script>
