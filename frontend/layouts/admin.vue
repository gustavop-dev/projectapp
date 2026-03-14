<template>
  <div class="admin-layout min-h-screen transition-colors duration-200" :class="isDark ? 'bg-gray-900' : 'bg-gray-50'">
    <!-- Top navigation bar -->
    <nav class="border-b px-4 sm:px-6 py-3 sm:py-4 transition-colors duration-200" :class="isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'">
      <div class="flex items-center justify-between">
        <NuxtLink :to="localePath('/panel')" class="text-lg sm:text-xl font-bold transition-colors" :class="isDark ? 'text-emerald-400 hover:text-emerald-300' : 'text-emerald-600 hover:text-emerald-700'">
          ProjectApp Admin
        </NuxtLink>
        <div class="flex items-center gap-3">
          <!-- Dark mode toggle -->
          <button
            class="p-1.5 rounded-lg transition-colors"
            :class="isDark ? 'text-yellow-400 hover:bg-gray-700' : 'text-gray-400 hover:bg-gray-100'"
            @click="toggle"
            :title="isDark ? 'Modo claro' : 'Modo oscuro'"
          >
            <svg v-if="isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
          <!-- Mobile menu toggle -->
          <button class="sm:hidden p-1.5 rounded-lg transition-colors" :class="isDark ? 'text-gray-400 hover:bg-gray-700' : 'text-gray-500 hover:bg-gray-100'" @click="mobileMenuOpen = !mobileMenuOpen">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <!-- Desktop links -->
          <div class="hidden sm:flex items-center gap-4">
            <span class="text-gray-300 dark:text-gray-600">|</span>
            <NuxtLink
              :to="localePath('/panel/proposals')"
              class="text-sm font-medium transition-colors border-b-2 pb-0.5"
              :class="isModule('proposals')
                ? 'text-emerald-600 border-emerald-600 dark:text-emerald-400 dark:border-emerald-400'
                : 'text-gray-500 border-transparent hover:text-emerald-600 dark:text-gray-400 dark:hover:text-emerald-400'"
            >
              Propuestas
            </NuxtLink>
            <NuxtLink
              :to="localePath('/panel/clients')"
              class="text-sm font-medium transition-colors border-b-2 pb-0.5"
              :class="isModule('clients')
                ? 'text-emerald-600 border-emerald-600 dark:text-emerald-400 dark:border-emerald-400'
                : 'text-gray-500 border-transparent hover:text-emerald-600 dark:text-gray-400 dark:hover:text-emerald-400'"
            >
              Clientes
            </NuxtLink>
            <NuxtLink
              :to="localePath('/panel/blog')"
              class="text-sm font-medium transition-colors border-b-2 pb-0.5"
              :class="isModule('blog')
                ? 'text-emerald-600 border-emerald-600 dark:text-emerald-400 dark:border-emerald-400'
                : 'text-gray-500 border-transparent hover:text-emerald-600 dark:text-gray-400 dark:hover:text-emerald-400'"
            >
              Blog
            </NuxtLink>
            <NuxtLink
              :to="localePath('/panel/portfolio')"
              class="text-sm font-medium transition-colors border-b-2 pb-0.5"
              :class="isModule('portfolio')
                ? 'text-emerald-600 border-emerald-600 dark:text-emerald-400 dark:border-emerald-400'
                : 'text-gray-500 border-transparent hover:text-emerald-600 dark:text-gray-400 dark:hover:text-emerald-400'"
            >
              Portfolio
            </NuxtLink>
            <span class="text-gray-200 dark:text-gray-600">|</span>
            <a
              href="/sitemap.xml"
              target="_blank"
              class="text-xs text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-1"
              title="Abrir sitemap.xml (se regenera automáticamente con blog + portfolio publicados)"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              Sitemap
            </a>
            <a href="/admin/" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors">
              Django Admin →
            </a>
          </div>
        </div>
      </div>
      <!-- Mobile menu -->
      <div v-if="mobileMenuOpen" class="sm:hidden mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 flex flex-col gap-2">
        <NuxtLink
          :to="localePath('/panel/proposals')"
          class="text-sm font-medium px-2 py-1.5 rounded-lg transition-colors"
          :class="isModule('proposals')
            ? 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/30'
            : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700'"
          @click="mobileMenuOpen = false"
        >
          Propuestas
        </NuxtLink>
        <NuxtLink
          :to="localePath('/panel/clients')"
          class="text-sm font-medium px-2 py-1.5 rounded-lg transition-colors"
          :class="isModule('clients')
            ? 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/30'
            : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700'"
          @click="mobileMenuOpen = false"
        >
          Clientes
        </NuxtLink>
        <NuxtLink
          :to="localePath('/panel/blog')"
          class="text-sm font-medium px-2 py-1.5 rounded-lg transition-colors"
          :class="isModule('blog')
            ? 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/30'
            : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700'"
          @click="mobileMenuOpen = false"
        >
          Blog
        </NuxtLink>
        <NuxtLink
          :to="localePath('/panel/portfolio')"
          class="text-sm font-medium px-2 py-1.5 rounded-lg transition-colors"
          :class="isModule('portfolio')
            ? 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/30'
            : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700'"
          @click="mobileMenuOpen = false"
        >
          Portfolio
        </NuxtLink>
        <a href="/admin/" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 px-2 py-1.5 transition-colors">
          Django Admin →
        </a>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8" :class="isDark ? 'text-gray-200' : ''">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useDarkMode } from '~/composables/useDarkMode';

const localePath = useLocalePath();
const route = useRoute();
const mobileMenuOpen = ref(false);
const { isDark, toggle } = useDarkMode();

function isModule(module) {
  return route.path.includes(`/panel/${module}`);
}
</script>
