<template>
  <div v-show="isOpen" class="mb-4">
    <div class="flex flex-wrap gap-2 items-center p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl">
      <FilterDropdown
        label="Estado"
        :options="statusOptions"
        :model-value="modelValue.statuses"
        @update:model-value="emit('update:modelValue', { ...modelValue, statuses: $event })"
      />
      <FilterDropdown
        label="Tipo de proyecto"
        :options="projectTypeOptions"
        :model-value="modelValue.projectTypes"
        @update:model-value="emit('update:modelValue', { ...modelValue, projectTypes: $event })"
      />
      <FilterDropdown
        label="Mercado"
        :options="marketTypeOptions"
        :model-value="modelValue.marketTypes"
        @update:model-value="emit('update:modelValue', { ...modelValue, marketTypes: $event })"
      />
      <FilterDropdown
        label="Moneda"
        :options="currencyOptions"
        :model-value="modelValue.currencies"
        @update:model-value="emit('update:modelValue', { ...modelValue, currencies: $event })"
      />
      <FilterDropdown
        label="Idioma"
        :options="languageOptions"
        :model-value="modelValue.languages"
        @update:model-value="emit('update:modelValue', { ...modelValue, languages: $event })"
      />

      <div class="w-px h-5 bg-gray-200 dark:bg-gray-600 self-center mx-0.5" />

      <FilterRangeDropdown
        label="Inversión"
        type="number"
        :min-value="modelValue.investmentMin"
        :max-value="modelValue.investmentMax"
        @update:min-value="emit('update:modelValue', { ...modelValue, investmentMin: $event })"
        @update:max-value="emit('update:modelValue', { ...modelValue, investmentMax: $event })"
      />
      <FilterRangeDropdown
        label="Heat Score"
        type="number"
        unit="/ 10"
        min-placeholder="0"
        max-placeholder="10"
        :min-value="modelValue.heatScoreMin"
        :max-value="modelValue.heatScoreMax"
        @update:min-value="emit('update:modelValue', { ...modelValue, heatScoreMin: $event })"
        @update:max-value="emit('update:modelValue', { ...modelValue, heatScoreMax: $event })"
      />
      <FilterRangeDropdown
        label="Vistas"
        type="number"
        :min-value="modelValue.viewCountMin"
        :max-value="modelValue.viewCountMax"
        @update:min-value="emit('update:modelValue', { ...modelValue, viewCountMin: $event })"
        @update:max-value="emit('update:modelValue', { ...modelValue, viewCountMax: $event })"
      />

      <div class="w-px h-5 bg-gray-200 dark:bg-gray-600 self-center mx-0.5" />

      <FilterRangeDropdown
        label="Creación"
        type="date"
        min-placeholder="Desde"
        max-placeholder="Hasta"
        :min-value="modelValue.createdAfter"
        :max-value="modelValue.createdBefore"
        @update:min-value="emit('update:modelValue', { ...modelValue, createdAfter: $event })"
        @update:max-value="emit('update:modelValue', { ...modelValue, createdBefore: $event })"
      />
      <FilterRangeDropdown
        label="Actividad"
        type="date"
        min-placeholder="Desde"
        max-placeholder="Hasta"
        :min-value="modelValue.lastActivityAfter"
        :max-value="modelValue.lastActivityBefore"
        @update:min-value="emit('update:modelValue', { ...modelValue, lastActivityAfter: $event })"
        @update:max-value="emit('update:modelValue', { ...modelValue, lastActivityBefore: $event })"
      />

      <div class="w-px h-5 bg-gray-200 dark:bg-gray-600 self-center mx-0.5" />

      <FilterDropdown
        label="Activo"
        :options="activeStatusOptions"
        :model-value="modelValue.isActive !== 'all' ? [modelValue.isActive] : []"
        @update:model-value="emit('update:modelValue', { ...modelValue, isActive: $event.length ? $event[$event.length - 1] : 'all' })"
      />

      <div ref="engagementRef" class="relative">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border whitespace-nowrap"
          :class="modelValue.technicalViewed
            ? 'bg-teal-600 text-white border-teal-600 hover:bg-teal-700'
            : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'"
          @click="engagementOpen = !engagementOpen"
        >
          🔬 Engagement
          <span
            v-if="modelValue.technicalViewed"
            class="inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold bg-white text-teal-600"
          >1</span>
          <svg class="w-3 h-3 ml-0.5 opacity-60" :class="{ 'rotate-180': engagementOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <Transition name="dropdown-fade">
          <div
            v-if="engagementOpen"
            class="absolute top-full left-0 mt-1 z-50 w-60 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg py-2"
          >
            <label class="flex items-center gap-2.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer">
              <input
                type="checkbox"
                :checked="modelValue.technicalViewed"
                class="w-3.5 h-3.5 rounded border-gray-300 dark:border-gray-600 accent-teal-600"
                @change="emit('update:modelValue', { ...modelValue, technicalViewed: $event.target.checked })"
              />
              <span>Solo det. técnico visto</span>
            </label>
          </div>
        </Transition>
      </div>

      <div class="flex-1" />
      <button
        v-if="filterCount > 0"
        type="button"
        class="text-xs text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors font-medium ml-auto whitespace-nowrap"
        @click="$emit('reset')"
      >
        Limpiar todo
      </button>
    </div>

    <div v-if="activeChips.length > 0" class="flex flex-wrap gap-1.5 mt-2 px-1">
      <span
        v-for="chip in activeChips"
        :key="chip.key"
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-700"
      >
        {{ chip.label }}
        <button
          type="button"
          class="ml-0.5 hover:text-red-500 dark:hover:text-red-400 leading-none"
          @click="clearChip(chip.key)"
        >&times;</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';

const props = defineProps({
  modelValue: { type: Object, required: true },
  isOpen: { type: Boolean, default: false },
  filterCount: { type: Number, default: 0 },
});

const emit = defineEmits(['update:modelValue', 'reset']);

const engagementRef = ref(null);
const engagementOpen = ref(false);
onClickOutside(engagementRef, () => { engagementOpen.value = false; });

const statusOptions = [
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviadas' },
  { value: 'viewed', label: 'Vistas' },
  { value: 'accepted', label: 'Aceptadas' },
  { value: 'rejected', label: 'Rechazadas' },
  { value: 'negotiating', label: 'Negociando' },
  { value: 'expired', label: 'Expiradas' },
];

const projectTypeOptions = [
  { value: 'website', label: 'Sitio Web' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'webapp', label: 'Aplicación Web' },
  { value: 'landing', label: 'Landing Page' },
  { value: 'redesign', label: 'Rediseño' },
  { value: 'mobile_app', label: 'App Móvil' },
  { value: 'branding', label: 'Branding' },
  { value: 'cms', label: 'Sistema CMS' },
  { value: 'portal', label: 'Portal / Intranet' },
  { value: 'api_integration', label: 'Integración de APIs' },
  { value: 'marketplace', label: 'Marketplace' },
  { value: 'erp', label: 'Sistema ERP' },
  { value: 'booking', label: 'Sistema de Reservas' },
  { value: 'dashboard', label: 'Dashboard / Reportes' },
  { value: 'crm', label: 'Sistema CRM' },
  { value: 'saas', label: 'SaaS / Plataforma' },
  { value: 'chatbot', label: 'Chatbot / IA' },
  { value: 'ai_tool', label: 'Herramienta con IA' },
  { value: 'automation', label: 'Automatización' },
  { value: 'data_analytics', label: 'Analítica de Datos' },
  { value: 'plugin_extension', label: 'Plugin / Extensión' },
  { value: 'other', label: 'Otro' },
];

const marketTypeOptions = [
  { value: 'b2b', label: 'B2B' },
  { value: 'b2c', label: 'B2C' },
  { value: 'saas', label: 'SaaS' },
  { value: 'retail', label: 'Retail' },
  { value: 'services', label: 'Servicios profesionales' },
  { value: 'health', label: 'Salud' },
  { value: 'education', label: 'Educación' },
  { value: 'real_estate', label: 'Inmobiliaria' },
  { value: 'fintech', label: 'Fintech' },
  { value: 'restaurant', label: 'Restaurantes' },
  { value: 'tourism', label: 'Turismo' },
  { value: 'logistics', label: 'Logística' },
  { value: 'sports', label: 'Deportes' },
  { value: 'legal', label: 'Servicios Legales' },
  { value: 'construction', label: 'Construcción' },
  { value: 'media', label: 'Medios' },
  { value: 'ngo', label: 'ONG / Sector Público' },
  { value: 'agriculture', label: 'Agro' },
  { value: 'tech', label: 'Tecnología' },
  { value: 'consulting', label: 'Consultoría' },
  { value: 'automotive', label: 'Automotriz' },
  { value: 'fashion', label: 'Moda' },
  { value: 'beauty', label: 'Belleza' },
  { value: 'manufacturing', label: 'Manufactura' },
  { value: 'energy', label: 'Energía' },
  { value: 'gaming', label: 'Gaming' },
  { value: 'other', label: 'Otro' },
];

const currencyOptions = [
  { value: 'COP', label: 'COP' },
  { value: 'USD', label: 'USD' },
];

const languageOptions = [
  { value: 'es', label: 'Español' },
  { value: 'en', label: 'English' },
];

const activeStatusOptions = [
  { value: 'active', label: 'Activas' },
  { value: 'inactive', label: 'Inactivas' },
];

const projectTypeLabelMap = Object.fromEntries(projectTypeOptions.map((o) => [o.value, o.label]));
const marketTypeLabelMap = Object.fromEntries(marketTypeOptions.map((o) => [o.value, o.label]));
const statusLabelMap = Object.fromEntries(statusOptions.map((o) => [o.value, o.label]));

function formatRange(min, max, unit = '') {
  const u = unit ? ` ${unit}` : '';
  if (min != null && max != null) return `${min}–${max}${u}`;
  if (min != null) return `≥ ${min}${u}`;
  if (max != null) return `≤ ${max}${u}`;
  return '';
}

function formatDateRange(after, before) {
  if (after && before) return `${after} → ${before}`;
  if (after) return `desde ${after}`;
  if (before) return `hasta ${before}`;
  return '';
}

const activeChips = computed(() => {
  const chips = [];
  const mv = props.modelValue;

  if (mv.statuses?.length)
    chips.push({ key: 'statuses', label: `Estado: ${mv.statuses.map((s) => statusLabelMap[s] || s).join(', ')}` });

  if (mv.projectTypes?.length)
    chips.push({ key: 'projectTypes', label: `Tipo: ${mv.projectTypes.map((t) => projectTypeLabelMap[t] || t).join(', ')}` });

  if (mv.marketTypes?.length)
    chips.push({ key: 'marketTypes', label: `Mercado: ${mv.marketTypes.map((t) => marketTypeLabelMap[t] || t).join(', ')}` });

  if (mv.currencies?.length)
    chips.push({ key: 'currencies', label: `Moneda: ${mv.currencies.join(', ')}` });

  if (mv.languages?.length)
    chips.push({ key: 'languages', label: `Idioma: ${mv.languages.join(', ').toUpperCase()}` });

  const inv = formatRange(mv.investmentMin, mv.investmentMax);
  if (inv) chips.push({ key: 'investment', label: `Inversión: ${inv}` });

  const hs = formatRange(mv.heatScoreMin, mv.heatScoreMax, '/ 10');
  if (hs) chips.push({ key: 'heatScore', label: `Heat Score: ${hs}` });

  const vc = formatRange(mv.viewCountMin, mv.viewCountMax);
  if (vc) chips.push({ key: 'viewCount', label: `Vistas: ${vc}` });

  const cr = formatDateRange(mv.createdAfter, mv.createdBefore);
  if (cr) chips.push({ key: 'createdRange', label: `Creación: ${cr}` });

  const ar = formatDateRange(mv.lastActivityAfter, mv.lastActivityBefore);
  if (ar) chips.push({ key: 'activityRange', label: `Actividad: ${ar}` });

  if (mv.isActive !== 'all')
    chips.push({ key: 'isActive', label: mv.isActive === 'active' ? 'Solo activas' : 'Solo inactivas' });

  if (mv.technicalViewed)
    chips.push({ key: 'technicalViewed', label: 'Det. técnico visto' });

  return chips;
});

const CHIP_RESET = {
  statuses:       (mv) => { mv.statuses = []; },
  projectTypes:   (mv) => { mv.projectTypes = []; },
  marketTypes:    (mv) => { mv.marketTypes = []; },
  currencies:     (mv) => { mv.currencies = []; },
  languages:      (mv) => { mv.languages = []; },
  investment:     (mv) => { mv.investmentMin = null; mv.investmentMax = null; },
  heatScore:      (mv) => { mv.heatScoreMin = null; mv.heatScoreMax = null; },
  viewCount:      (mv) => { mv.viewCountMin = null; mv.viewCountMax = null; },
  createdRange:   (mv) => { mv.createdAfter = null; mv.createdBefore = null; },
  activityRange:  (mv) => { mv.lastActivityAfter = null; mv.lastActivityBefore = null; },
  isActive:       (mv) => { mv.isActive = 'all'; },
  technicalViewed:(mv) => { mv.technicalViewed = false; },
};

function clearChip(key) {
  const mv = { ...props.modelValue };
  CHIP_RESET[key]?.(mv);
  emit('update:modelValue', mv);
}
</script>
