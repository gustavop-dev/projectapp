<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="visible"
        data-testid="diagnostic-onboarding-backdrop"
        class="onb-backdrop fixed inset-0 z-[9998] bg-white/60 backdrop-blur-[2px]"
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
          class="tooltip-arrow absolute w-3 h-3 bg-white rotate-45 border border-gray-100"
          :style="arrowComputedStyle"
        />

        <div class="relative bg-white rounded-2xl shadow-2xl border border-gray-100 p-5 w-[272px] sm:w-[296px]">
          <div class="flex items-center gap-1.5 mb-3">
            <div
              v-for="i in totalSteps"
              :key="i"
              class="h-1.5 rounded-full transition-all duration-300"
              :class="i - 1 === currentStep
                ? 'w-5 bg-esmerald'
                : i - 1 < currentStep
                  ? 'w-1.5 bg-esmerald/40'
                  : 'w-1.5 bg-gray-200'"
            />
            <span data-testid="diagnostic-onboarding-step-progress" class="ml-auto text-[10px] text-gray-400 font-medium tabular-nums">
              {{ currentStep + 1 }}/{{ totalSteps }}
            </span>
          </div>

          <h4 class="text-sm font-bold text-gray-900 mb-1">{{ currentStepData.title }}</h4>
          <p class="text-xs text-gray-500 leading-relaxed mb-4">{{ currentStepData.description }}</p>

          <div class="flex items-center justify-between">
            <button
              class="text-xs text-gray-400 hover:text-gray-600 transition-colors pointer-events-auto"
              @click="dismiss"
            >
              {{ btnLabels.skip }}
            </button>
            <div class="flex items-center gap-2">
              <button
                v-if="currentStep > 0"
                class="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-800 transition-colors pointer-events-auto"
                @click="prev"
              >
                {{ btnLabels.back }}
              </button>
              <button
                :data-testid="isLastStep ? 'diagnostic-onboarding-done-btn' : 'diagnostic-onboarding-next-btn'"
                class="px-4 py-1.5 text-xs font-medium text-white bg-esmerald rounded-lg
                       hover:bg-esmerald/90 transition-colors shadow-sm pointer-events-auto"
                @click="next"
              >
                {{ isLastStep ? btnLabels.done : btnLabels.next }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';

const STORAGE_KEY = 'diagnostic_onboarding_seen';
const TOOLTIP_W = 296;
const TOOLTIP_H_EST = 190;
const GAP = 14;
const ARROW_SIZE = 6;
const VIEWPORT_PAD = 12;

const props = defineProps({
  language: { type: String, default: 'es' },
});

const emit = defineEmits(['complete']);

const visible = ref(false);
const currentStep = ref(0);
const tooltipRef = ref(null);
const cloneContainerRef = ref(null);

const spotlightRect = ref(null);
const cloneStyle = ref({});
const tooltipStyle = ref({});
const arrowComputedStyle = ref({});

const stepsI18n = {
  es: [
    { target: '.theme-toggle',         title: 'Modo claro y oscuro',     description: 'Cambia entre modo claro y oscuro para leer el diagnóstico como prefieras. Tu preferencia se guarda automáticamente.', prefer: 'right' },
    { target: '.index-toggle',         title: 'Índice de secciones',     description: 'Abre el índice para navegar entre las secciones del diagnóstico. Puedes saltar directamente a cualquier parte.',     prefer: 'right',  optional: true },
    { target: '.section-nav',          title: 'Navegar entre secciones', description: 'Usa los botones Anterior y Siguiente para avanzar o retroceder dentro del diagnóstico.',                              prefer: 'top',    optional: true },
    { target: '.section-counter',      title: 'Tu progreso',             description: 'Aquí puedes ver en qué sección estás y cuántas hay en total.',                                                        prefer: 'top',    optional: true },
    { target: '.diagnostic-cta',       title: 'Responder al diagnóstico', description: 'Cuando termines de revisarlo, puedes aceptarlo para avanzar o indicarnos que prefieres no continuar por ahora.',     prefer: 'top',    optional: true },
    { target: '.share-btn',            title: 'Compartir diagnóstico',   description: 'Comparte el enlace de este diagnóstico con tu equipo o socios para revisarlo juntos.',                                prefer: 'left' },
    { target: '.pdf-download',         title: 'Descargar como PDF',      description: 'Descarga todo el diagnóstico en formato PDF para revisarlo offline o compartirlo con tu equipo.',                     prefer: 'left' },
    { target: '.restart-tutorial-btn', title: 'Repetir guía',            description: 'Si necesitas recordar cómo navegar el diagnóstico, puedes reiniciar esta guía cuando quieras desde este botón.',       prefer: 'right' },
  ],
  en: [
    { target: '.theme-toggle',         title: 'Light & Dark Mode',     description: 'Switch between light and dark mode to read the diagnostic however you prefer. Your preference is saved automatically.', prefer: 'right' },
    { target: '.index-toggle',         title: 'Section Index',         description: 'Open the index to navigate between diagnostic sections. You can jump directly to any part.',                            prefer: 'right',  optional: true },
    { target: '.section-nav',          title: 'Navigate Sections',     description: 'Use the Previous and Next buttons to move forward or back through the diagnostic.',                                     prefer: 'top',    optional: true },
    { target: '.section-counter',      title: 'Your Progress',         description: 'See which section you are on and how many there are in total.',                                                          prefer: 'top',    optional: true },
    { target: '.diagnostic-cta',       title: 'Respond to Diagnostic', description: 'When you are done reviewing it, you can accept to move forward or let us know you prefer not to continue right now.',  prefer: 'top',    optional: true },
    { target: '.share-btn',            title: 'Share Diagnostic',      description: 'Share the diagnostic link with your team or partners so they can review it together.',                                  prefer: 'left' },
    { target: '.pdf-download',         title: 'Download as PDF',       description: 'Download the entire diagnostic as a PDF to review offline or share with your team.',                                    prefer: 'left' },
    { target: '.restart-tutorial-btn', title: 'Restart Guide',         description: 'If you need a reminder on how to navigate the diagnostic, you can restart this guide anytime from this button.',         prefer: 'right' },
  ],
};
const steps = computed(() => stepsI18n[props.language] || stepsI18n.es);

const btnLabels = computed(() => props.language === 'en'
  ? { skip: 'Skip', back: 'Back', next: 'Next', done: 'Got it' }
  : { skip: 'Omitir', back: 'Atrás', next: 'Siguiente', done: 'Entendido' }
);

const activeSteps = ref([]);
const totalSteps = computed(() => activeSteps.value.length);
const currentStepData = computed(() => activeSteps.value[currentStep.value] || steps.value[0]);
const isLastStep = computed(() => currentStep.value === activeSteps.value.length - 1);

const spotlightStyle = computed(() => {
  if (!spotlightRect.value) return { display: 'none' };
  const r = spotlightRect.value;
  const pad = 4;
  return {
    top: `${r.top - pad}px`,
    left: `${r.left - pad}px`,
    width: `${r.width + pad * 2}px`,
    height: `${r.height + pad * 2}px`,
  };
});

function getRect(selector) {
  const el = document.querySelector(selector);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { top: r.top, left: r.left, width: r.width, height: r.height, bottom: r.bottom, right: r.right, el };
}

function cloneTarget(rect) {
  if (!cloneContainerRef.value || !rect?.el) return;
  cloneContainerRef.value.innerHTML = '';
  const clone = rect.el.cloneNode(true);
  clone.removeAttribute('class');
  const cs = window.getComputedStyle(rect.el);
  const skip = new Set([
    'position', 'top', 'right', 'bottom', 'left',
    'transform', 'translate', 'margin',
    'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
    'z-index', 'animation', 'animation-name', 'animation-duration',
    'animation-delay', 'animation-fill-mode',
  ]);
  for (const prop of cs) {
    if (skip.has(prop)) continue;
    try { clone.style.setProperty(prop, cs.getPropertyValue(prop)); } catch { /* skip */ }
  }
  clone.style.pointerEvents = 'none';
  cloneContainerRef.value.appendChild(clone);
  cloneStyle.value = {
    top: `${rect.top}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    height: `${rect.height}px`,
    overflow: 'hidden',
  };
}

function computePosition(rect, prefer) {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;

  const sides = [prefer, 'bottom', 'right', 'left', 'top'].filter((v, i, a) => a.indexOf(v) === i);

  for (const side of sides) {
    const pos = calcSidePosition(side, rect, vw, vh, cx, cy);
    if (pos) return pos;
  }
  return {
    style: { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
    arrow: { display: 'none' },
    side: 'center',
  };
}

function calcSidePosition(side, rect, vw, vh, cx, cy) {
  let tipTop, tipLeft, arrowSty;

  if (side === 'right') {
    tipLeft = rect.right + GAP;
    if (tipLeft + TOOLTIP_W > vw - VIEWPORT_PAD) return null;
    tipTop = clampVertical(cy - TOOLTIP_H_EST / 2, vh);
    const arrowTop = Math.max(16, Math.min(TOOLTIP_H_EST - 24, cy - tipTop));
    arrowSty = { top: `${arrowTop}px`, left: `-${ARROW_SIZE}px`, transform: 'rotate(45deg)', borderRight: 'none', borderTop: 'none' };
    return { style: { top: `${tipTop}px`, left: `${tipLeft}px` }, arrow: arrowSty, side };
  }

  if (side === 'left') {
    tipLeft = rect.left - GAP - TOOLTIP_W;
    if (tipLeft < VIEWPORT_PAD) return null;
    tipTop = clampVertical(cy - TOOLTIP_H_EST / 2, vh);
    const arrowTop = Math.max(16, Math.min(TOOLTIP_H_EST - 24, cy - tipTop));
    arrowSty = { top: `${arrowTop}px`, right: `-${ARROW_SIZE}px`, transform: 'rotate(45deg)', borderLeft: 'none', borderBottom: 'none' };
    return { style: { top: `${tipTop}px`, left: `${tipLeft}px` }, arrow: arrowSty, side };
  }

  if (side === 'bottom') {
    tipTop = rect.bottom + GAP;
    if (tipTop + TOOLTIP_H_EST > vh - VIEWPORT_PAD) return null;
    tipLeft = clampHorizontal(cx - TOOLTIP_W / 2, vw);
    const arrowLeft = Math.max(20, Math.min(TOOLTIP_W - 28, cx - tipLeft));
    arrowSty = { top: `-${ARROW_SIZE}px`, left: `${arrowLeft}px`, transform: 'rotate(45deg)', borderBottom: 'none', borderRight: 'none' };
    return { style: { top: `${tipTop}px`, left: `${tipLeft}px` }, arrow: arrowSty, side };
  }

  if (side === 'top') {
    tipTop = rect.top - GAP - TOOLTIP_H_EST;
    if (tipTop < VIEWPORT_PAD) return null;
    tipLeft = clampHorizontal(cx - TOOLTIP_W / 2, vw);
    const arrowLeft = Math.max(20, Math.min(TOOLTIP_W - 28, cx - tipLeft));
    arrowSty = { bottom: `-${ARROW_SIZE}px`, left: `${arrowLeft}px`, transform: 'rotate(45deg)', borderTop: 'none', borderLeft: 'none' };
    return { style: { top: `${tipTop}px`, left: `${tipLeft}px` }, arrow: arrowSty, side };
  }

  return null;
}

function clampVertical(top, vh) {
  return Math.max(VIEWPORT_PAD, Math.min(vh - TOOLTIP_H_EST - VIEWPORT_PAD, top));
}

function clampHorizontal(left, vw) {
  return Math.max(VIEWPORT_PAD, Math.min(vw - TOOLTIP_W - VIEWPORT_PAD, left));
}

function positionAll() {
  const step = currentStepData.value;
  const rect = getRect(step.target);

  if (!rect) {
    spotlightRect.value = null;
    cloneStyle.value = { display: 'none' };
    tooltipStyle.value = { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' };
    arrowComputedStyle.value = { display: 'none' };
    return;
  }

  spotlightRect.value = rect;
  cloneTarget(rect);

  const pos = computePosition(rect, step.prefer);
  tooltipStyle.value = pos.style;
  arrowComputedStyle.value = pos.arrow;
}

function next() {
  if (isLastStep.value) { dismiss(); return; }
  currentStep.value++;
  nextTick(positionAll);
}

function prev() {
  if (currentStep.value > 0) {
    currentStep.value--;
    nextTick(positionAll);
  }
}

function dismiss() {
  if (cloneContainerRef.value) cloneContainerRef.value.innerHTML = '';
  spotlightRect.value = null;
  cloneStyle.value = { display: 'none' };
  tooltipStyle.value = { display: 'none' };
  visible.value = false;
  try { localStorage.setItem(STORAGE_KEY, 'true'); } catch { /* noop */ }
  emit('complete');
}

function start() {
  try { if (localStorage.getItem(STORAGE_KEY)) return; } catch { /* noop */ }

  setTimeout(() => {
    activeSteps.value = steps.value.filter((s) => !s.optional || document.querySelector(s.target));
    if (!activeSteps.value.length) return;
    currentStep.value = 0;
    visible.value = true;
    nextTick(positionAll);
  }, 800);
}

function forceStart() {
  try { localStorage.removeItem(STORAGE_KEY); } catch { /* noop */ }
  setTimeout(() => {
    activeSteps.value = steps.value.filter((s) => !s.optional || document.querySelector(s.target));
    if (!activeSteps.value.length) return;
    currentStep.value = 0;
    visible.value = true;
    nextTick(positionAll);
  }, 300);
}

function onResize() {
  if (visible.value) positionAll();
}

onMounted(() => {
  window.addEventListener('resize', onResize);
});
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize);
});

defineExpose({ start, forceStart });
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.tooltip-pop-enter-active {
  transition: opacity 0.3s ease, transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tooltip-pop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.tooltip-pop-enter-from {
  opacity: 0;
  transform: scale(0.92);
}
.tooltip-pop-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

.tooltip-arrow {
  z-index: -1;
}
</style>
