<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
    <div class="text-center">
      <h1 class="text-2xl font-light text-gray-900 mb-4">ProjectApp Admin</h1>
      <p class="text-gray-500 text-sm mb-6">
        Inicia sesión a través del panel de administración de Django.
      </p>
      <a
        href="/admin/"
        class="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white rounded-xl
               font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
      >
        Ir al Django Admin →
      </a>
    </div>
  </div>
</template>

<script setup>
definePageMeta({ layout: false });
</script>
