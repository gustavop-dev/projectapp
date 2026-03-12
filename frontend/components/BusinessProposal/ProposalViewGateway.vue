<template>
  <section class="proposal-gateway min-h-screen flex items-center justify-center bg-white px-4 py-12 sm:py-16">
    <div class="max-w-4xl w-full mx-auto">
      <!-- Header -->
      <div class="text-center mb-10 sm:mb-14">
        <h2 class="text-esmerald font-light leading-tight text-3xl sm:text-4xl md:text-5xl mb-3">
          {{ t.heading }}
        </h2>
        <p class="text-green-light font-light text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
          {{ t.subheading }}
        </p>
      </div>

      <!-- Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-5 sm:gap-6">
        <!-- Executive card -->
        <button
          type="button"
          class="gateway-card group relative bg-esmerald rounded-2xl sm:rounded-3xl p-6 sm:p-8 text-left
                 border-2 border-transparent hover:border-lemon transition-all duration-300
                 shadow-lg hover:shadow-2xl cursor-pointer"
          @click="$emit('select', 'executive')"
        >
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 bg-lemon rounded-xl flex items-center justify-center flex-shrink-0">
              <span class="text-2xl">⚡</span>
            </div>
            <div>
              <h3 class="text-lemon font-bold text-lg sm:text-xl leading-tight">{{ t.executiveTitle }}</h3>
              <span class="text-esmerald-light/60 text-xs font-medium uppercase tracking-wider">{{ t.executiveTime }}</span>
            </div>
          </div>
          <p class="text-esmerald-light/80 font-light text-sm sm:text-base leading-relaxed mb-6">
            {{ t.executiveSub }}
          </p>
          <div class="flex items-center gap-2 text-lemon font-medium text-sm group-hover:gap-3 transition-all">
            <span>{{ t.executiveCta }}</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>

        <!-- Complete card -->
        <button
          type="button"
          class="gateway-card group relative bg-white rounded-2xl sm:rounded-3xl p-6 sm:p-8 text-left
                 border-2 border-esmerald/15 hover:border-esmerald transition-all duration-300
                 shadow-lg hover:shadow-2xl cursor-pointer"
          @click="$emit('select', 'detailed')"
        >
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 bg-esmerald/10 rounded-xl flex items-center justify-center flex-shrink-0">
              <span class="text-2xl">📋</span>
            </div>
            <div>
              <h3 class="text-esmerald font-bold text-lg sm:text-xl leading-tight">{{ t.detailedTitle }}</h3>
              <span class="text-green-light text-xs font-medium uppercase tracking-wider">{{ t.detailedTime }}</span>
            </div>
          </div>
          <p class="text-esmerald/70 font-light text-sm sm:text-base leading-relaxed mb-6">
            {{ t.detailedSub }}
          </p>
          <div class="flex items-center gap-2 text-esmerald font-medium text-sm group-hover:gap-3 transition-all">
            <span>{{ t.detailedCta }}</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  language: {
    type: String,
    default: 'es',
  },
  clientName: {
    type: String,
    default: '',
  },
});

defineEmits(['select']);

const i18n = {
  es: {
    heading: '¿Cómo prefieres explorar esta propuesta?',
    subheading: 'Elige el nivel de detalle que mejor se adapte a tu tiempo y necesidad.',
    executiveTitle: 'Vista Ejecutiva',
    executiveSub: 'Lo esencial para tomar tu decisión: qué incluye, cuánto cuesta y cuándo lo tienes.',
    executiveTime: '~2 min de lectura',
    executiveCta: 'Ir al resumen',
    detailedTitle: 'Propuesta Completa',
    detailedSub: 'Cada sección de la propuesta: contexto, estrategia, requerimientos técnicos y proceso de trabajo.',
    detailedTime: '~8 min de lectura',
    detailedCta: 'Ver todo el detalle',
  },
  en: {
    heading: 'How would you like to explore this proposal?',
    subheading: 'Choose the level of detail that best fits your time and needs.',
    executiveTitle: 'Executive View',
    executiveSub: 'The essentials to make your decision: what\'s included, how much it costs, and when you\'ll have it.',
    executiveTime: '~2 min read',
    executiveCta: 'Go to summary',
    detailedTitle: 'Full Proposal',
    detailedSub: 'Every section of the proposal: context, strategy, technical requirements, and work process.',
    detailedTime: '~8 min read',
    detailedCta: 'See all the details',
  },
};

const t = computed(() => i18n[props.language] || i18n.es);
</script>

<style scoped>
.gateway-card {
  transition: all 0.3s ease;
}
.gateway-card:hover {
  transform: translateY(-4px);
}
</style>
