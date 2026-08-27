<template>
  <article class="rounded-xl border border-border-default bg-surface-raised p-3">
    <p class="text-sm font-medium text-text-default">{{ note?.title || 'Observación' }}</p>
    <p class="mt-1 whitespace-pre-wrap break-words text-sm text-text-muted">{{ note?.content }}</p>
  </article>
</template>

<script setup>
defineProps({
  note: { type: Object, required: true },
});
</script>
