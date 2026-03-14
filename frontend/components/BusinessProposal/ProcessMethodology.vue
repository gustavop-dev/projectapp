<template>
  <section ref="sectionRef" class="process-methodology min-h-screen py-16 md:py-24 bg-white">
    <div class="container mx-auto px-6 md:px-12 lg:px-24 max-w-5xl">
      <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
        <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
          {{ index }}
        </span>
        <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
          {{ title }}
        </h2>
      </div>

      <p data-animate="fade-up" class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl mb-12">
        {{ intro }}
      </p>

      <!-- Horizontal steps pipeline (desktop) / Vertical (mobile) -->
      <div data-animate="fade-up-stagger" class="hidden md:flex items-start justify-between gap-2 relative">
        <!-- Connector line -->
        <div class="absolute top-8 left-12 right-12 h-px bg-emerald-200 z-0"></div>

        <div
          v-for="(step, idx) in steps"
          :key="step.title"
          class="relative z-10 flex-1 text-center group"
        >
          <!-- Step circle -->
          <div
            class="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center text-2xl
                   transition-all group-hover:scale-110 group-hover:shadow-lg"
            :class="idx <= activeStep ? 'bg-esmerald text-lemon shadow-md' : 'bg-emerald-50 text-emerald-400 border border-emerald-200'"
          >
            {{ step.icon }}
          </div>
          <h3 class="text-sm font-semibold mb-1.5" :class="idx <= activeStep ? 'text-esmerald' : 'text-gray-500'">
            {{ step.title }}
          </h3>
          <p class="text-xs font-light leading-relaxed px-2" :class="idx <= activeStep ? 'text-esmerald/70' : 'text-gray-400'">
            {{ step.description }}
          </p>
          <div v-if="step.clientAction" class="mt-2 text-[10px] text-emerald-600 bg-emerald-50 rounded-lg px-2 py-1 inline-block">
            {{ step.clientAction }}
          </div>
        </div>
      </div>

      <!-- Mobile vertical layout -->
      <div data-animate="fade-up-stagger" class="md:hidden space-y-4">
        <div class="relative">
          <div class="absolute left-6 top-0 bottom-0 w-px bg-emerald-200"></div>
          <div
            v-for="(step, idx) in steps"
            :key="step.title"
            class="relative rounded-2xl border px-5 py-4 ml-14 transition-all"
            :class="idx <= activeStep ? 'bg-esmerald/5 border-esmerald/20' : 'border-gray-100'"
          >
            <div
              class="absolute -left-[2.35rem] top-5 h-3 w-3 rounded-full border-2 border-white"
              :class="idx <= activeStep ? 'bg-emerald-600' : 'bg-emerald-200'"
            ></div>
            <div class="flex items-start gap-3">
              <span class="text-xl flex-shrink-0">{{ step.icon }}</span>
              <div class="min-w-0">
                <h3 class="text-sm font-semibold" :class="idx <= activeStep ? 'text-esmerald' : 'text-gray-500'">
                  {{ step.title }}
                </h3>
                <p class="text-xs font-light leading-relaxed mt-1" :class="idx <= activeStep ? 'text-esmerald/70' : 'text-gray-400'">
                  {{ step.description }}
                </p>
                <div v-if="step.clientAction" class="mt-1.5 text-[10px] text-emerald-600 bg-emerald-50 rounded-lg px-2 py-0.5 inline-block">
                  {{ step.clientAction }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  index: {
    type: String,
    default: '07',
  },
  title: {
    type: String,
    default: 'Proceso y Metodología',
  },
  intro: {
    type: String,
    default: 'Trabajamos con un proceso estructurado que garantiza transparencia, calidad y entrega a tiempo en cada etapa del proyecto.',
  },
  activeStep: {
    type: Number,
    default: 0,
  },
  steps: {
    type: Array,
    default: () => [
      {
        icon: '🔍',
        title: 'Discovery',
        description: 'Investigamos tu negocio, competidores y usuarios para definir la estrategia ideal.',
        clientAction: 'Tu aporte: briefing inicial',
      },
      {
        icon: '🎨',
        title: 'Diseño UX/UI',
        description: 'Creamos prototipos interactivos en Figma con iteraciones hasta la aprobación visual.',
        clientAction: 'Tu aporte: feedback de diseño',
      },
      {
        icon: '💻',
        title: 'Desarrollo',
        description: 'Implementamos con código limpio, arquitectura escalable y las mejores prácticas.',
        clientAction: '',
      },
      {
        icon: '🧪',
        title: 'QA y Testing',
        description: 'Pruebas exhaustivas de funcionalidad, rendimiento, seguridad y compatibilidad.',
        clientAction: 'Tu aporte: pruebas de aceptación',
      },
      {
        icon: '🚀',
        title: 'Lanzamiento',
        description: 'Despliegue en producción, monitoreo post-lanzamiento y capacitación del equipo.',
        clientAction: '',
      },
    ],
  },
});
</script>

<style scoped>
</style>
