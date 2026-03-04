<template>
  <div class="bg-lemon" itemscope itemtype="https://schema.org/Blog">
    <!-- Navbar -->
    <header class="fixed top-0 left-0 w-full z-50">
      <Navbar />
    </header>

    <!-- Hero -->
    <section class="px-3 pt-32 pb-16 lg:pt-52 lg:pb-24" aria-labelledby="blog-title">
      <div class="max-w-7xl mx-auto">
        <h1 id="blog-title" class="text-6xl lg:text-8xl font-light text-esmerald">Blog</h1>
        <p class="mt-4 text-lg text-green-light font-regular max-w-xl">
          {{ isEnglish ? 'Insights and trends in AI, software development, and digital transformation.' : 'Novedades y tendencias en IA, desarrollo de software y transformación digital.' }}
        </p>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex items-center justify-center py-32 bg-esmerald-light">
      <div class="w-8 h-8 border-2 border-esmerald/30 border-t-esmerald rounded-full animate-spin" />
    </div>

    <!-- Content -->
    <main v-else class="bg-esmerald-light px-3 py-16 lg:py-24">
      <div class="max-w-7xl mx-auto">

        <!-- Empty state -->
        <div v-if="posts.length === 0" class="text-center py-32">
          <p class="text-green-light text-lg font-regular">
            {{ isEnglish ? 'No articles published yet.' : 'No hay artículos publicados aún.' }}
          </p>
        </div>

        <template v-else>
          <!-- Featured Post (Hero Card) -->
          <article
            v-if="featured"
            class="mb-16 group cursor-pointer"
            @click="navigateTo(`/blog/${featured.slug}`)"
            itemscope
            itemtype="https://schema.org/BlogPosting"
          >
            <div class="relative overflow-hidden rounded-xl bg-white border border-gray-200/60">
              <!-- Cover image -->
              <div class="aspect-[21/9] overflow-hidden">
                <img
                  v-if="featured.cover_image"
                  :src="featured.cover_image"
                  :alt="featured.title"
                  class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                  loading="eager"
                  itemprop="image"
                />
                <div
                  v-else
                  class="w-full h-full bg-gradient-to-br from-lemon/40 to-esmerald-light flex items-center justify-center"
                >
                  <svg class="w-16 h-16 text-esmerald/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                  </svg>
                </div>
              </div>

              <!-- Text -->
              <div class="p-6 sm:p-8">
                <div class="flex items-center gap-3 mb-4">
                  <span class="text-xs font-medium text-esmerald bg-lemon px-3 py-1 rounded-full">
                    {{ isEnglish ? 'Latest article' : 'Último artículo' }}
                  </span>
                  <time
                    v-if="featured.published_at"
                    :datetime="featured.published_at"
                    class="text-xs text-green-light"
                    itemprop="datePublished"
                  >
                    {{ formatDate(featured.published_at) }}
                  </time>
                </div>
                <h2 class="text-2xl sm:text-3xl lg:text-4xl font-light text-esmerald mb-3 group-hover:text-esmerald/70 transition-colors leading-tight" itemprop="headline">
                  {{ featured.title }}
                </h2>
                <p class="text-green-light text-base sm:text-lg leading-relaxed max-w-3xl font-regular" itemprop="description">
                  {{ featured.excerpt }}
                </p>
                <span class="inline-flex items-center gap-1 mt-5 text-sm text-esmerald font-regular group-hover:text-esmerald/70 transition-colors">
                  {{ isEnglish ? 'Read article' : 'Leer artículo' }}
                  <svg class="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </div>
          </article>

          <!-- Other Posts Grid -->
          <section v-if="others.length > 0">
            <h3 class="text-sm font-regular text-green-light uppercase tracking-wider mb-8">
              {{ isEnglish ? 'More articles' : 'Más artículos' }}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <article
                v-for="post in others"
                :key="post.id"
                class="group cursor-pointer bg-white border border-gray-200/60 rounded-xl overflow-hidden hover:shadow-lg transition-all duration-300"
                @click="navigateTo(`/blog/${post.slug}`)"
                itemscope
                itemtype="https://schema.org/BlogPosting"
              >
                <!-- Card image -->
                <div class="aspect-[16/9] overflow-hidden">
                  <img
                    v-if="post.cover_image"
                    :src="post.cover_image"
                    :alt="post.title"
                    class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                    itemprop="image"
                  />
                  <div
                    v-else
                    class="w-full h-full bg-gradient-to-br from-lemon/30 to-esmerald-light flex items-center justify-center"
                  >
                    <svg class="w-10 h-10 text-esmerald/15" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                    </svg>
                  </div>
                </div>

                <!-- Card body -->
                <div class="p-5">
                  <time
                    v-if="post.published_at"
                    :datetime="post.published_at"
                    class="text-xs text-green-light mb-2 block"
                    itemprop="datePublished"
                  >
                    {{ formatDate(post.published_at) }}
                  </time>
                  <h4 class="text-lg font-light text-esmerald mb-2 group-hover:text-esmerald/70 transition-colors leading-snug" itemprop="headline">
                    {{ post.title }}
                  </h4>
                  <p class="text-sm text-green-light leading-relaxed line-clamp-3 font-regular" itemprop="description">
                    {{ post.excerpt }}
                  </p>
                </div>
              </article>
            </div>
          </section>
        </template>
      </div>
    </main>

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

const { locale } = useI18n();
const blogStore = useBlogStore();
const posts = computed(() => blogStore.posts);
const featured = computed(() => blogStore.featuredPost);
const others = computed(() => blogStore.otherPosts);
const isEnglish = computed(() => locale.value.startsWith('en'));

const blogLang = computed(() => isEnglish.value ? 'en' : 'es');

onMounted(() => {
  blogStore.fetchPosts(blogLang.value);
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
