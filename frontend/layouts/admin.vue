<template>
  <div class="admin-layout min-h-screen bg-gray-50">
    <!-- Top navigation bar -->
    <nav class="bg-white border-b border-gray-200 px-4 sm:px-6 py-3 sm:py-4">
      <div class="flex items-center justify-between">
        <NuxtLink to="/panel" class="text-lg sm:text-xl font-bold text-emerald-600 hover:text-emerald-700 transition-colors">
          ProjectApp Admin
        </NuxtLink>
        <div class="flex items-center gap-3">
          <!-- Mobile menu toggle -->
          <button class="sm:hidden p-1.5 rounded-lg hover:bg-gray-100 text-gray-500" @click="mobileMenuOpen = !mobileMenuOpen">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <!-- Desktop links -->
          <div class="hidden sm:flex items-center gap-4">
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
              to="/panel/clients"
              class="text-sm font-medium transition-colors border-b-2 pb-0.5"
              :class="isModule('clients')
                ? 'text-emerald-600 border-emerald-600'
                : 'text-gray-500 border-transparent hover:text-emerald-600'"
            >
              Clientes
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
            <NuxtLink
              to="/panel/portfolio"
              class="text-sm font-medium transition-colors border-b-2 pb-0.5"
              :class="isModule('portfolio')
                ? 'text-emerald-600 border-emerald-600'
                : 'text-gray-500 border-transparent hover:text-emerald-600'"
            >
              Portfolio
            </NuxtLink>
            <span class="text-gray-200">|</span>
            <a
              href="/sitemap.xml"
              target="_blank"
              class="text-xs text-gray-400 hover:text-emerald-600 transition-colors flex items-center gap-1"
              title="Abrir sitemap.xml (se regenera automáticamente con blog + portfolio publicados)"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              Sitemap
            </a>
            <a href="/admin/" class="text-sm text-gray-500 hover:text-gray-700 transition-colors">
              Django Admin →
            </a>
          </div>
        </div>
      </div>
      <!-- Mobile menu -->
      <div v-if="mobileMenuOpen" class="sm:hidden mt-3 pt-3 border-t border-gray-100 flex flex-col gap-2">
        <NuxtLink
          to="/panel/proposals"
          class="text-sm font-medium px-2 py-1.5 rounded-lg transition-colors"
          :class="isModule('proposals')
            ? 'text-emerald-600 bg-emerald-50'
            : 'text-gray-600 hover:bg-gray-50'"
          @click="mobileMenuOpen = false"
        >
          Propuestas
        </NuxtLink>
        <NuxtLink
          to="/panel/clients"
          class="text-sm font-medium px-2 py-1.5 rounded-lg transition-colors"
          :class="isModule('clients')
            ? 'text-emerald-600 bg-emerald-50'
            : 'text-gray-600 hover:bg-gray-50'"
          @click="mobileMenuOpen = false"
        >
          Clientes
        </NuxtLink>
        <NuxtLink
          to="/panel/blog"
          class="text-sm font-medium px-2 py-1.5 rounded-lg transition-colors"
          :class="isModule('blog')
            ? 'text-emerald-600 bg-emerald-50'
            : 'text-gray-600 hover:bg-gray-50'"
          @click="mobileMenuOpen = false"
        >
          Blog
        </NuxtLink>
        <NuxtLink
          to="/panel/portfolio"
          class="text-sm font-medium px-2 py-1.5 rounded-lg transition-colors"
          :class="isModule('portfolio')
            ? 'text-emerald-600 bg-emerald-50'
            : 'text-gray-600 hover:bg-gray-50'"
          @click="mobileMenuOpen = false"
        >
          Portfolio
        </NuxtLink>
        <a href="/admin/" class="text-sm text-gray-500 hover:text-gray-700 px-2 py-1.5 transition-colors">
          Django Admin →
        </a>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const route = useRoute();
const mobileMenuOpen = ref(false);

function isModule(module) {
  return route.path.includes(`/panel/${module}`);
}
</script>
