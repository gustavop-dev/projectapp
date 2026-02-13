<template>
  <section ref="sectionRef" class="development-stages h-full min-w-[100vw] w-max bg-white flex items-center">
    <div class="stages-layout w-max flex flex-col">
      <div ref="pinRef" class="w-screen px-6 md:px-12 lg:px-24 pt-4">
        <div class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            06
          </span>
          <h2 ref="titleRef" class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            Etapas de contratación y desarrollo
          </h2>
        </div>

        <p ref="introRef" class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl">
          Nuestro proceso está diseñado para ofrecer claridad, confianza y acompañamiento en cada fase 🧭:
        </p>
      </div>

      <div class="pr-6 md:pr-12 lg:pr-24 pl-6 md:pl-12 lg:pl-24 pt-12">
        <div class="relative">
          <div ref="trackRef" class="flex gap-4 pt-10 w-max">
            <div
              v-for="(stage, idx) in stages"
              :key="stage.title"
              :ref="(el) => setStageItemRef(el, idx)"
              class="relative rounded-3xl border border-esmerald-light/70 bg-white px-6 py-6 md:px-7 md:py-7 min-w-[18rem] md:min-w-[22rem]"
              :class="stage.current ? 'border-esmerald bg-esmerald-light/60' : ''"
            >
              <div
                class="absolute -top-[0.45rem] left-6 h-3.5 w-3.5 rounded-full"
                :ref="(el) => setStageDotRef(el, idx)"
                :class="(stage.current || passedStageFlags[idx]) ? 'bg-esmerald' : 'bg-esmerald-light'"
              ></div>

              <div class="flex items-start justify-between gap-5">
                <div class="min-w-0">
                  <div class="flex items-center gap-3">
                    <span class="text-xl md:text-2xl">{{ stage.icon }}</span>
                    <h3 class="text-esmerald font-light text-lg md:text-xl leading-snug">
                      {{ stage.title }}
                    </h3>
                  </div>
                  <p class="mt-2 text-esmerald/80 font-light leading-relaxed">
                    {{ stage.description }}
                  </p>
                </div>

                <div class="flex-shrink-0 text-green-light font-light tracking-[0.25em] text-xs pt-2">
                  {{ String(idx + 1).padStart(2, '0') }}
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
import { ref, inject, watch, nextTick, onBeforeUnmount } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const sectionRef = ref(null)
const pinRef = ref(null)
const titleRef = ref(null)
const introRef = ref(null)
const trackRef = ref(null)

const stageItemRefs = ref([])
const setStageItemRef = (el, idx) => {
  if (!el) return
  stageItemRefs.value[idx] = el
}

const stageDotRefs = ref([])
const setStageDotRef = (el, idx) => {
  if (!el) return
  stageDotRefs.value[idx] = el
}

const horizontalTweenRef = inject('horizontalTweenRef', ref(null))

let stageTimeline = null
let dotTriggers = []

const stages = [
  {
    icon: '✉️',
    title: 'Propuesta Comercial',
    description: 'Presentación formal de la propuesta técnica y económica (etapa actual).',
    current: true
  },
  {
    icon: '🧾',
    title: 'Borrador de Contrato',
    description: 'Envío del documento que establece los términos, condiciones y compromisos de ambas partes.'
  },
  {
    icon: '✍️',
    title: 'Formalización del Contrato',
    description: 'Firma del acuerdo y confirmación del inicio oficial del proyecto.'
  },
  {
    icon: '🎨',
    title: 'Etapa de Diseño',
    description: 'Creación del prototipo visual en Figma, con reuniones de revisión para refinar la estética y estructura del sitio hasta su aprobación final.'
  },
  {
    icon: '💻',
    title: 'Etapa de Desarrollo',
    description: 'Implementación del diseño en código nativo, con una arquitectura limpia, fluida y optimizada para la mejor experiencia del usuario.'
  },
  {
    icon: '🚀',
    title: 'Despliegue del Proyecto',
    description: 'Publicación del sitio web en el entorno de producción y revisión final de funcionalidad y rendimiento.'
  },
  {
    icon: '💖',
    title: 'Entrega Final',
    description: 'Con el sitio en línea y validado, se realiza el pago final, cerrando el ciclo con una experiencia de transformación digital completa.'
  }
]

const passedStageFlags = ref(stages.map(() => false))

const initAnimations = async (containerTween) => {
  await nextTick()

  if (!sectionRef.value || !containerTween) return

  if (stageTimeline) {
    stageTimeline.scrollTrigger?.kill()
    stageTimeline.kill()
    stageTimeline = null
  }

  dotTriggers.forEach((t) => t.kill())
  dotTriggers = []
  passedStageFlags.value = stages.map(() => false)

  const items = stageItemRefs.value.filter(Boolean)

  gsap.set([titleRef.value, introRef.value], { opacity: 0, y: 16 })
  gsap.set(items, { opacity: 0, y: 18 })

  stageTimeline = gsap.timeline({
    defaults: { ease: 'power3.out' },
    scrollTrigger: {
      trigger: sectionRef.value,
      containerAnimation: containerTween,
      start: 'left 70%',
      toggleActions: 'play none none reverse'
    }
  })

  stageTimeline
    .to(titleRef.value, { opacity: 1, y: 0, duration: 0.7 })
    .to(introRef.value, { opacity: 1, y: 0, duration: 0.6 }, '-=0.35')
    .to(items, { opacity: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')

  items.forEach((item, idx) => {
    const dot = stageDotRefs.value[idx]
    if (!dot) return

    const syncState = () => {
      const rect = dot.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      passedStageFlags.value[idx] = centerX <= window.innerWidth / 2
    }

    const t = ScrollTrigger.create({
      trigger: item,
      containerAnimation: containerTween,
      start: 'left right',
      end: 'right left',
      onUpdate: syncState,
      onRefresh: syncState
    })

    dotTriggers.push(t)
  })

  ScrollTrigger.refresh()
}

watch(
  () => horizontalTweenRef.value,
  (tween) => {
    if (tween) initAnimations(tween)
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (stageTimeline) {
    stageTimeline.scrollTrigger?.kill()
    stageTimeline.kill()
    stageTimeline = null
  }

  dotTriggers.forEach((t) => t.kill())
  dotTriggers = []
})
</script>

<style scoped>
</style>
