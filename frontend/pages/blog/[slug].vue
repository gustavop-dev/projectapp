<template>
  <div class="bg-lemon" itemscope itemtype="https://schema.org/BlogPosting">
    <!-- Navbar -->
    <header class="fixed top-0 left-0 w-full z-50">
      <Navbar />
    </header>

    <!-- Hero spacer + back link -->
    <section class="px-3 pt-32 pb-8 lg:pt-44 lg:pb-12">
      <div class="max-w-4xl mx-auto">
        <NuxtLink
          to="/blog"
          class="inline-flex items-center gap-2 text-sm text-esmerald font-regular bg-window-black bg-opacity-40 backdrop-blur-md px-4 py-2 rounded-xl hover:bg-esmerald hover:text-white transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          {{ isEnglish ? 'Back to blog' : 'Volver al blog' }}
        </NuxtLink>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex items-center justify-center py-32">
      <div class="w-8 h-8 border-2 border-esmerald/30 border-t-esmerald rounded-full animate-spin" />
    </div>

    <!-- Not found -->
    <div v-else-if="blogStore.error === 'not_found'" class="text-center py-32">
      <h2 class="text-2xl font-light text-esmerald mb-4">
        {{ isEnglish ? 'Article not found' : 'Artículo no encontrado' }}
      </h2>
      <NuxtLink to="/blog" class="text-esmerald hover:text-esmerald/70 text-sm font-regular">
        {{ isEnglish ? 'Back to blog' : 'Volver al blog' }}
      </NuxtLink>
    </div>

    <!-- Article -->
    <template v-else-if="post">
      <!-- Title + excerpt on lemon background -->
      <section class="px-3 pb-16">
        <div class="max-w-4xl mx-auto">
          <time
            v-if="post.published_at"
            :datetime="post.published_at"
            class="text-sm text-green-light block mb-4 font-regular"
            itemprop="datePublished"
          >
            {{ formatDate(post.published_at) }}
          </time>
          <h1 class="text-3xl sm:text-4xl lg:text-5xl font-light text-esmerald leading-tight mb-4" itemprop="headline">
            {{ post.title }}
          </h1>
          <p class="text-lg text-green-light leading-relaxed font-regular" itemprop="description">
            {{ post.excerpt }}
          </p>
        </div>
      </section>

      <!-- Cover image -->
      <div v-if="post.cover_image" class="px-3 pb-8">
        <div class="max-w-4xl mx-auto rounded-xl overflow-hidden">
          <img
            :src="post.cover_image"
            :alt="post.title"
            class="w-full h-auto object-cover"
            loading="eager"
            itemprop="image"
          />
        </div>
      </div>

      <!-- Content on light background -->
      <article class="bg-esmerald-light px-3 py-16 lg:py-24">
        <div class="max-w-4xl mx-auto">
          <div
            class="blog-content"
            v-html="post.content"
          />

          <!-- Sources -->
          <section v-if="post.sources && post.sources.length > 0" class="mt-16 pt-8 border-t border-gray-300/50">
            <h3 class="text-sm font-regular text-green-light uppercase tracking-wider mb-5">
              {{ isEnglish ? 'Sources consulted' : 'Fuentes consultadas' }}
            </h3>
            <ul class="space-y-3">
              <li v-for="(source, idx) in post.sources" :key="idx">
                <a
                  :href="source.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-2 text-esmerald hover:text-esmerald/70 transition-colors text-sm font-regular"
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
          <div class="mt-16 pt-8 border-t border-gray-300/50">
            <NuxtLink
              to="/blog"
              class="inline-flex items-center gap-2 text-sm text-green-light hover:text-esmerald transition-colors font-regular"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              {{ isEnglish ? 'Back to blog' : 'Volver al blog' }}
            </NuxtLink>
          </div>
        </div>
      </article>
    </template>

    <!-- Contact + Footer -->
    <ContactSection />
    <FooterSection />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import Navbar from '~/components/layouts/Navbar.vue';
import ContactSection from '~/views-legacy/partials/ContactSection.vue';
import FooterSection from '~/views-legacy/partials/FooterSection.vue';
import { useBlogStore } from '~/stores/blog';

const route = useRoute();
const { locale } = useI18n();
const blogStore = useBlogStore();
const post = computed(() => blogStore.currentPost);
const isEnglish = computed(() => locale.value.startsWith('en'));
const blogLang = computed(() => isEnglish.value ? 'en' : 'es');

onMounted(() => {
  blogStore.fetchPost(route.params.slug, blogLang.value);
});

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString(isEnglish.value ? 'en-US' : 'es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}
</script>

<style scoped>
.blog-content :deep(h2) {
  font-family: 'Ubuntu-Light', sans-serif;
  font-size: 1.75rem;
  color: #002921;
  margin-top: 2.5rem;
  margin-bottom: 1rem;
}

.blog-content :deep(h3) {
  font-family: 'Ubuntu-Regular', sans-serif;
  font-size: 1.25rem;
  color: #002921;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
}

.blog-content :deep(p) {
  font-family: 'Ubuntu-Regular', sans-serif;
  color: #809490;
  line-height: 1.75;
  margin-bottom: 1rem;
}

.blog-content :deep(a) {
  color: #002921;
  text-decoration: underline;
}

.blog-content :deep(strong) {
  color: #002921;
  font-family: 'Ubuntu-Medium', sans-serif;
}

.blog-content :deep(ul),
.blog-content :deep(ol) {
  color: #809490;
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.blog-content :deep(li) {
  margin-bottom: 0.5rem;
  font-family: 'Ubuntu-Regular', sans-serif;
}

.blog-content :deep(blockquote) {
  border-left: 3px solid #F0FF3D;
  padding-left: 1rem;
  color: #002921;
  font-style: italic;
  font-family: 'Ubuntu-Regular', sans-serif;
  margin: 1.5rem 0;
}
</style>
