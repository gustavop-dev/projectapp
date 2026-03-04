<template>
  <div class="min-h-screen bg-gray-950 text-white">
    <!-- Header -->
    <header class="border-b border-gray-800/50">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex items-center justify-between">
        <NuxtLink to="/blog" class="text-emerald-400 hover:text-emerald-300 transition-colors text-sm font-medium">
          ← Blog
        </NuxtLink>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex items-center justify-center py-32">
      <div class="w-8 h-8 border-2 border-emerald-400/30 border-t-emerald-400 rounded-full animate-spin" />
    </div>

    <!-- Not found -->
    <div v-else-if="blogStore.error === 'not_found'" class="text-center py-32">
      <h2 class="text-2xl font-light text-gray-400 mb-4">Artículo no encontrado</h2>
      <NuxtLink to="/blog" class="text-emerald-400 hover:text-emerald-300 text-sm">
        Volver al blog
      </NuxtLink>
    </div>

    <!-- Article -->
    <article v-else-if="post" class="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <!-- Meta -->
      <div class="mb-8">
        <time
          v-if="post.published_at"
          :datetime="post.published_at"
          class="text-sm text-gray-500 block mb-4"
        >
          {{ formatDate(post.published_at) }}
        </time>
        <h1 class="text-3xl sm:text-4xl lg:text-5xl font-light text-white leading-tight mb-4">
          {{ post.title }}
        </h1>
        <p class="text-lg text-gray-400 leading-relaxed">
          {{ post.excerpt }}
        </p>
      </div>

      <!-- Cover image -->
      <div v-if="post.cover_image" class="mb-12 rounded-2xl overflow-hidden">
        <img
          :src="post.cover_image"
          :alt="post.title"
          class="w-full h-auto object-cover"
          loading="eager"
        />
      </div>

      <!-- Content -->
      <div
        class="blog-content prose prose-invert prose-emerald max-w-none
               prose-headings:font-light prose-headings:text-gray-200
               prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
               prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
               prose-p:text-gray-300 prose-p:leading-relaxed prose-p:mb-4
               prose-a:text-emerald-400 prose-a:no-underline hover:prose-a:text-emerald-300
               prose-strong:text-white prose-strong:font-medium
               prose-ul:text-gray-300 prose-ol:text-gray-300
               prose-li:marker:text-emerald-600
               prose-blockquote:border-emerald-600 prose-blockquote:text-gray-400"
        v-html="post.content"
      />

      <!-- Sources -->
      <section v-if="post.sources && post.sources.length > 0" class="mt-16 pt-8 border-t border-gray-800/50">
        <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-5">
          Fuentes consultadas
        </h3>
        <ul class="space-y-3">
          <li v-for="(source, idx) in post.sources" :key="idx">
            <a
              :href="source.url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 transition-colors text-sm"
            >
              <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              {{ source.name }}
            </a>
          </li>
        </ul>
      </section>

      <!-- Back link -->
      <div class="mt-16 pt-8 border-t border-gray-800/50">
        <NuxtLink
          to="/blog"
          class="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-emerald-400 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Volver al blog
        </NuxtLink>
      </div>
    </article>

    <!-- Footer -->
    <footer class="border-t border-gray-800/50 mt-16">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8 text-center">
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

const route = useRoute();
const blogStore = useBlogStore();
const post = computed(() => blogStore.currentPost);

onMounted(() => {
  blogStore.fetchPost(route.params.slug);
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
