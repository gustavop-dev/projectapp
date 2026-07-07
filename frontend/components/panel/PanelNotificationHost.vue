<script setup>
import { useRouter } from 'vue-router';
import { usePanelNotify } from '~/composables/usePanelNotify';

const { notifications, dismiss } = usePanelNotify();
const router = useRouter();

const variants = {
  success: 'bg-success-soft text-success-strong border-success-strong/40',
  error: 'bg-danger-soft text-danger-strong border-danger-strong/40',
  warning: 'bg-warning-soft text-warning-strong border-warning-strong/40',
  info: 'bg-primary-soft text-text-default border-primary',
};

function variantClass(type) {
  return variants[type] || variants.info;
}

async function runAction(n) {
  const { action } = n;
  dismiss(n.id);
  if (!action) return;
  if (typeof action.handler === 'function') {
    await action.handler();
  } else if (action.to) {
    router.push(action.to);
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-6 right-6 z-[9999] flex w-full max-w-sm flex-col gap-3 pointer-events-none">
      <TransitionGroup
        enter-active-class="transition-all duration-300 ease-out motion-reduce:transition-none"
        leave-active-class="transition-all duration-200 ease-in motion-reduce:transition-none"
        enter-from-class="opacity-0 translate-y-4 motion-reduce:translate-y-0"
        leave-to-class="opacity-0 translate-y-4 motion-reduce:translate-y-0"
        move-class="transition-transform duration-200 motion-reduce:transition-none"
      >
        <div
          v-for="n in notifications"
          :key="n.id"
          role="alert"
          class="pointer-events-auto flex items-start gap-3 rounded-xl border-l-4 px-4 py-3 shadow-lg"
          :class="variantClass(n.type)"
        >
          <span class="mt-0.5 shrink-0">
            <svg v-if="n.type === 'success'" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else-if="n.type === 'error'" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3m0 4h.01M10.29 3.86l-8.48 14.7A1.5 1.5 0 003.11 21h17.78a1.5 1.5 0 001.3-2.44l-8.48-14.7a1.5 1.5 0 00-2.62 0z" />
            </svg>
            <svg v-else-if="n.type === 'warning'" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M12 3a9 9 0 100 18 9 9 0 000-18z" />
            </svg>
            <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </span>

          <div class="min-w-0 flex-1">
            <p v-if="n.title" class="text-sm font-semibold" :class="{ 'mb-0.5': n.detail }">{{ n.title }}</p>
            <p v-if="n.detail" class="text-sm opacity-90">{{ n.detail }}</p>
            <button
              v-if="n.action"
              type="button"
              class="mt-2 inline-flex items-center gap-1 text-sm font-semibold underline underline-offset-2 transition-opacity hover:opacity-80"
              @click="runAction(n)"
            >
              {{ n.action.label }}
            </button>
          </div>

          <button
            type="button"
            aria-label="Cerrar"
            class="-mr-1 -mt-1 shrink-0 rounded-lg p-1 transition-colors hover:bg-surface-raised"
            @click="dismiss(n.id)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
