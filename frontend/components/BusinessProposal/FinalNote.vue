<template>
  <section ref="sectionRef" class="final-note py-16 md:py-24 bg-gray-50">
    <div class="container mx-auto px-6 md:px-12 lg:px-24 max-w-4xl">
      <div class="section-header mb-12">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ index }}
          </span>
          <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            {{ title }}
          </h2>
        </div>
      </div>

      <div data-animate="fade-up" class="note-content bg-white p-5 sm:p-8 md:p-12 rounded-2xl shadow-sm mb-8">
        <div class="quote-icon mb-6">
          <svg class="w-12 h-12 text-emerald-600 opacity-50" fill="currentColor" viewBox="0 0 24 24">
            <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/>
          </svg>
        </div>

        <div class="message-text space-y-6 text-lg text-gray-700 leading-relaxed">
          <p>{{ message }}</p>
          
          <p v-if="personalNote" class="italic text-gray-600">
            {{ personalNote }}
          </p>
        </div>

        <div class="signature mt-12 pt-8 border-t border-gray-200">
          <div class="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <p class="text-xl font-bold text-gray-900 mb-2">{{ teamName }}</p>
              <p class="text-gray-600">{{ teamRole }}</p>
              <p class="text-sm text-gray-500 mt-2">{{ contactEmail }}</p>
            </div>
            <div class="mt-6 md:mt-0">
              <img v-if="signature" :src="signature" alt="Firma" class="h-16" />
            </div>
          </div>
        </div>
      </div>

      <div data-animate="fade-up-stagger" class="commitment-badges grid md:grid-cols-3 gap-6">
        <div v-for="(badge, index) in commitmentBadges" :key="index"
             class="badge-card bg-white p-6 rounded-xl shadow-sm text-center hover:shadow-md transition-shadow">
          <div class="text-4xl mb-3">{{ badge.icon }}</div>
          <h4 class="font-bold text-gray-900 mb-2">{{ badge.title }}</h4>
          <p class="text-sm text-gray-600">{{ badge.description }}</p>
        </div>
      </div>

      <!-- F4: Kickoff Plan — first 5 days after approval -->
      <div v-if="kickoffPlan && kickoffPlan.length" data-animate="fade-up" class="mt-16 mb-12">
        <h3 class="text-2xl font-bold text-esmerald mb-2 text-center">{{ kickoffTitle }}</h3>
        <p class="text-sm text-esmerald/60 text-center mb-8">{{ kickoffSubtitle }}</p>
        <div class="relative">
          <div class="absolute left-6 sm:left-8 top-0 bottom-0 w-0.5 bg-emerald-200"></div>
          <div v-for="(step, kIdx) in kickoffPlan" :key="kIdx" class="relative flex items-start gap-4 sm:gap-6 mb-6 last:mb-0">
            <div class="relative z-10 flex-shrink-0 w-12 h-12 sm:w-16 sm:h-16 bg-esmerald text-lemon rounded-full flex items-center justify-center font-bold text-sm sm:text-base shadow-md">
              {{ step.day || `D${kIdx + 1}` }}
            </div>
            <div class="pt-1 sm:pt-3">
              <h4 class="font-bold text-esmerald text-sm sm:text-base">{{ step.title }}</h4>
              <p class="text-xs sm:text-sm text-esmerald/60 leading-relaxed mt-1">{{ step.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Next Steps (merged from next_steps section) -->
      <template v-if="nextSteps && nextSteps.length">
        <div data-animate="fade-up" class="mt-16 mb-8 text-center" v-if="nextStepsIntro">
          <p class="text-xl sm:text-2xl text-esmerald/80 leading-relaxed font-light">
            {{ nextStepsIntro }}
          </p>
        </div>

        <div data-animate="fade-up-stagger" class="grid md:grid-cols-3 gap-4 sm:gap-8 mb-12">
          <div v-for="(step, sIdx) in nextSteps" :key="sIdx"
               class="step-card bg-esmerald/5 p-5 sm:p-8 rounded-2xl border-2 border-esmerald/10 hover:border-esmerald/30 transition-all text-center">
            <div class="step-number w-12 h-12 sm:w-16 sm:h-16 bg-esmerald text-lemon rounded-full flex items-center justify-center text-xl sm:text-2xl font-bold mx-auto mb-4 sm:mb-6 shadow-lg">
              {{ sIdx + 1 }}
            </div>
            <h3 class="text-xl font-bold text-esmerald mb-3">{{ step.title }}</h3>
            <p class="text-esmerald/70 font-light leading-relaxed">{{ step.description }}</p>
          </div>
        </div>

        <div v-if="ctaMessage" data-animate="fade-up" class="bg-esmerald p-5 sm:p-8 md:p-12 rounded-3xl text-white text-center mb-12 shadow-2xl">
          <h3 class="text-2xl sm:text-3xl md:text-4xl font-bold text-lemon mb-4">¿Listo para Comenzar?</h3>
          <p class="text-base sm:text-xl text-esmerald-light/80 mb-6 sm:mb-8 max-w-2xl mx-auto">
            {{ ctaMessage }}
          </p>
          <div class="cta-buttons flex flex-col md:flex-row gap-4 justify-center">
            <a v-if="primaryCTA?.link" :href="primaryCTA.link" target="_blank"
               class="inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 bg-lemon text-esmerald rounded-xl font-bold text-base sm:text-lg hover:bg-lemon/90 transition-all shadow-lg hover:shadow-xl">
              <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
              {{ primaryCTA.text }}
            </a>
            <button v-if="secondaryCTA?.text" type="button"
               data-cal-link="projectapp/discovery-call-projectapp"
               data-cal-namespace="discovery-call-projectapp"
               data-cal-config='{"layout":"month_view","useSlotsViewOnSmallScreen":"true"}'
               class="inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 bg-esmerald-dark text-esmerald-light rounded-xl font-bold text-base sm:text-lg hover:bg-esmerald-dark/80 transition-all cursor-pointer">
              <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              {{ secondaryCTA.text }}
            </button>
          </div>
        </div>

        <div v-if="contactMethods?.length" data-animate="fade-up-stagger" class="grid md:grid-cols-3 gap-6 mb-12">
          <div v-for="(contact, cIdx) in contactMethods" :key="cIdx"
               class="contact-card bg-esmerald/5 p-4 sm:p-6 rounded-xl text-center border border-esmerald/10 hover:border-esmerald/20 transition-colors">
            <div class="text-4xl mb-3">{{ contact.icon }}</div>
            <h4 class="font-bold text-esmerald mb-2">{{ contact.title }}</h4>
            <a :href="contact.link" target="_blank" class="text-green-light hover:text-esmerald font-medium transition-colors">
              {{ contact.value }}
            </a>
          </div>
        </div>
      </template>

    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  index: {
    type: String,
    default: '10'
  },
  title: {
    type: String,
    default: 'Nota Final'
  },
  message: {
    type: String,
    default: 'Creemos firmemente que esta propuesta representa una oportunidad excepcional para transformar tu presencia digital y alcanzar tus objetivos de negocio. Cada elemento ha sido cuidadosamente diseñado pensando en tus necesidades específicas y en los resultados que buscas lograr. Estamos comprometidos no solo con entregar un proyecto excepcional, sino con construir una relación de largo plazo donde tu éxito sea nuestro éxito.'
  },
  personalNote: {
    type: String,
    default: 'Estamos emocionados por la posibilidad de trabajar contigo y ayudarte a llevar tu negocio al siguiente nivel. Esta propuesta es solo el comienzo de lo que podemos lograr juntos.'
  },
  teamName: {
    type: String,
    default: 'El equipo de Project App'
  },
  teamRole: {
    type: String,
    default: 'Tu socio en transformación digital'
  },
  contactEmail: {
    type: String,
    default: 'hola@projectapp.com'
  },
  signature: {
    type: String,
    default: null
  },
  commitmentBadges: {
    type: Array,
    default: () => [
      {
        icon: '🤝',
        title: 'Compromiso Total',
        description: 'Dedicación completa a tu proyecto hasta lograr resultados excepcionales'
      },
      {
        icon: '💯',
        title: 'Garantía de Calidad',
        description: 'Revisiones ilimitadas hasta tu completa satisfacción'
      },
      {
        icon: '🎯',
        title: 'Enfoque en Resultados',
        description: 'Medimos nuestro éxito por el impacto en tu negocio'
      }
    ]
  },
  validityMessage: {
    type: String,
    default: ''
  },
  thankYouMessage: {
    type: String,
    default: ''
  },
  nextSteps: {
    type: Array,
    default: () => []
  },
  nextStepsIntro: {
    type: String,
    default: ''
  },
  ctaMessage: {
    type: String,
    default: ''
  },
  primaryCTA: {
    type: Object,
    default: () => ({})
  },
  secondaryCTA: {
    type: Object,
    default: () => ({})
  },
  contactMethods: {
    type: Array,
    default: () => []
  },
  kickoffPlan: {
    type: Array,
    default: () => []
  },
  language: {
    type: String,
    default: 'es'
  }
});

const kickoffTitle = computed(() => {
  return props.language === 'en' ? 'Kickoff Plan' : 'Plan de Kickoff';
});

const kickoffSubtitle = computed(() => {
  return props.language === 'en'
    ? 'What happens in the first days after you approve'
    : 'Qué sucede en los primeros días después de aprobar';
});
</script>

<style scoped>
.badge-card {
  transition: all 0.3s ease;
}

.badge-card:hover {
  transform: translateY(-4px);
}

.message-text p {
  text-align: justify;
}

.step-card {
  transition: all 0.3s ease;
}

.step-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(16, 185, 129, 0.2);
}

.step-number {
  transition: transform 0.3s ease;
}

.step-card:hover .step-number {
  transform: scale(1.1) rotate(5deg);
}

.contact-card {
  transition: all 0.3s ease;
}

.contact-card:hover {
  transform: scale(1.05);
}

.cta-buttons a {
  transition: all 0.3s ease;
}

.cta-buttons a:hover {
  transform: translateY(-2px);
}
</style>
