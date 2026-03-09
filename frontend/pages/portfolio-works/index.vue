<template>
  <div itemscope itemtype="https://schema.org/CollectionPage">
    <!-- Navbar -->
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar />
    </div>

    <!-- Original Hero: Video + Lemon background -->
    <section itemscope itemtype="https://schema.org/WPHeader">
      <div class="p-3 h-svh">
        <div class="w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2">
          <div class="absolute z-10 bottom-0 flex items-center bg-transparent px-16 py-24 order-2 xl:bg-lemon xl:top-0 xl:relative xl:z-0">
            <h1 itemprop="headline">
              <span class="text-4xl font-light text-esmerald lg:text-6xl">{{ messages.header_title }}</span>
              <span class="sr-only"> - Project App. Portfolio</span><br />
              <span class="text-md font-medium text-esmerald" itemprop="description">{{ messages.header_subtitle }}</span>
              <span class="sr-only">by Project App.</span>
            </h1>
          </div>
          <div class="order-1" itemscope itemtype="https://schema.org/VideoObject">
            <div class="relative w-full h-svh overflow-hidden">
              <video ref="backgroundVideo" autoplay muted loop playsinline class="absolute inset-0 w-auto h-full object-cover" itemprop="contentUrl">
                <source :src="vidAbstractGradient" type="video/mp4" />
                Your browser does not support the video tag.
                <span class="sr-only">Project App. video presentation</span>
              </video>
              <meta itemprop="name" content="Project App. Portfolio Background Video" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Transforming Ideas section -->
    <section class="px-3" itemscope itemtype="https://schema.org/CreativeWorkSeries">
      <div class="mt-32 max-w-7xl mx-auto sm:px-6 lg:mt-52 lg:px-8">
        <h1 class="text-5xl font-light text-esmerald" itemprop="name">
          {{ messages.section_title }}
          <span class="sr-only">by Project App.</span>
        </h1>
        <h2 class="text-4xl font-light text-esmerald mt-20" itemprop="alternativeHeadline">
          {{ messages.section_subtitle }}
          <span class="sr-only">Project App. portfolio</span>
        </h2>
        <p class="text-md font-light text-esmerald mt-6" itemprop="description">
          *{{ messages.custom_software_notice }}
          <span class="sr-only">Project App.</span>
        </p>
        <p class="text-2md font-light text-esmerald mt-3" itemprop="description">
          *{{ messages.dynamic_web_notice }}
          <span class="sr-only">Project App. specializes in web solutions</span>
        </p>

        <!-- Loading -->
        <div v-if="portfolioStore.isLoading" class="flex items-center justify-center py-24">
          <div class="w-8 h-8 border-2 border-esmerald/30 border-t-esmerald rounded-full animate-spin" />
        </div>

        <!-- Empty state -->
        <div v-else-if="works.length === 0" class="text-center py-24">
          <p class="text-green-light text-lg font-regular">
            {{ isEnglish ? 'No projects published yet.' : 'No hay proyectos publicados aún.' }}
          </p>
        </div>

        <!-- Awwwards-style project grid (replaces old simple cards) -->
        <div v-else ref="worksGrid" class="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:mt-24" role="list" aria-label="Portfolio projects">
          <article
            v-for="work in works"
            :key="work.id"
            class="group cursor-pointer"
            itemscope
            itemtype="https://schema.org/CreativeWork"
            itemprop="workExample"
            @click="navigateTo(localePath(`/portfolio-works/${work.slug}`))"
          >
            <!-- Card image with hover overlay -->
            <div class="relative border border-gray-200 rounded-lg overflow-hidden">
              <img
                v-if="work.cover_image"
                :src="work.cover_image"
                :alt="`${work.title} - Project App. portfolio project`"
                class="w-full h-auto object-cover group-hover:scale-105 transition-transform duration-700"
                loading="lazy"
                itemprop="image"
              />
              <div
                v-else
                class="w-full aspect-[4/3] bg-gradient-to-br from-esmerald-light to-gray-100 flex items-center justify-center"
              >
                <svg class="w-12 h-12 text-esmerald/15" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>

              <!-- Hover overlay with share + open-in-new-tab -->
              <div class="absolute inset-0 bg-esmerald-dark/0 group-hover:bg-esmerald-dark/40 transition-all duration-300 flex items-start justify-end p-3 opacity-0 group-hover:opacity-100">
                <div class="flex items-center gap-2">
                  <button
                    class="w-9 h-9 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center text-esmerald hover:bg-white hover:scale-110 transition-all shadow-lg"
                    :title="isEnglish ? 'Share' : 'Compartir'"
                    @click.stop="handleShare(work)"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                    </svg>
                  </button>
                  <a
                    :href="work.project_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="w-9 h-9 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center text-esmerald hover:bg-white hover:scale-110 transition-all shadow-lg"
                    :title="isEnglish ? 'Open live site' : 'Abrir sitio en vivo'"
                    @click.stop
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              </div>
            </div>

            <h3 class="mt-4 font-regular text-esmerald text-md group-hover:text-green-light transition-colors" itemprop="name">
              {{ work.title }}
              <span class="sr-only">- Project App. portfolio showcase</span>
            </h3>
            <meta itemprop="creator" content="Project App." />
            <link itemprop="url" :href="`/portfolio-works/${work.slug}`" />
          </article>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <div class="mt-32 lg:mt-52">
      <footer itemscope itemtype="https://schema.org/WPFooter">
        <Footer />
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import Navbar from '~/components/layouts/Navbar.vue';
import Footer from '~/components/layouts/Footer.vue';
import { usePortfolioWorksStore } from '~/stores/portfolio_works';
import { useMessages } from '~/composables/useMessages';
import { useFreeResources } from '~/composables/useFreeResources';
import { staggerFadeUp } from '~/animations';

import vidAbstractGradient from '~/assets/videos/webDevelopments/abstractGradientBackground.mp4';

useSeoHead('portfolioWorks');

const localePath = useLocalePath();
const { locale } = useI18n();
const { messages } = useMessages();
const portfolioStore = usePortfolioWorksStore();
const works = computed(() => portfolioStore.works);
const isEnglish = computed(() => locale.value.startsWith('en'));
const portfolioLang = computed(() => isEnglish.value ? 'en' : 'es');

const backgroundVideo = ref(null);
const worksGrid = ref(null);

function runGridAnimations() {
  nextTick(() => {
    if (worksGrid.value) {
      const cards = worksGrid.value.querySelectorAll('article');
      if (cards.length) staggerFadeUp(Array.from(cards), { delay: 0.15 });
    }
  });
}

onMounted(() => {
  portfolioStore.fetchWorks(portfolioLang.value);
});

watch(works, () => { runGridAnimations(); });

useFreeResources({ videos: [backgroundVideo] });

function handleShare(work) {
  const url = `${window.location.origin}${localePath(`/portfolio-works/${work.slug}`)}`;
  if (navigator.share) {
    navigator.share({ title: work.title, text: work.excerpt || '', url });
  } else {
    navigator.clipboard.writeText(url);
  }
}
</script>
