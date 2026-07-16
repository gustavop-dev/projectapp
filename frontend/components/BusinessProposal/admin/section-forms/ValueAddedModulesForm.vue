<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <FieldInput v-model="form.index" label="Índice" placeholder="9" />
    <FieldInput v-model="form.title" label="Título" />
  </div>
  <FieldTextarea v-model="form.intro" label="Intro (por qué se incluyen sin costo)" :rows="3" :isSingle="true" />

  <div>
    <label class="block text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Módulos a destacar</label>
    <p class="text-[11px] text-text-muted mb-3">
      Selecciona qué módulos base aparecerán en esta sección de "incluido sin costo". Los datos completos
      (icono, título, items) viven en la sección Requerimientos funcionales.
    </p>
    <div class="space-y-3">
      <div v-for="id in valueAddedAvailableIds" :key="id"
           class="border border-border-default dark:border-white/[0.08] rounded-xl p-3 bg-surface-raised">
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            :checked="form.module_ids.includes(id)"
            class="rounded border-input-border text-text-brand focus:ring-focus-ring/30"
            @change="toggleValueAddedId(id, $event.target.checked)"
          />
          <span class="text-sm font-medium text-text-default">
            {{ valueAddedModuleLabel(id) }}
          </span>
        </label>
        <template v-if="form.module_ids.includes(id)">
          <FieldTextarea
            :modelValue="form.justifications[id] || ''"
            label="Justificación corta"
            help="Máx ~180 caracteres. Una oración explicando por qué este módulo aporta valor."
            :rows="2"
            :isSingle="true"
            class="mt-2"
            @update:modelValue="form.justifications[id] = $event"
          />

          <!-- Condiciones del módulo (Req 3) -->
          <div class="mt-3 border-t border-border-default dark:border-white/[0.08] pt-3 space-y-2">
            <p class="text-[11px] text-text-muted uppercase tracking-wider">Condiciones del beneficio</p>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <label class="block">
                <span class="block text-xs text-text-muted mb-0.5">Precio mínimo (USD)</span>
                <BaseCurrencyInput
                  :model-value="getCond(id, 'min_price_usd')"
                  placeholder="0 = sin mínimo"
                  @update:model-value="setCondNum(id, 'min_price_usd', $event)"
                />
              </label>
              <label class="block">
                <span class="block text-xs text-text-muted mb-0.5">Precio mínimo (COP)</span>
                <BaseCurrencyInput
                  :model-value="getCond(id, 'min_price_cop')"
                  placeholder="0 = sin mínimo"
                  @update:model-value="setCondNum(id, 'min_price_cop', $event)"
                />
              </label>
              <FieldInput
                :modelValue="getCond(id, 'duration_months')"
                label="Duración (meses)"
                placeholder="vacío = sin límite"
                @update:modelValue="setCondNum(id, 'duration_months', $event)"
              />
            </div>
            <FieldTextarea
              :modelValue="getCond(id, 'discretionary_note')"
              label="Nota discrecional"
              help="Ej: se implementa si la lógica de negocio lo permite y tiene sentido medir/automatizar."
              :rows="2"
              :isSingle="true"
              @update:modelValue="setCond(id, 'discretionary_note', $event)"
            />
            <FieldTextarea
              :modelValue="getCond(id, 'terms')"
              label="Términos y condiciones"
              help="Texto que verá el cliente en el modal de T&C de este módulo."
              :rows="4"
              :isSingle="true"
              @update:modelValue="setCond(id, 'terms', $event)"
            />
          </div>
        </template>
      </div>
    </div>
  </div>

  <FieldTextarea v-model="form.footer_note" label="Nota de cierre" :rows="2" :isSingle="true" />
</template>

<script setup>
import { computed } from 'vue';
import { FieldInput, FieldTextarea } from './fields.js';
import { VALUE_ADDED_DEFAULT_MODULE_IDS } from '~/components/BusinessProposal/admin/sectionEditorUtils.js';

const props = defineProps({
  form: { type: Object, required: true },
  proposalData: { type: Object, default: () => ({}) },
  /** All sections in the proposal (used to discover available group ids). */
  allSections: { type: Array, default: () => [] },
});

const valueAddedFreeGroups = computed(() => {
  const fr = (props.allSections || []).find((s) => s.section_type === 'functional_requirements');
  const groups = fr?.content_json?.groups || [];
  return groups.filter((g) => g && g.id && (g.price_percent ?? 0) === 0);
});

const valueAddedLabelById = computed(() => {
  const map = new Map();
  for (const g of valueAddedFreeGroups.value) {
    map.set(g.id, `${g.icon || ''} ${g.title || g.id}`.trim());
  }
  return map;
});

const valueAddedAvailableIds = computed(() => {
  const fromGroups = valueAddedFreeGroups.value.map((g) => g.id);
  if (fromGroups.length) return fromGroups;
  return [...VALUE_ADDED_DEFAULT_MODULE_IDS];
});

function valueAddedModuleLabel(id) {
  return valueAddedLabelById.value.get(id) || id;
}

function toggleValueAddedId(id, checked) {
  if (!Array.isArray(props.form.module_ids)) props.form.module_ids = [];
  if (!props.form.justifications) props.form.justifications = {};
  const idx = props.form.module_ids.indexOf(id);
  if (checked && idx === -1) {
    props.form.module_ids.push(id);
    if (!(id in props.form.justifications)) props.form.justifications[id] = '';
  } else if (!checked && idx !== -1) {
    props.form.module_ids.splice(idx, 1);
  }
}

function getCond(id, key) {
  const value = props.form.conditions?.[id]?.[key];
  return value == null ? '' : value;
}

function ensureCond(id) {
  if (!props.form.conditions) props.form.conditions = {};
  if (!props.form.conditions[id]) props.form.conditions[id] = {};
  return props.form.conditions[id];
}

function setCond(id, key, value) {
  ensureCond(id)[key] = value;
}

function setCondNum(id, key, value) {
  // Empty → null (no minimum / no limit); otherwise store a Number.
  const cond = ensureCond(id);
  cond[key] = value === '' || value == null ? null : Number(value);
}
</script>
