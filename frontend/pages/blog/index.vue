<template>
  <div class="min-h-screen bg-gray-950 text-white">
    <!-- Header -->
    <header class="border-b border-gray-800/50">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6 flex items-center justify-between">
        <NuxtLink to="/" class="text-emerald-400 hover:text-emerald-300 transition-colors text-sm font-medium">
          ← Project App
        </NuxtLink>
        <h1 class="text-lg font-light tracking-wide text-gray-300">Blog</h1>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex items-center justify-center py-32">
      <div class="w-8 h-8 border-2 border-emerald-400/30 border-t-emerald-400 rounded-full animate-spin" />
    </div>

    <!-- Content -->
    <main v-else class="max-w-6xl mx-auto px-4 sm:px-6 py-10">

      <!-- Empty state -->
      <div v-if="posts.length === 0" class="text-center py-32">
        <p class="text-gray-500 text-lg">No hay artículos publicados aún.</p>
      </div>

      <template v-else>
        <!-- Featured Post (Hero) -->
        <article
          v-if="featured"
          class="mb-16 group cursor-pointer"
          @click="navigateTo(`/blog/${featured.slug}`)"
        >
          <div class="relative overflow-hidden rounded-2xl bg-gray-900 border border-gray-800/50">
            <!-- Cover image -->
            <div class="aspect-[21/9] overflow-hidden">
              <img
                v-if="featured.cover_image"
                :src="featured.cover_image"
                :alt="featured.title"
                class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                loading="eager"
              />
              <div
                v-else
                class="w-full h-full bg-gradient-to-br from-emerald-900/40 to-gray-900 flex items-center justify-center"
              >
                <svg class="w-16 h-16 text-emerald-600/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
              </div>
            </div>

            <!-- Text overlay -->
            <div class="p-6 sm:p-8">
              <div class="flex items-center gap-3 mb-4">
                <span class="text-xs font-medium text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full">
                  Último artículo
                </span>
                <time
                  v-if="featured.published_at"
                  :datetime="featured.published_at"
                  class="text-xs text-gray-500"
                >
                  {{ formatDate(featured.published_at) }}
                </time>
              </div>
              <h2 class="text-2xl sm:text-3xl lg:text-4xl font-light text-white mb-3 group-hover:text-emerald-300 transition-colors leading-tight">
                {{ featured.title }}
              </h2>
              <p class="text-gray-400 text-base sm:text-lg leading-relaxed max-w-3xl">
                {{ featured.excerpt }}
              </p>
              <span class="inline-flex items-center gap-1 mt-5 text-sm text-emerald-400 group-hover:text-emerald-300 transition-colors">
                Leer artículo
                <svg class="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </span>
            </div>
          </div>
        </article>

        <!-- Other Posts Grid -->
        <section v-if="others.length > 0">
          <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-8">
            Más artículos
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <article
              v-for="post in others"
              :key="post.id"
              class="group cursor-pointer bg-gray-900/50 border border-gray-800/50 rounded-xl overflow-hidden hover:border-emerald-800/50 transition-all duration-300"
              @click="navigateTo(`/blog/${post.slug}`)"
            >
              <!-- Card image -->
              <div class="aspect-[16/9] overflow-hidden">
                <img
                  v-if="post.cover_image"
                  :src="post.cover_image"
                  :alt="post.title"
                  class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  loading="lazy"
                />
                <div
                  v-else
                  class="w-full h-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center"
                >
                  <svg class="w-10 h-10 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                  </svg>
                </div>
              </div>

              <!-- Card body -->
              <div class="p-5">
                <time
                  v-if="post.published_at"
                  :datetime="post.published_at"
                  class="text-xs text-gray-500 mb-2 block"
                >
                  {{ formatDate(post.published_at) }}
                </time>
                <h4 class="text-lg font-light text-white mb-2 group-hover:text-emerald-300 transition-colors leading-snug">
                  {{ post.title }}
                </h4>
                <p class="text-sm text-gray-400 leading-relaxed line-clamp-3">
                  {{ post.excerpt }}
                </p>
              </div>
            </article>
          </div>
        </section>
      </template>
    </main>

    <!-- Footer -->
    <footer class="border-t border-gray-800/50 mt-16">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 text-center">
        <p class="text-xs text-gray-600">
          © {{ new Date().getFullYear() }} Project App. — Todos los derechos reservados.
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useBlogStore } from '~/stores/blog';

const blogStore = useBlogStore();
const posts = computed(() => blogStore.posts);
const featured = computed(() => blogStore.featuredPost);
const others = computed(() => blogStore.otherPosts);

onMounted(() => {
  blogStore.fetchPosts();
});

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}
</script>
