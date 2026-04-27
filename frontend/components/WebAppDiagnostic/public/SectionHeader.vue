<template>
  <div class="mb-5">
    <div class="flex items-center gap-3">
      <span
        v-if="index"
        class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-primary/5 dark:bg-primary-soft/10 text-text-brand dark:text-text-brand text-xs font-mono font-semibold tracking-wide"
      >{{ index }}</span>
      <h2 class="m-0 text-2xl md:text-3xl font-semibold text-text-brand dark:text-text-brand leading-tight">
        {{ title || fallback }}
      </h2>
    </div>
    <div class="mt-3 h-px bg-gradient-to-r from-esmerald/30 dark:from-esmerald-light/40 via-esmerald/10 dark:via-esmerald-light/15 to-transparent" />
  </div>
</template>

<script setup>
defineProps({
  index: { type: String, default: '' },
  title: { type: String, default: '' },
  fallback: { type: String, default: '' },
});
</script>
