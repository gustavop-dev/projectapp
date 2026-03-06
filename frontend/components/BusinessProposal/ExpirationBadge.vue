<template>
  <div
    v-if="!isExpired"
    class="expiration-badge fixed top-16 sm:top-4 left-1/2 -translate-x-1/2 z-40
           px-3 sm:px-4 py-1.5 sm:py-2 rounded-full backdrop-blur-sm shadow-md border
           select-none transition-colors duration-300"
    :class="badgeClasses"
  >
    <span class="flex items-center gap-2 text-sm font-medium">
      <span class="inline-block w-2 h-2 rounded-full" :class="dotClass" />
      Expira en {{ formattedCountdown }}
    </span>
  </div>
</template>

<script setup>
import { computed, toRef } from 'vue';
import { useExpirationTimer } from '~/composables/useExpirationTimer';

const props = defineProps({
  expiresAt: {
    type: String,
    default: null,
  },
});

const { isExpired, urgencyLevel, formattedCountdown } = useExpirationTimer(
  toRef(props, 'expiresAt'),
);

const badgeClasses = computed(() => {
  switch (urgencyLevel.value) {
    case 'urgent':
      return 'bg-red-50/90 border-red-200 text-red-700 animate-pulse';
    case 'warning':
      return 'bg-yellow-50/90 border-yellow-200 text-yellow-700';
    default:
      return 'bg-emerald-50/90 border-emerald-200 text-emerald-700';
  }
});

const dotClass = computed(() => {
  switch (urgencyLevel.value) {
    case 'urgent':
      return 'bg-red-500';
    case 'warning':
      return 'bg-yellow-500';
    default:
      return 'bg-emerald-500';
  }
});
</script>
