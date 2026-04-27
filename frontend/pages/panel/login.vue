<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
    <div class="text-center">
      <h1 class="text-2xl font-light text-text-default mb-4">ProjectApp Admin</h1>
      <p class="text-text-muted text-sm mb-6">
        Inicia sesión a través del panel de administración de Django.
      </p>
      <a
        href="/admin/"
        class="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-xl
               font-medium text-sm hover:bg-primary-strong transition-colors shadow-sm"
      >
        Ir al Django Admin →
      </a>
    </div>
  </div>
</template>

<script setup>
definePageMeta({ layout: false });
</script>
