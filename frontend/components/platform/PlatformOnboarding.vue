<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="visible"
        class="onb-backdrop fixed inset-0 z-[9998] bg-white/60 backdrop-blur-[2px] dark:bg-esmerald-dark/60"
      />
    </Transition>

    <div
      v-if="visible"
      ref="cloneContainerRef"
      class="fixed z-[9999] pointer-events-none"
      :style="cloneStyle"
    />

    <Transition name="fade">
      <div
        v-if="visible && spotlightRect"
        class="fixed z-[9999] pointer-events-none rounded-2xl
               ring-[3px] ring-green-light/60
               transition-all duration-400 ease-out"
        :style="spotlightStyle"
      />
    </Transition>

    <Transition name="tooltip-pop" mode="out-in">
      <div
        v-if="visible"
        :key="currentStep"
        ref="tooltipRef"
        class="fixed z-[10000]"
        :style="tooltipStyle"
      >
        <div
          class="tooltip-arrow absolute w-3 h-3 bg-white rotate-45 border border-gray-100 dark:bg-esmerald dark:border-white/10"
          :style="arrowComputedStyle"
        />

        <div class="relative bg-white rounded-2xl shadow-2xl border border-gray-100 p-5 w-[272px] sm:w-[296px] dark:bg-esmerald dark:border-white/10">
          <div class="flex items-center gap-1.5 mb-3">
            <div
              v-for="i in totalSteps"
              :key="i"
              class="h-1.5 rounded-full transition-all duration-300"
              :class="i - 1 === currentStep
                ? 'w-5 bg-esmerald dark:bg-lemon'
                : i - 1 < currentStep
                  ? 'w-1.5 bg-esmerald/40 dark:bg-lemon/40'
                  : 'w-1.5 bg-gray-200 dark:bg-white/10'"
            />
            <span class="ml-auto text-[10px] text-gray-400 dark:text-white/40 font-medium tabular-nums">
              {{ currentStep + 1 }}/{{ totalSteps }}
            </span>
          </div>

          <h4 class="text-sm font-bold text-gray-900 dark:text-white mb-1">{{ currentStepData.title }}</h4>
          <p class="text-xs text-gray-500 dark:text-white/60 leading-relaxed mb-4">{{ currentStepData.description }}</p>

          <div class="flex items-center justify-between">
            <button
              class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-white/80 transition-colors pointer-events-auto"
              @click="dismiss"
            >
              Omitir
            </button>
            <div class="flex items-center gap-2">
              <button
                v-if="currentStep > 0"
                class="px-3 py-1.5 text-xs text-gray-600 dark:text-white/60 hover:text-gray-800 dark:hover:text-white transition-colors pointer-events-auto"
                @click="prev"
              >
                Atrás
              </button>
              <button
                class="px-4 py-1.5 text-xs font-medium text-white bg-esmerald rounded-lg
                       hover:bg-esmerald/90 transition-colors shadow-sm pointer-events-auto
                       dark:bg-lemon dark:text-esmerald-dark dark:hover:bg-lemon/90"
                @click="next"
              >
                {{ isLastStep ? 'Entendido' : 'Siguiente' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'

const STORAGE_KEY = 'platform_onboarding_seen'
const TOOLTIP_W = 296
const TOOLTIP_H_EST = 190
const GAP = 14
const ARROW_SIZE = 6
const VIEWPORT_PAD = 12

const emit = defineEmits(['complete'])

const visible = ref(false)
const currentStep = ref(0)
const tooltipRef = ref(null)
const cloneContainerRef = ref(null)

const spotlightRect = ref(null)
const cloneStyle = ref({})
const tooltipStyle = ref({})
const arrowComputedStyle = ref({})

const steps = [
  { target: '.tour-nav-dashboard', title: 'Dashboard', description: 'Tu panel de control. Aquí verás un resumen de tus proyectos activos, métricas clave y accesos rápidos.', prefer: 'right' },
  { target: '.tour-nav-notifications', title: 'Notificaciones', description: 'Recibe alertas cuando haya actualizaciones, comentarios nuevos o cambios importantes en tus proyectos.', prefer: 'right' },
  { target: '.tour-nav-projects', title: 'Tus proyectos', description: 'Accede a todos tus proyectos activos. Desde aquí entras al detalle de cada uno con su tablero, bugs y entregables.', prefer: 'right' },
  { target: '.tour-nav-board', title: 'Tablero Kanban', description: 'Vista general con el estado de todos los requerimientos de tus proyectos organizados en columnas.', prefer: 'right' },
  { target: '.tour-nav-changes', title: 'Solicitudes de cambio', description: 'Solicita modificaciones o nuevas funcionalidades para tus proyectos. Tu equipo las recibirá y evaluará.', prefer: 'right' },
  { target: '.tour-nav-bugs', title: 'Reportar bugs', description: 'Encontraste un error? Repórtalo aquí con detalles para que sea corregido lo antes posible.', prefer: 'right' },
  { target: '.tour-nav-deliverables', title: 'Entregables', description: 'Archivos, versiones y entregas que tu equipo de desarrollo comparte contigo. Descárgalos cuando necesites.', prefer: 'right' },
  { target: '.tour-nav-payments', title: 'Pagos', description: 'Consulta el estado de tus pagos, historial de transacciones y suscripciones activas.', prefer: 'right' },
  { target: '.tour-nav-profile', title: 'Configuración', description: 'Edita tu perfil, cambia tu contraseña y actualiza tus datos personales.', prefer: 'right' },
  { target: '.tour-nav-theme', title: 'Personaliza tu portal', description: 'Cambia los colores y la imagen de fondo para hacer tuyo este espacio. Los cambios se guardan en tu cuenta.', prefer: 'right' },
]

const activeSteps = ref([])
const totalSteps = computed(() => activeSteps.value.length)
const currentStepData = computed(() => activeSteps.value[currentStep.value] || steps[0])
const isLastStep = computed(() => currentStep.value === activeSteps.value.length - 1)

const spotlightStyle = computed(() => {
  if (!spotlightRect.value) return { display: 'none' }
  const r = spotlightRect.value
  const pad = 4
  return {
    top: `${r.top - pad}px`,
    left: `${r.left - pad}px`,
    width: `${r.width + pad * 2}px`,
    height: `${r.height + pad * 2}px`,
  }
})

function scrollToTarget(el) {
  const r = el.getBoundingClientRect()
  const inViewport = r.top >= 0 && r.bottom <= window.innerHeight
  if (!inViewport) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return new Promise((resolve) => setTimeout(resolve, 400))
  }
  return Promise.resolve()
}

function getRect(selector) {
  const el = document.querySelector(selector)
  if (!el) return null
  const r = el.getBoundingClientRect()
  return { top: r.top, left: r.left, width: r.width, height: r.height, bottom: r.bottom, right: r.right, el }
}

function cloneTarget(rect) {
  if (!cloneContainerRef.value || !rect?.el) return
  cloneContainerRef.value.innerHTML = ''
  const clone = rect.el.cloneNode(true)
  clone.removeAttribute('class')
  const cs = window.getComputedStyle(rect.el)
  const skip = new Set([
    'position', 'top', 'right', 'bottom', 'left',
    'transform', 'translate', 'margin',
    'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
    'z-index', 'animation', 'animation-name', 'animation-duration',
    'animation-delay', 'animation-fill-mode',
  ])
  for (const prop of cs) {
    if (skip.has(prop)) continue
    try { clone.style.setProperty(prop, cs.getPropertyValue(prop)) } catch { /* skip */ }
  }
  clone.style.pointerEvents = 'none'
  cloneContainerRef.value.appendChild(clone)
  cloneStyle.value = {
    top: `${rect.top}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    height: `${rect.height}px`,
    overflow: 'hidden',
  }
}

function computePosition(rect, prefer) {
  const vw = window.innerWidth
  const vh = window.innerHeight
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2

  const sides = [prefer, 'bottom', 'right', 'left', 'top'].filter((v, i, a) => a.indexOf(v) === i)

  for (const side of sides) {
    const pos = calcSidePosition(side, rect, vw, vh, cx, cy)
    if (pos) return pos
  }
  return {
    style: { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
    arrow: { display: 'none' },
  }
}

function calcSidePosition(side, rect, vw, vh, cx, cy) {
  if (side === 'right') {
    const tipLeft = rect.right + GAP
    if (tipLeft + TOOLTIP_W > vw - VIEWPORT_PAD) return null
    const tipTop = clampVertical(cy - TOOLTIP_H_EST / 2, vh)
    const arrowTop = Math.max(16, Math.min(TOOLTIP_H_EST - 24, cy - tipTop))
    return { style: { top: `${tipTop}px`, left: `${tipLeft}px` }, arrow: { top: `${arrowTop}px`, left: `-${ARROW_SIZE}px`, transform: 'rotate(45deg)', borderRight: 'none', borderTop: 'none' } }
  }
  if (side === 'left') {
    const tipLeft = rect.left - GAP - TOOLTIP_W
    if (tipLeft < VIEWPORT_PAD) return null
    const tipTop = clampVertical(cy - TOOLTIP_H_EST / 2, vh)
    const arrowTop = Math.max(16, Math.min(TOOLTIP_H_EST - 24, cy - tipTop))
    return { style: { top: `${tipTop}px`, left: `${tipLeft}px` }, arrow: { top: `${arrowTop}px`, right: `-${ARROW_SIZE}px`, transform: 'rotate(45deg)', borderLeft: 'none', borderBottom: 'none' } }
  }
  if (side === 'bottom') {
    const tipTop = rect.bottom + GAP
    if (tipTop + TOOLTIP_H_EST > vh - VIEWPORT_PAD) return null
    const tipLeft = clampHorizontal(cx - TOOLTIP_W / 2, vw)
    const arrowLeft = Math.max(20, Math.min(TOOLTIP_W - 28, cx - tipLeft))
    return { style: { top: `${tipTop}px`, left: `${tipLeft}px` }, arrow: { top: `-${ARROW_SIZE}px`, left: `${arrowLeft}px`, transform: 'rotate(45deg)', borderBottom: 'none', borderRight: 'none' } }
  }
  if (side === 'top') {
    const tipTop = rect.top - GAP - TOOLTIP_H_EST
    if (tipTop < VIEWPORT_PAD) return null
    const tipLeft = clampHorizontal(cx - TOOLTIP_W / 2, vw)
    const arrowLeft = Math.max(20, Math.min(TOOLTIP_W - 28, cx - tipLeft))
    return { style: { top: `${tipTop}px`, left: `${tipLeft}px` }, arrow: { bottom: `-${ARROW_SIZE}px`, left: `${arrowLeft}px`, transform: 'rotate(45deg)', borderTop: 'none', borderLeft: 'none' } }
  }
  return null
}

function clampVertical(top, vh) {
  return Math.max(VIEWPORT_PAD, Math.min(vh - TOOLTIP_H_EST - VIEWPORT_PAD, top))
}

function clampHorizontal(left, vw) {
  return Math.max(VIEWPORT_PAD, Math.min(vw - TOOLTIP_W - VIEWPORT_PAD, left))
}

async function positionAll() {
  const step = currentStepData.value
  const el = document.querySelector(step.target)

  if (!el) {
    spotlightRect.value = null
    cloneStyle.value = { display: 'none' }
    tooltipStyle.value = { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
    arrowComputedStyle.value = { display: 'none' }
    return
  }

  // Scroll target into view before measuring
  await scrollToTarget(el)

  const rect = getRect(step.target)
  if (!rect) return

  spotlightRect.value = rect
  cloneTarget(rect)

  const pos = computePosition(rect, step.prefer)
  tooltipStyle.value = pos.style
  arrowComputedStyle.value = pos.arrow
}

function next() {
  if (isLastStep.value) { dismiss(); return }
  currentStep.value++
  nextTick(positionAll)
}

function prev() {
  if (currentStep.value > 0) {
    currentStep.value--
    nextTick(positionAll)
  }
}

function onKeydown(e) {
  if (!visible.value) return
  if (e.key === 'Escape') dismiss()
}

function dismiss() {
  if (cloneContainerRef.value) cloneContainerRef.value.innerHTML = ''
  spotlightRect.value = null
  cloneStyle.value = { display: 'none' }
  tooltipStyle.value = { display: 'none' }
  visible.value = false
  try { localStorage.setItem(STORAGE_KEY, 'true') } catch { /* noop */ }
  emit('complete')
}

function start() {
  try { if (localStorage.getItem(STORAGE_KEY)) return } catch { /* noop */ }

  setTimeout(() => {
    activeSteps.value = steps.filter((s) => document.querySelector(s.target))
    if (!activeSteps.value.length) return
    currentStep.value = 0
    visible.value = true
    nextTick(positionAll)
  }, 1000)
}

function forceStart() {
  try { localStorage.removeItem(STORAGE_KEY) } catch { /* noop */ }
  setTimeout(() => {
    activeSteps.value = steps.filter((s) => document.querySelector(s.target))
    if (!activeSteps.value.length) return
    currentStep.value = 0
    visible.value = true
    nextTick(positionAll)
  }, 300)
}

function onResize() {
  if (visible.value) positionAll()
}

onMounted(() => {
  window.addEventListener('resize', onResize)
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('keydown', onKeydown)
})

defineExpose({ start, forceStart })
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

.tooltip-pop-enter-active { transition: opacity 0.3s ease, transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); }
.tooltip-pop-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.tooltip-pop-enter-from { opacity: 0; transform: scale(0.92); }
.tooltip-pop-leave-to { opacity: 0; transform: scale(0.96); }

.tooltip-arrow { z-index: -1; }
</style>
