<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold text-text-default">Hostings</h1>
    <p class="text-sm text-text-muted">Vista en construcción.</p>
  </div>
</template>

<script setup>
definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });
</script>
