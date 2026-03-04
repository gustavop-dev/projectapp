<template>
  <div class="admin-layout min-h-screen bg-gray-50">
    <!-- Top navigation bar -->
    <nav class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <NuxtLink to="/admin" class="text-xl font-bold text-emerald-600 hover:text-emerald-700 transition-colors">
          ProjectApp Admin
        </NuxtLink>
        <span class="text-gray-300">|</span>
        <NuxtLink
          to="/admin/proposals"
          class="text-gray-600 hover:text-emerald-600 transition-colors text-sm font-medium"
          active-class="text-emerald-600"
        >
          Propuestas
        </NuxtLink>
      </div>
      <div class="flex items-center gap-4">
        <a href="/admin/" class="text-sm text-gray-500 hover:text-gray-700 transition-colors">
          Django Admin →
        </a>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-6 py-8">
      <slot />
    </main>
  </div>
</template>

<script setup>
</script>
