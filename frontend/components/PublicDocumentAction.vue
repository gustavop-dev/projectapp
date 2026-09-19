<script setup>
import BaseButton from '~/components/base/BaseButton.vue'

defineProps({
  action: { type: String, required: true, validator: (value) => ['theme', 'guide', 'pdf', 'share'].includes(value) },
  label: { type: String, required: true },
  isDark: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})
</script>

<template>
  <BaseButton
    unstyled
    icon-only
    :loading="loading"
    :aria-label="label"
    :title="label"
    :aria-pressed="action === 'theme' ? isDark : undefined"
    class="public-document-action fixed z-40 flex items-center justify-center rounded-full border border-border-default bg-surface text-text-muted shadow-raised transition-colors hover:bg-surface-muted hover:text-text-brand"
    :class="`public-document-action--${action}`"
  >
    <template v-if="!loading">
      <span v-if="action === 'theme'" aria-hidden="true" class="text-lg">{{ isDark ? '☀️' : '🌙' }}</span>
      <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path v-if="action === 'guide'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0Z" />
        <path v-else-if="action === 'pdf'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0-3-3m3 3 3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2H7Z" />
        <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342A3 3 0 108.684 10.658m0 2.684 6.632 3.316m-6.632-6 6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684Zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684Z" />
      </svg>
    </template>
  </BaseButton>
</template>

<style scoped>
.public-document-action--theme,
.public-document-action--guide {
  width: 2.75rem;
  height: 2.75rem;
  left: max(1rem, env(safe-area-inset-left));
}
.public-document-action--theme { bottom: calc(1rem + env(safe-area-inset-bottom)); }
.public-document-action--guide { bottom: calc(4.5rem + env(safe-area-inset-bottom)); }
.public-document-action--pdf,
.public-document-action--share {
  width: 3rem;
  height: 3rem;
  right: max(1rem, env(safe-area-inset-right));
}
.public-document-action--pdf { bottom: calc(4.75rem + env(safe-area-inset-bottom)); }
.public-document-action--share { bottom: calc(8.5rem + env(safe-area-inset-bottom)); }
@media (min-width: 640px) {
  .public-document-action--theme,
  .public-document-action--guide { left: max(1.5rem, env(safe-area-inset-left)); }
  .public-document-action--theme { bottom: calc(1.5rem + env(safe-area-inset-bottom)); }
}
</style>
