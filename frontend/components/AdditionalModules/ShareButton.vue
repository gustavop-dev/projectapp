<script setup>
import PublicDocumentShareButton from '~/components/PublicDocumentShareButton.vue'

defineProps({
  isDark: { type: Boolean, default: false },
})
</script>

<template>
  <PublicDocumentShareButton :is-dark="isDark" />
</template>
