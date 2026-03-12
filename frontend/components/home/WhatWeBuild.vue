<template>
  <section class="px-3 lg:px-8 py-6">
    <div class="gradient-banner relative w-full rounded-[2rem] sm:rounded-[3rem] overflow-hidden">

      <!-- Animated gradient background -->
      <BackgroundGradientAnimation
        gradient-background-start="rgb(180, 40, 50)"
        gradient-background-end="rgb(40, 40, 60)"
        first-color="200, 60, 40"
        second-color="210, 90, 30"
        third-color="160, 50, 120"
        fourth-color="80, 50, 80"
        fifth-color="230, 80, 60"
        pointer-color="190, 60, 50"
        size="100%"
        blending-value="hard-light"
        :interactive="true"
        container-class-name="!w-full !h-full !absolute !inset-0"
      />

      <!-- Grain noise overlay -->
      <div class="grain-overlay"></div>

      <!-- Content -->
      <div class="relative z-10 flex flex-col h-full px-6 sm:px-10 lg:px-16 py-10 lg:py-14">

        <!-- Title + Subtitle -->
        <div class="mb-8 lg:mb-10">
          <h2 class="font-serif italic text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-white leading-tight mb-3">
            {{ messages?.whatWeBuild?.title || '¿Qué desarrollamos?' }}
          </h2>
          <p class="text-sm sm:text-base lg:text-lg text-white/70 max-w-2xl font-light">
            {{ messages?.whatWeBuild?.subtitle || 'Tienes un equipo de diseñadores, desarrolladores y QA listos para hacer realidad tu proyecto.' }}
          </p>
        </div>

        <!-- Two-column: Tabs left + Content right -->
        <div class="flex flex-col lg:flex-row gap-4 lg:gap-6 flex-1">

          <!-- Left: Service tabs -->
          <div class="flex flex-col gap-2 lg:w-2/5">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              @click="activeTab = tab.key"
              class="tab-btn"
              :class="activeTab === tab.key ? 'tab-btn--active' : 'tab-btn--inactive'"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" :d="tab.icon" />
              </svg>
              <span class="text-base sm:text-lg font-medium">{{ tab.label }}</span>
            </button>
          </div>

          <!-- Right: Content bubble -->
          <div class="content-bubble lg:w-3/5">
            <Transition name="fade" mode="out-in">

              <!-- Web -->
              <div v-if="activeTab === 'web'" key="web">
                <p class="text-white/80 text-sm sm:text-base leading-relaxed mb-5">
                  {{ messages?.whatWeBuild?.web?.description || 'Sitios que convierten visitantes en clientes. Diseño profesional, SEO optimizado y experiencia de usuario impecable.' }}
                </p>
                <ul class="space-y-3 mb-5">
                  <li
                    v-for="(item, i) in (messages?.whatWeBuild?.web?.items || webItemsFallback)"
                    :key="i"
                    class="flex items-center gap-3 text-white text-sm sm:text-base font-medium"
                  >
                    <span class="w-1.5 h-1.5 bg-white rounded-full flex-shrink-0" />
                    {{ item }}
                  </li>
                </ul>
                <a
                  :href="messages?.hero?.cta_whatsapp_url || 'https://wa.me/573238122373'"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-slate-900 rounded-full text-sm font-semibold hover:bg-white/90 transition-all hover:scale-105"
                >
                  {{ messages?.whatWeBuild?.web?.cta || 'Cotizar proyecto web' }}
                </a>
              </div>

              <!-- Apps -->
              <div v-else-if="activeTab === 'apps'" key="apps">
                <p class="text-white/80 text-sm sm:text-base leading-relaxed mb-5">
                  {{ messages?.whatWeBuild?.apps?.description || '¿Sabías que el 70% del tráfico digital viene de móviles? Una app nativa ofrece velocidad, notificaciones push y presencia en App Store y Google Play.' }}
                </p>
                <ul class="space-y-3 mb-5">
                  <li
                    v-for="(item, i) in (messages?.whatWeBuild?.apps?.items || appsItemsFallback)"
                    :key="i"
                    class="flex items-center gap-3 text-white text-sm sm:text-base font-medium"
                  >
                    <span class="w-1.5 h-1.5 bg-white rounded-full flex-shrink-0" />
                    {{ item }}
                  </li>
                </ul>
                <div class="flex flex-wrap gap-3">
                  <NuxtLink
                    :to="localePath('/landing-apps')"
                    class="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-slate-900 rounded-full text-sm font-semibold hover:bg-white/90 transition-all hover:scale-105"
                  >
                    {{ messages?.whatWeBuild?.apps?.cta || 'Desarrollo de Apps' }}
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" /></svg>
                  </NuxtLink>
                  <a
                    :href="messages?.hero?.cta_whatsapp_url || 'https://wa.me/573238122373'"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-2 px-5 py-2.5 border border-white/30 text-white rounded-full text-sm font-semibold hover:bg-white/10 transition-all hover:scale-105"
                  >
                    {{ messages?.whatWeBuild?.apps?.ctaQuote || 'Cotizar app' }}
                  </a>
                </div>
              </div>

              <!-- Software -->
              <div v-else-if="activeTab === 'software'" key="software">
                <p class="text-white/80 text-sm sm:text-base leading-relaxed mb-5">
                  {{ messages?.whatWeBuild?.software?.description || 'Automatiza procesos, integra sistemas y escala tu operación con plataformas construidas específicamente para tu empresa.' }}
                </p>
                <ul class="space-y-3 mb-5">
                  <li
                    v-for="(item, i) in (messages?.whatWeBuild?.software?.items || softwareItemsFallback)"
                    :key="i"
                    class="flex items-center gap-3 text-white text-sm sm:text-base font-medium"
                  >
                    <span class="w-1.5 h-1.5 bg-white rounded-full flex-shrink-0" />
                    {{ item }}
                  </li>
                </ul>
                <a
                  :href="messages?.hero?.cta_whatsapp_url || 'https://wa.me/573238122373'"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-slate-900 rounded-full text-sm font-semibold hover:bg-white/90 transition-all hover:scale-105"
                >
                  {{ messages?.whatWeBuild?.software?.cta || 'Cotizar software' }}
                </a>
              </div>

            </Transition>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import BackgroundGradientAnimation from '~/components/ui/BackgroundGradientAnimation.vue'
import { useMessages } from '~/composables/useMessages'

const localePath = useLocalePath()
const { messages } = useMessages()

const activeTab = ref('web')

const tabs = computed(() => [
  {
    key: 'web',
    label: messages.value?.whatWeBuild?.web?.title || 'Diseño Web',
    icon: 'M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A8.966 8.966 0 0 1 3 12c0-1.264.26-2.466.732-3.558'
  },
  {
    key: 'apps',
    label: messages.value?.whatWeBuild?.apps?.title || 'Apps Móviles',
    icon: 'M10.5 1.5H8.25A2.25 2.25 0 0 0 6 3.75v16.5a2.25 2.25 0 0 0 2.25 2.25h7.5A2.25 2.25 0 0 0 18 20.25V3.75a2.25 2.25 0 0 0-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3'
  },
  {
    key: 'software',
    label: messages.value?.whatWeBuild?.software?.title || 'Software a la Medida',
    icon: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.248a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28ZM15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z'
  }
])

const webItemsFallback = ['Landing Pages', 'E-Commerce', 'Plataformas Web']
const appsItemsFallback = ['iOS & Android nativas', 'Flutter & React Native', 'Publicación en tiendas']
const softwareItemsFallback = ['CRMs & ERPs personalizados', 'Automatización de procesos', 'Integraciones API', 'Dashboards & reportes']
</script>

<style scoped>
.font-serif {
  font-family: 'DM Serif Display', serif;
}

.gradient-banner {
  min-height: 50vh;
}

.grain-overlay {
  position: absolute;
  inset: -50%;
  width: 200%;
  height: 200%;
  z-index: 1;
  pointer-events: none;
  opacity: 0.35;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  animation: grainDrift 8s linear infinite;
}

@keyframes grainDrift {
  0% { transform: translate(0, 0); }
  25% { transform: translate(-5%, 5%); }
  50% { transform: translate(5%, -3%); }
  75% { transform: translate(-3%, -5%); }
  100% { transform: translate(0, 0); }
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.25rem;
  border-radius: 1rem;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  text-align: left;
  cursor: pointer;
  border: none;
}

.tab-btn--active {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(12px);
  color: #fff;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.3);
}

.tab-btn--inactive {
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
}

.tab-btn--inactive:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
}

.content-bubble {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1.5rem;
  padding: 1.5rem;
}

@media (min-width: 640px) {
  .content-bubble {
    padding: 2rem;
  }
}

/* Fade transition for content swap */
.fade-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
