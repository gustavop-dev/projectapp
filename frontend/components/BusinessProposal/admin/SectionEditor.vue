<template>
  <div class="section-editor">
    <!-- Section title -->
    <div class="mb-5">
      <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Título de la sección</label>
      <input
        v-model="sectionTitle"
        type="text"
        class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
               focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
      />
    </div>

    <!-- Paste mode toggle -->
    <div v-if="hasPasteSupport" class="mb-5">
      <div class="flex items-center gap-3 mb-3">
        <button
          type="button"
          class="text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors"
          :class="!pasteMode
            ? 'bg-emerald-600 text-white border-emerald-600'
            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'"
          @click="pasteMode = false"
        >Formulario</button>
        <button
          type="button"
          class="text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors"
          :class="pasteMode
            ? 'bg-emerald-600 text-white border-emerald-600'
            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'"
          @click="pasteMode = true"
        >Pegar contenido</button>
      </div>

      <div v-if="pasteMode" class="space-y-3">
        <textarea
          v-model="pasteText"
          rows="16"
          placeholder="Pega aquí todo el contenido de esta sección..."
          class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm
                 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y"
        />
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-medium
                   hover:bg-blue-700 transition-colors"
            @click="processPastedContent"
          >
            Procesar y llenar campos
          </button>
          <span class="text-[10px] text-gray-400">Esto llenará los campos del formulario con el contenido pegado</span>
        </div>
        <p v-if="pasteMsg" class="text-xs text-green-600">{{ pasteMsg }}</p>
      </div>
    </div>

    <!-- Dynamic form fields based on section_type -->
    <div v-show="!pasteMode" class="space-y-5">
      <!-- GREETING -->
      <template v-if="sectionType === 'greeting'">
        <FieldInput v-model="form.clientName" label="Nombre del cliente" />
        <FieldTextarea v-model="form.inspirationalQuote" label="Frase inspiracional" :rows="2" />
      </template>

      <!-- EXECUTIVE SUMMARY -->
      <template v-else-if="sectionType === 'executive_summary'">
        <div class="grid grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="01" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
        <FieldInput v-model="form.highlightsTitle" label="Título de highlights" />
        <FieldTextarea v-model="form.highlights" label="Highlights / Incluye" help="Un item por línea" :rows="4" />
      </template>

      <!-- CONTEXT DIAGNOSTIC -->
      <template v-else-if="sectionType === 'context_diagnostic'">
        <div class="grid grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="02" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
        <FieldInput v-model="form.issuesTitle" label="Título de problemas" />
        <FieldTextarea v-model="form.issues" label="Problemas" help="Un problema por línea" :rows="4" />
        <FieldInput v-model="form.opportunityTitle" label="Título de oportunidad" />
        <FieldTextarea v-model="form.opportunity" label="Oportunidad" :rows="3" :isSingle="true" />
      </template>

      <!-- CONVERSION STRATEGY -->
      <template v-else-if="sectionType === 'conversion_strategy'">
        <div class="grid grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="03" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.intro" label="Introducción" :rows="4" :isSingle="true" />
        <!-- Steps: repeatable -->
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Pasos</label>
          <div v-for="(step, idx) in form.steps" :key="idx" class="mb-4 bg-gray-50 rounded-xl p-4 border border-gray-100">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-gray-400">Paso {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500 hover:text-red-700" @click="form.steps.splice(idx, 1)">Eliminar</button>
            </div>
            <FieldInput v-model="step.title" label="Título del paso" class="mb-2" />
            <FieldTextarea v-model="step.bullets" label="Bullets" help="Un bullet por línea" :rows="3" />
          </div>
          <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium" @click="form.steps.push({ title: '', bullets: '' })">
            + Agregar paso
          </button>
        </div>
        <FieldInput v-model="form.resultTitle" label="Título del resultado" />
        <FieldTextarea v-model="form.result" label="Resultado esperado" :rows="3" :isSingle="true" />
      </template>

      <!-- DESIGN UX -->
      <template v-else-if="sectionType === 'design_ux'">
        <div class="grid grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="04" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
        <FieldInput v-model="form.focusTitle" label="Título de enfoque" />
        <FieldTextarea v-model="form.focusItems" label="Items de enfoque" help="Un item por línea" :rows="4" />
        <FieldInput v-model="form.objectiveTitle" label="Título del objetivo" />
        <FieldTextarea v-model="form.objective" label="Objetivo" :rows="3" :isSingle="true" />
      </template>

      <!-- CREATIVE SUPPORT -->
      <template v-else-if="sectionType === 'creative_support'">
        <div class="grid grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="05" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
        <FieldInput v-model="form.includesTitle" label="Título de incluye" />
        <FieldTextarea v-model="form.includes" label="Incluye" help="Un item por línea" :rows="4" />
        <FieldTextarea v-model="form.closing" label="Cierre" :rows="3" :isSingle="true" />
      </template>

      <!-- DEVELOPMENT STAGES -->
      <template v-else-if="sectionType === 'development_stages'">
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Etapas</label>
          <div v-for="(stage, idx) in form.stages" :key="idx" class="mb-4 bg-gray-50 rounded-xl p-4 border border-gray-100">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-gray-400">Etapa {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500 hover:text-red-700" @click="form.stages.splice(idx, 1)">Eliminar</button>
            </div>
            <div class="grid grid-cols-[60px_1fr] gap-3 mb-2">
              <FieldInput v-model="stage.icon" label="Icono" placeholder="✉️" />
              <FieldInput v-model="stage.title" label="Título" />
            </div>
            <FieldTextarea v-model="stage.description" label="Descripción" :rows="2" :isSingle="true" />
            <label class="flex items-center gap-2 mt-2 text-xs">
              <input type="checkbox" v-model="stage.current" class="rounded border-gray-300 text-emerald-600" />
              <span class="text-gray-600">Etapa actual</span>
            </label>
          </div>
          <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium" @click="form.stages.push({ icon: '', title: '', description: '', current: false })">
            + Agregar etapa
          </button>
        </div>
      </template>

      <!-- FUNCTIONAL REQUIREMENTS -->
      <template v-else-if="sectionType === 'functional_requirements'">
        <div class="grid grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="07" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.intro" label="Introducción" :rows="3" :isSingle="true" />
        <p class="text-xs text-gray-400 bg-gray-50 p-3 rounded-lg">
          Los grupos de requerimientos (Vistas, Componentes, Funcionalidades) y módulos se gestionan desde los modelos de RequirementGroup/Item en el backend.
        </p>
      </template>

      <!-- TIMELINE -->
      <template v-else-if="sectionType === 'timeline'">
        <FieldTextarea v-model="form.introText" label="Texto introductorio" :rows="3" :isSingle="true" />
        <FieldInput v-model="form.totalDuration" label="Duración total" placeholder="Aproximadamente 1 mes" />
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Fases</label>
          <div v-for="(phase, idx) in form.phases" :key="idx" class="mb-4 bg-gray-50 rounded-xl p-4 border border-gray-100">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-gray-400">Fase {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500 hover:text-red-700" @click="form.phases.splice(idx, 1)">Eliminar</button>
            </div>
            <div class="grid grid-cols-2 gap-3 mb-2">
              <FieldInput v-model="phase.title" label="Título" />
              <FieldInput v-model="phase.duration" label="Duración" placeholder="2 semanas" />
            </div>
            <FieldTextarea v-model="phase.description" label="Descripción" :rows="2" :isSingle="true" />
            <FieldTextarea v-model="phase.tasks" label="Tareas" help="Una por línea" :rows="3" />
            <FieldInput v-model="phase.milestone" label="Hito / Milestone" class="mt-2" />
          </div>
          <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium" @click="form.phases.push({ title: '', duration: '', description: '', tasks: '', milestone: '' })">
            + Agregar fase
          </button>
        </div>
      </template>

      <!-- INVESTMENT -->
      <template v-else-if="sectionType === 'investment'">
        <FieldTextarea v-model="form.introText" label="Texto introductorio" :rows="2" :isSingle="true" />
        <div class="grid grid-cols-2 gap-4">
          <FieldInput v-model="form.totalInvestment" label="Inversión total" placeholder="$3.500.000" />
          <FieldInput v-model="form.currency" label="Moneda" placeholder="COP" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Qué incluye</label>
          <div v-for="(item, idx) in form.whatsIncluded" :key="idx" class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-400">Item {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500" @click="form.whatsIncluded.splice(idx, 1)">Eliminar</button>
            </div>
            <div class="grid grid-cols-[60px_1fr] gap-2 mb-1">
              <FieldInput v-model="item.icon" label="Icono" placeholder="🎨" />
              <FieldInput v-model="item.title" label="Título" />
            </div>
            <FieldInput v-model="item.description" label="Descripción" />
          </div>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.whatsIncluded.push({ icon: '', title: '', description: '' })">+ Agregar item</button>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Opciones de pago</label>
          <div v-for="(opt, idx) in form.paymentOptions" :key="idx" class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-400">Opción {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500" @click="form.paymentOptions.splice(idx, 1)">Eliminar</button>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <FieldInput v-model="opt.label" label="Etiqueta" placeholder="40% al firmar" />
              <FieldInput v-model="opt.description" label="Descripción" placeholder="$596.000 COP" />
            </div>
          </div>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.paymentOptions.push({ label: '', description: '' })">+ Agregar opción</button>
        </div>
        <FieldTextarea v-model="form.paymentMethods" label="Métodos de pago" help="Uno por línea" :rows="3" />
        <FieldTextarea v-model="form.valueReasons" label="Razones de valor" help="Una por línea" :rows="3" />
      </template>

      <!-- FINAL NOTE -->
      <template v-else-if="sectionType === 'final_note'">
        <FieldTextarea v-model="form.message" label="Mensaje" :rows="5" :isSingle="true" />
        <FieldTextarea v-model="form.personalNote" label="Nota personal" :rows="3" :isSingle="true" />
        <div class="grid grid-cols-3 gap-4">
          <FieldInput v-model="form.teamName" label="Nombre del equipo" />
          <FieldInput v-model="form.teamRole" label="Rol" />
          <FieldInput v-model="form.contactEmail" label="Email de contacto" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Badges de compromiso</label>
          <div v-for="(badge, idx) in form.commitmentBadges" :key="idx" class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-400">Badge {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500" @click="form.commitmentBadges.splice(idx, 1)">Eliminar</button>
            </div>
            <div class="grid grid-cols-[60px_1fr] gap-2 mb-1">
              <FieldInput v-model="badge.icon" label="Icono" placeholder="🤝" />
              <FieldInput v-model="badge.title" label="Título" />
            </div>
            <FieldInput v-model="badge.description" label="Descripción" />
          </div>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.commitmentBadges.push({ icon: '', title: '', description: '' })">+ Agregar badge</button>
        </div>
      </template>

      <!-- NEXT STEPS -->
      <template v-else-if="sectionType === 'next_steps'">
        <FieldTextarea v-model="form.introMessage" label="Mensaje de introducción" :rows="3" :isSingle="true" />
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Pasos</label>
          <div v-for="(step, idx) in form.steps" :key="idx" class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-400">Paso {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500" @click="form.steps.splice(idx, 1)">Eliminar</button>
            </div>
            <FieldInput v-model="step.title" label="Título" class="mb-1" />
            <FieldInput v-model="step.description" label="Descripción" />
          </div>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.steps.push({ title: '', description: '' })">+ Agregar paso</button>
        </div>
        <FieldTextarea v-model="form.ctaMessage" label="Mensaje CTA" :rows="2" :isSingle="true" />
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-xl p-3 border border-gray-100">
            <p class="text-xs text-gray-400 mb-2">CTA Primario</p>
            <FieldInput v-model="form.primaryCTA.text" label="Texto" class="mb-1" />
            <FieldInput v-model="form.primaryCTA.link" label="Link" />
          </div>
          <div class="bg-gray-50 rounded-xl p-3 border border-gray-100">
            <p class="text-xs text-gray-400 mb-2">CTA Secundario</p>
            <FieldInput v-model="form.secondaryCTA.text" label="Texto" class="mb-1" />
            <FieldInput v-model="form.secondaryCTA.link" label="Link" />
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Métodos de contacto</label>
          <div v-for="(method, idx) in form.contactMethods" :key="idx" class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-400">Método {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500" @click="form.contactMethods.splice(idx, 1)">Eliminar</button>
            </div>
            <div class="grid grid-cols-4 gap-2">
              <FieldInput v-model="method.icon" label="Icono" placeholder="📧" />
              <FieldInput v-model="method.title" label="Título" />
              <FieldInput v-model="method.value" label="Valor" />
              <FieldInput v-model="method.link" label="Link" />
            </div>
          </div>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.contactMethods.push({ icon: '', title: '', value: '', link: '' })">+ Agregar método</button>
        </div>
        <FieldTextarea v-model="form.validityMessage" label="Mensaje de vigencia" :rows="2" :isSingle="true" />
        <FieldTextarea v-model="form.thankYouMessage" label="Mensaje de agradecimiento" :rows="2" :isSingle="true" />
      </template>
    </div>

    <!-- Raw JSON toggle -->
    <div class="mt-6 border-t border-gray-100 pt-4">
      <button type="button" class="text-xs text-gray-400 hover:text-gray-600" @click="showRawJson = !showRawJson">
        {{ showRawJson ? 'Ocultar' : 'Mostrar' }} JSON crudo
      </button>
      <div v-if="showRawJson" class="mt-2">
        <textarea
          v-model="rawJsonText"
          rows="10"
          class="w-full px-4 py-3 border border-gray-200 rounded-xl text-xs font-mono bg-gray-50 resize-y outline-none"
          readonly
        />
      </div>
    </div>

    <!-- Save button -->
    <div class="flex items-center gap-3 mt-5">
      <button
        type="button"
        :disabled="isSaving"
        class="px-5 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium
               hover:bg-emerald-700 transition-colors disabled:opacity-50"
        @click="handleSave"
      >
        {{ isSaving ? 'Guardando...' : 'Guardar Sección' }}
      </button>
      <span v-if="savedMsg" class="text-xs text-green-600">{{ savedMsg }}</span>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue';

// --- Inline sub-components ---
const FieldInput = {
  props: { modelValue: String, label: String, placeholder: String },
  emits: ['update:modelValue'],
  template: `
    <div>
      <label v-if="label" class="block text-xs text-gray-500 mb-0.5">{{ label }}</label>
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :placeholder="placeholder"
        class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
      />
    </div>
  `,
};

const FieldTextarea = {
  props: { modelValue: String, label: String, help: String, rows: { type: Number, default: 4 }, isSingle: Boolean },
  emits: ['update:modelValue'],
  template: `
    <div>
      <label v-if="label" class="block text-xs text-gray-500 mb-0.5">{{ label }}</label>
      <textarea
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :rows="rows"
        class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y"
      />
      <p v-if="help" class="text-[10px] text-gray-400 mt-0.5">{{ help }}</p>
    </div>
  `,
};

const props = defineProps({
  section: { type: Object, required: true },
});

const emit = defineEmits(['save']);

const sectionType = computed(() => props.section.section_type);
const sectionTitle = ref(props.section.title);
const isSaving = ref(false);
const savedMsg = ref('');
const showRawJson = ref(false);
const pasteMode = ref(false);
const pasteText = ref('');
const pasteMsg = ref('');

const PASTE_SUPPORTED_TYPES = [
  'executive_summary', 'context_diagnostic', 'design_ux',
  'creative_support', 'conversion_strategy', 'final_note', 'next_steps',
];
const hasPasteSupport = computed(() => PASTE_SUPPORTED_TYPES.includes(sectionType.value));

function processPastedContent() {
  const text = pasteText.value.trim();
  if (!text) return;

  const paragraphs = [];
  const listItems = [];
  let closingText = '';

  // Split by double newlines into blocks
  const blocks = text.split(/\n\s*\n/).map(b => b.trim()).filter(Boolean);

  for (const block of blocks) {
    const lines = block.split('\n').map(l => l.trim()).filter(Boolean);
    const allBullets = lines.every(l => /^[\*\-•]\s/.test(l));
    if (allBullets && lines.length > 0) {
      for (const line of lines) {
        listItems.push(line.replace(/^[\*\-•]\s*/, ''));
      }
    } else {
      paragraphs.push(lines.join(' '));
    }
  }

  const type = sectionType.value;

  if (type === 'executive_summary') {
    form.paragraphs = paragraphs.join('\n');
    if (listItems.length) form.highlights = listItems.join('\n');
  } else if (type === 'context_diagnostic') {
    if (paragraphs.length > 1) {
      form.opportunity = paragraphs.pop();
    }
    form.paragraphs = paragraphs.join('\n');
    if (listItems.length) form.issues = listItems.join('\n');
  } else if (type === 'design_ux') {
    if (paragraphs.length > 1) {
      form.objective = paragraphs.pop();
    }
    form.paragraphs = paragraphs.join('\n');
    if (listItems.length) form.focusItems = listItems.join('\n');
  } else if (type === 'creative_support') {
    if (paragraphs.length > 1) {
      form.closing = paragraphs.pop();
    }
    form.paragraphs = paragraphs.join('\n');
    if (listItems.length) form.includes = listItems.join('\n');
  } else if (type === 'conversion_strategy') {
    if (paragraphs.length > 1) {
      form.result = paragraphs.pop();
    }
    form.intro = paragraphs.join('\n');
  } else if (type === 'final_note') {
    if (paragraphs.length > 1) {
      form.personalNote = paragraphs.pop();
    }
    form.message = paragraphs.join('\n');
  } else if (type === 'next_steps') {
    form.introMessage = paragraphs.length ? paragraphs[0] : '';
    if (paragraphs.length > 1) {
      form.ctaMessage = paragraphs[paragraphs.length - 1];
    }
  }

  pasteMsg.value = '✓ Campos llenados. Revisa el formulario para ajustes.';
  pasteMode.value = false;
  setTimeout(() => { pasteMsg.value = ''; }, 4000);
}

// --- Build form state from content_json ---
const form = reactive(buildFormFromJson(props.section.content_json || {}, props.section.section_type));

watch(() => props.section, (s) => {
  sectionTitle.value = s.title;
  Object.assign(form, buildFormFromJson(s.content_json || {}, s.section_type));
}, { deep: true });

// --- Helpers: JSON ↔ form conversion ---

function arrToText(arr) {
  return Array.isArray(arr) ? arr.join('\n') : (arr || '');
}

function textToArr(text) {
  if (!text) return [];
  return text.split('\n').map(l => l.trim()).filter(Boolean);
}

function buildFormFromJson(json, type) {
  const j = json || {};
  switch (type) {
    case 'greeting':
      return { clientName: j.clientName || '', inspirationalQuote: j.inspirationalQuote || '' };
    case 'executive_summary':
      return { index: j.index || '', title: j.title || '', paragraphs: arrToText(j.paragraphs), highlightsTitle: j.highlightsTitle || '', highlights: arrToText(j.highlights) };
    case 'context_diagnostic':
      return { index: j.index || '', title: j.title || '', paragraphs: arrToText(j.paragraphs), issuesTitle: j.issuesTitle || '', issues: arrToText(j.issues), opportunityTitle: j.opportunityTitle || '', opportunity: j.opportunity || '' };
    case 'conversion_strategy':
      return { index: j.index || '', title: j.title || '', intro: j.intro || '', steps: (j.steps || []).map(s => ({ title: s.title || '', bullets: arrToText(s.bullets) })), resultTitle: j.resultTitle || '', result: j.result || '' };
    case 'design_ux':
      return { index: j.index || '', title: j.title || '', paragraphs: arrToText(j.paragraphs), focusTitle: j.focusTitle || '', focusItems: arrToText(j.focusItems), objectiveTitle: j.objectiveTitle || '', objective: j.objective || '' };
    case 'creative_support':
      return { index: j.index || '', title: j.title || '', paragraphs: arrToText(j.paragraphs), includesTitle: j.includesTitle || '', includes: arrToText(j.includes), closing: j.closing || '' };
    case 'development_stages':
      return { stages: (j.stages || []).map(s => ({ icon: s.icon || '', title: s.title || '', description: s.description || '', current: !!s.current })) };
    case 'functional_requirements':
      return { index: j.index || '', title: j.title || '', intro: j.intro || '', technicalSpecs: j.technicalSpecs || [], integrations: j.integrations || [] };
    case 'timeline':
      return { introText: j.introText || '', totalDuration: j.totalDuration || '', phases: (j.phases || []).map(p => ({ title: p.title || '', duration: p.duration || '', description: p.description || '', tasks: arrToText(p.tasks), milestone: p.milestone || '' })), calendarWeeks: j.calendarWeeks || [] };
    case 'investment':
      return { introText: j.introText || '', totalInvestment: j.totalInvestment || '', currency: j.currency || 'COP', whatsIncluded: (j.whatsIncluded || []).map(i => ({ ...i })), paymentOptions: (j.paymentOptions || []).map(o => ({ ...o })), hostingPlan: j.hostingPlan || {}, paymentMethods: arrToText(j.paymentMethods), valueReasons: arrToText(j.valueReasons) };
    case 'final_note':
      return { message: j.message || '', personalNote: j.personalNote || '', teamName: j.teamName || '', teamRole: j.teamRole || '', contactEmail: j.contactEmail || '', commitmentBadges: (j.commitmentBadges || []).map(b => ({ ...b })) };
    case 'next_steps':
      return { introMessage: j.introMessage || '', steps: (j.steps || []).map(s => ({ ...s })), ctaMessage: j.ctaMessage || '', primaryCTA: { text: j.primaryCTA?.text || '', link: j.primaryCTA?.link || '' }, secondaryCTA: { text: j.secondaryCTA?.text || '', link: j.secondaryCTA?.link || '' }, contactMethods: (j.contactMethods || []).map(m => ({ ...m })), validityMessage: j.validityMessage || '', thankYouMessage: j.thankYouMessage || '' };
    default:
      return {};
  }
}

function formToJson(formData, type) {
  const f = formData;
  switch (type) {
    case 'greeting':
      return { clientName: f.clientName, inspirationalQuote: f.inspirationalQuote };
    case 'executive_summary':
      return { index: f.index, title: f.title, paragraphs: textToArr(f.paragraphs), highlightsTitle: f.highlightsTitle, highlights: textToArr(f.highlights) };
    case 'context_diagnostic':
      return { index: f.index, title: f.title, paragraphs: textToArr(f.paragraphs), issuesTitle: f.issuesTitle, issues: textToArr(f.issues), opportunityTitle: f.opportunityTitle, opportunity: f.opportunity };
    case 'conversion_strategy':
      return { index: f.index, title: f.title, intro: f.intro, steps: f.steps.map(s => ({ title: s.title, bullets: textToArr(s.bullets) })), resultTitle: f.resultTitle, result: f.result };
    case 'design_ux':
      return { index: f.index, title: f.title, paragraphs: textToArr(f.paragraphs), focusTitle: f.focusTitle, focusItems: textToArr(f.focusItems), objectiveTitle: f.objectiveTitle, objective: f.objective };
    case 'creative_support':
      return { index: f.index, title: f.title, paragraphs: textToArr(f.paragraphs), includesTitle: f.includesTitle, includes: textToArr(f.includes), closing: f.closing };
    case 'development_stages':
      return { stages: f.stages.map(s => ({ icon: s.icon, title: s.title, description: s.description, ...(s.current ? { current: true } : {}) })) };
    case 'functional_requirements':
      return { index: f.index, title: f.title, intro: f.intro, technicalSpecs: f.technicalSpecs, integrations: f.integrations };
    case 'timeline':
      return { introText: f.introText, totalDuration: f.totalDuration, phases: f.phases.map(p => ({ title: p.title, duration: p.duration, description: p.description, tasks: textToArr(p.tasks), milestone: p.milestone })), calendarWeeks: f.calendarWeeks || [] };
    case 'investment':
      return { introText: f.introText, totalInvestment: f.totalInvestment, currency: f.currency, whatsIncluded: f.whatsIncluded, paymentOptions: f.paymentOptions, hostingPlan: f.hostingPlan || {}, paymentMethods: textToArr(f.paymentMethods), valueReasons: textToArr(f.valueReasons) };
    case 'final_note':
      return { message: f.message, personalNote: f.personalNote, teamName: f.teamName, teamRole: f.teamRole, contactEmail: f.contactEmail, commitmentBadges: f.commitmentBadges };
    case 'next_steps':
      return { introMessage: f.introMessage, steps: f.steps, ctaMessage: f.ctaMessage, primaryCTA: f.primaryCTA, secondaryCTA: f.secondaryCTA, contactMethods: f.contactMethods, validityMessage: f.validityMessage, thankYouMessage: f.thankYouMessage };
    default:
      return {};
  }
}

const rawJsonText = computed(() => {
  try {
    return JSON.stringify(formToJson(form, sectionType.value), null, 2);
  } catch { return '{}'; }
});

function handleSave() {
  isSaving.value = true;
  savedMsg.value = '';
  try {
    const contentJson = formToJson(form, sectionType.value);
    emit('save', {
      sectionId: props.section.id,
      payload: {
        title: sectionTitle.value,
        is_wide_panel: props.section.is_wide_panel,
        content_json: contentJson,
      },
    });
    savedMsg.value = '✓ Guardado';
    setTimeout(() => { savedMsg.value = ''; }, 3000);
  } finally {
    isSaving.value = false;
  }
}
</script>
