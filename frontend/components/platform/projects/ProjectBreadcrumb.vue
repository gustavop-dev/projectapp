<template>
  <nav class="flex items-center gap-2 text-sm text-green-light">
    <NuxtLink :to="localePath('/platform/projects')" class="hover:text-text-brand">Proyectos</NuxtLink>
    <span class="text-green-light/40">/</span>
    <span class="text-text-default">{{ projectName || '…' }}</span>
  </nav>
</template>

<script setup>
defineProps({ projectName: { type: String, default: '' } })
const localePath = useLocalePath()
</script>
