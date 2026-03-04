<template>
  <div class="admin-layout min-h-screen bg-gray-50">
    <!-- Top navigation bar -->
    <nav class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <NuxtLink to="/panel" class="text-xl font-bold text-emerald-600 hover:text-emerald-700 transition-colors">
          ProjectApp Admin
        </NuxtLink>
        <span class="text-gray-300">|</span>
        <NuxtLink
          to="/panel/proposals"
          class="text-sm font-medium transition-colors border-b-2 pb-0.5"
          :class="isModule('proposals')
            ? 'text-emerald-600 border-emerald-600'
            : 'text-gray-500 border-transparent hover:text-emerald-600'"
        >
          Propuestas
        </NuxtLink>
        <NuxtLink
          to="/panel/blog"
          class="text-sm font-medium transition-colors border-b-2 pb-0.5"
          :class="isModule('blog')
            ? 'text-emerald-600 border-emerald-600'
            : 'text-gray-500 border-transparent hover:text-emerald-600'"
        >
          Blog
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
const route = useRoute();

function isModule(module) {
  return route.path.includes(`/panel/${module}`);
}
</script>
