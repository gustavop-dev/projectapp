<template>
  <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
    <!-- Header -->
    <div
      class="flex flex-wrap items-center justify-between gap-2 px-5 py-3 border-b border-gray-100 dark:border-gray-700 cursor-pointer select-none"
      @click="expanded = !expanded"
    >
      <div class="flex items-center gap-2 min-w-0">
        <span class="text-base">{{ meta.icon }}</span>
        <div class="min-w-0">
          <div class="text-sm font-semibold text-gray-800 dark:text-gray-100 truncate">
            {{ section.title || meta.label }}
          </div>
          <div class="text-xs text-gray-400 dark:text-gray-500">
            {{ meta.label }} · orden {{ section.order }}
          </div>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span
          class="px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wide"
          :class="section.is_enabled
            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300'
            : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'"
        >
          {{ section.is_enabled ? 'Activa' : 'Oculta' }}
        </span>
        <span
          class="px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wide bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
        >
          {{ visibilityLabel }}
        </span>
        <svg
          class="w-4 h-4 text-gray-400 transition-transform"
          :class="{ 'rotate-180': expanded }"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>

    <!-- Body -->
    <div v-if="expanded" class="p-5 space-y-4">
      <!-- Meta bar -->
      <div class="grid sm:grid-cols-3 gap-3 text-sm">
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Título</label>
          <input
            type="text"
            v-model="localSection.title"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 rounded-lg text-sm"
            @change="onMetaChange"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Visibilidad</label>
          <select
            v-model="localSection.visibility"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 rounded-lg text-sm"
            @change="onMetaChange"
          >
            <option v-for="opt in visibilityOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="flex items-end gap-3">
          <label class="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
            <input type="checkbox" v-model="localSection.is_enabled" class="rounded" @change="onMetaChange" />
            Activa en la vista pública
          </label>
        </div>
      </div>

      <!-- Per-type form -->
      <component
        :is="FormComponent"
        v-model="form"
        @update:modelValue="onFormChange"
      />

      <!-- Footer -->
      <div class="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
        <button
          type="button"
          class="text-xs text-rose-600 dark:text-rose-400 hover:underline"
          @click="$emit('reset')"
        >
          Restaurar contenido por defecto
        </button>
        <div class="text-xs text-gray-400 dark:text-gray-500">
          <span v-if="isSaving">Guardando…</span>
          <span v-else-if="lastSavedAt">Guardado {{ lastSavedAt }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, shallowRef } from 'vue';
import {
  SECTION_META,
  VISIBILITY_OPTIONS,
  buildFormFromJson,
  formToJson,
} from './diagnosticSectionEditorUtils';
import PurposeForm from './sections/PurposeForm.vue';
import RadiographyForm from './sections/RadiographyForm.vue';
import CategoriesForm from './sections/CategoriesForm.vue';
import DeliveryStructureForm from './sections/DeliveryStructureForm.vue';
import ExecutiveSummaryForm from './sections/ExecutiveSummaryForm.vue';
import CostForm from './sections/CostForm.vue';
import TimelineForm from './sections/TimelineForm.vue';
import ScopeForm from './sections/ScopeForm.vue';

const props = defineProps({
  section: { type: Object, required: true },
  isSaving: { type: Boolean, default: false },
  lastSavedAt: { type: String, default: '' },
});

const emit = defineEmits(['update:section', 'update:content', 'reset']);

const expanded = ref(false);
const visibilityOptions = VISIBILITY_OPTIONS;

const meta = computed(() => SECTION_META[props.section.section_type] || { label: props.section.section_type, icon: '📄' });
const visibilityLabel = computed(() =>
  visibilityOptions.find((o) => o.value === props.section.visibility)?.label ?? props.section.visibility,
);

const FORM_COMPONENTS = {
  purpose: PurposeForm,
  radiography: RadiographyForm,
  categories: CategoriesForm,
  delivery_structure: DeliveryStructureForm,
  executive_summary: ExecutiveSummaryForm,
  cost: CostForm,
  timeline: TimelineForm,
  scope: ScopeForm,
};

const FormComponent = shallowRef(FORM_COMPONENTS[props.section.section_type] || null);

const localSection = reactive({
  title: props.section.title,
  visibility: props.section.visibility,
  is_enabled: props.section.is_enabled,
});

const form = ref(buildFormFromJson(props.section.section_type, props.section.content_json));

// Rehydrate only when the incoming section row swaps (different id/type) —
// not on every inbound save merge, otherwise in-flight keystrokes are
// clobbered by the parent's merge after the debounced save returns.
watch(
  () => [props.section.id, props.section.section_type],
  () => {
    localSection.title = props.section.title;
    localSection.visibility = props.section.visibility;
    localSection.is_enabled = props.section.is_enabled;
    FormComponent.value = FORM_COMPONENTS[props.section.section_type] || null;
    form.value = buildFormFromJson(props.section.section_type, props.section.content_json);
  },
);

function onMetaChange() {
  emit('update:section', { ...localSection });
}

function onFormChange(next) {
  form.value = next;
  const contentJson = formToJson(props.section.section_type, next);
  emit('update:content', contentJson);
}
</script>
