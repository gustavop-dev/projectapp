<template>
  <div v-show="isOpen" class="mb-4">
    <div class="bg-surface border border-border-default rounded-xl divide-y divide-border-muted">

      <!-- Propuestas -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Propuestas</span>
        <ProposalFilterDropdown
          label="Estado de propuesta"
          :options="statusOptions"
          :model-value="modelValue.lastStatuses"
          @update:model-value="emit('update:modelValue', { ...modelValue, lastStatuses: $event })"
        />
        <ProposalFilterRangeDropdown
          label="Total"
          type="number"
          min-placeholder="Mín"
          max-placeholder="Máx"
          :min-value="modelValue.totalProposalsMin"
          :max-value="modelValue.totalProposalsMax"
          @update:min-value="emit('update:modelValue', { ...modelValue, totalProposalsMin: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, totalProposalsMax: $event })"
        />
        <ProposalFilterRangeDropdown
          label="Aceptadas"
          type="number"
          min-placeholder="Mín"
          max-placeholder="Máx"
          :min-value="modelValue.acceptedMin"
          :max-value="modelValue.acceptedMax"
          @update:min-value="emit('update:modelValue', { ...modelValue, acceptedMin: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, acceptedMax: $event })"
        />
      </div>

      <!-- Diagnóstico -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Diagnóstico</span>
        <ProposalFilterDropdown
          label="Diagnóstico"
          test-id="client-filter-diagnostic-status"
          :options="diagnosticStatusOptions"
          :model-value="modelValue.diagnosticStatus || []"
          @update:model-value="emit('update:modelValue', { ...modelValue, diagnosticStatus: $event })"
        />
      </div>

      <!-- Proyectos -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Proyectos</span>
        <ProposalFilterDropdown
          label="Proyecto"
          test-id="client-filter-project-status"
          :options="projectStatusOptions"
          :model-value="modelValue.projectStatus || []"
          @update:model-value="emit('update:modelValue', { ...modelValue, projectStatus: $event })"
        />
        <ProposalFilterDropdown
          label="Tipo de proyecto"
          :options="projectTypeOptions"
          :model-value="modelValue.projectTypes"
          @update:model-value="emit('update:modelValue', { ...modelValue, projectTypes: $event })"
        />
        <ProposalFilterDropdown
          label="Mercado"
          :options="marketTypeOptions"
          :model-value="modelValue.marketTypes"
          @update:model-value="emit('update:modelValue', { ...modelValue, marketTypes: $event })"
        />
      </div>

      <!-- Hosting -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Hosting</span>
        <ProposalFilterDropdown
          label="Hosting"
          test-id="client-filter-hosting-status"
          :options="hostingStatusOptions"
          :model-value="modelValue.hostingStatus || []"
          @update:model-value="emit('update:modelValue', { ...modelValue, hostingStatus: $event })"
        />
      </div>

      <!-- Contabilidad -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Contabilidad</span>
        <ProposalFilterDropdown
          label="Facturación"
          test-id="client-filter-billing-data"
          :options="billingDataOptions"
          :model-value="modelValue.billingData || []"
          @update:model-value="emit('update:modelValue', { ...modelValue, billingData: $event })"
        />
      </div>

      <!-- Documentos -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Documentos</span>
        <ProposalFilterDropdown
          label="Documentos"
          test-id="client-filter-documents-status"
          :options="documentsStatusOptions"
          :model-value="modelValue.documentsStatus || []"
          @update:model-value="emit('update:modelValue', { ...modelValue, documentsStatus: $event })"
        />
      </div>

      <!-- Emails -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Emails</span>
        <ProposalFilterDropdown
          label="Correos"
          test-id="client-filter-email-status"
          :options="emailStatusOptions"
          :model-value="modelValue.emailStatus || []"
          @update:model-value="emit('update:modelValue', { ...modelValue, emailStatus: $event })"
        />
      </div>

      <!-- Fechas -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Fechas</span>
        <ProposalFilterRangeDropdown
          label="Última actividad"
          type="date"
          min-placeholder="Desde"
          max-placeholder="Hasta"
          :min-value="modelValue.lastActivityAfter"
          :max-value="modelValue.lastActivityBefore"
          @update:min-value="emit('update:modelValue', { ...modelValue, lastActivityAfter: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, lastActivityBefore: $event })"
        />
      </div>

      <!-- Limpiar todo -->
      <div class="flex items-center gap-2 px-3 py-2.5">
        <div class="flex-1" />
        <BaseButton variant="link" size="sm" class="whitespace-nowrap" v-if="filterCount > 0" @click="emit('reset')">
          Limpiar todo
        </BaseButton>
      </div>
    </div>

    <!-- Active filter chips -->
    <div v-if="activeChips.length > 0" class="flex flex-wrap items-center gap-1.5 mt-2 px-1">
      <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle mr-0.5">Activos:</span>
      <span
        v-for="chip in activeChips"
        :key="chip.key"
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-primary-soft text-text-brand"
      >
        {{ chip.label }}
        <BaseButton
          variant="danger-ghost"
          icon-only
          size="sm"
          aria-label="Quitar"
          :data-testid="`client-filter-chip-${chip.key}`"
          @click="clearChip(chip.key)"
        >&times;</BaseButton>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import ProposalFilterDropdown from '~/components/proposals/ProposalFilterDropdown.vue';
import ProposalFilterRangeDropdown from '~/components/proposals/ProposalFilterRangeDropdown.vue';
import {
  proposalStatusOptions as statusOptions,
  projectTypeOptions,
  marketTypeOptions,
  proposalStatusLabelMap as statusLabelMap,
  projectTypeLabelMap,
  marketTypeLabelMap,
} from '~/constants/filterOptions.js';
import { formatDate } from '~/utils/formatDate';
import { clientModuleName, subfilterOptionsFor } from '~/constants/clientFilters';

// Derived from the subfilters themselves, so the panel can always rebuild any
// predefined filter and the two can never drift apart.
const hostingStatusOptions = subfilterOptionsFor('hosting', 'hostingStatus');
const projectStatusOptions = subfilterOptionsFor('projects', 'projectStatus');
const billingDataOptions = subfilterOptionsFor('accounting', 'billingData');
const documentsStatusOptions = subfilterOptionsFor('documents', 'documentsStatus');
const diagnosticStatusOptions = subfilterOptionsFor('diagnostics', 'diagnosticStatus');
const emailStatusOptions = subfilterOptionsFor('emails', 'emailStatus');

/** Chip label prefixed with the module the cut belongs to. */
function moduleLabel(moduleId, text) {
  const name = clientModuleName(moduleId);
  return name ? `${name}: ${text}` : text;
}

function optionLabel(options, value) {
  return options.find((o) => o.value === value)?.label || value;
}

const props = defineProps({
  modelValue: { type: Object, required: true },
  isOpen: { type: Boolean, default: false },
  filterCount: { type: Number, default: 0 },
});

const emit = defineEmits(['update:modelValue', 'reset']);

function formatRange(min, max) {
  if (min != null && max != null) return `${min}–${max}`;
  if (min != null) return `≥ ${min}`;
  if (max != null) return `≤ ${max}`;
  return '';
}

function formatDateRange(after, before) {
  const fmt = (value) => formatDate(value, { fallback: value });
  if (after && before) return `${fmt(after)} → ${fmt(before)}`;
  if (after) return `desde ${fmt(after)}`;
  if (before) return `hasta ${fmt(before)}`;
  return '';
}

const activeChips = computed(() => {
  const chips = [];
  const mv = props.modelValue;

  // Every chip names the module its cut comes from, so a list narrowed from
  // several angles at once can still be read back one clause at a time.
  if (mv.lastStatuses?.length)
    chips.push({ key: 'lastStatuses', label: moduleLabel('proposals', mv.lastStatuses.map((s) => statusLabelMap[s] || s).join(', ')) });

  const total = formatRange(mv.totalProposalsMin, mv.totalProposalsMax);
  if (total) chips.push({ key: 'totalProposals', label: moduleLabel('proposals', `total ${total}`) });

  const accepted = formatRange(mv.acceptedMin, mv.acceptedMax);
  if (accepted) chips.push({ key: 'accepted', label: moduleLabel('proposals', `aceptadas ${accepted}`) });

  if (mv.diagnosticStatus?.length)
    chips.push({ key: 'diagnosticStatus', label: moduleLabel('diagnostics', mv.diagnosticStatus.map((v) => optionLabel(diagnosticStatusOptions, v)).join(', ')) });

  if (mv.projectStatus?.length)
    chips.push({ key: 'projectStatus', label: moduleLabel('projects', mv.projectStatus.map((v) => optionLabel(projectStatusOptions, v)).join(', ')) });

  if (mv.projectTypes?.length)
    chips.push({ key: 'projectTypes', label: moduleLabel('projects', `tipo ${mv.projectTypes.map((t) => projectTypeLabelMap[t] || t).join(', ')}`) });

  if (mv.marketTypes?.length)
    chips.push({ key: 'marketTypes', label: moduleLabel('projects', `mercado ${mv.marketTypes.map((t) => marketTypeLabelMap[t] || t).join(', ')}`) });

  if (mv.hostingStatus?.length)
    chips.push({ key: 'hostingStatus', label: moduleLabel('hosting', mv.hostingStatus.map((v) => optionLabel(hostingStatusOptions, v)).join(', ')) });

  if (mv.billingData?.length)
    chips.push({ key: 'billingData', label: moduleLabel('accounting', mv.billingData.map((v) => optionLabel(billingDataOptions, v)).join(', ')) });

  if (mv.documentsStatus?.length)
    chips.push({ key: 'documentsStatus', label: moduleLabel('documents', mv.documentsStatus.map((v) => optionLabel(documentsStatusOptions, v)).join(', ')) });

  if (mv.emailStatus?.length)
    chips.push({ key: 'emailStatus', label: moduleLabel('emails', mv.emailStatus.map((v) => optionLabel(emailStatusOptions, v)).join(', ')) });

  const ar = formatDateRange(mv.lastActivityAfter, mv.lastActivityBefore);
  if (ar) chips.push({ key: 'activityRange', label: `Actividad: ${ar}` });

  return chips;
});

const CHIP_RESET = {
  lastStatuses:   (mv) => { mv.lastStatuses = []; },
  projectTypes:   (mv) => { mv.projectTypes = []; },
  marketTypes:    (mv) => { mv.marketTypes = []; },
  totalProposals: (mv) => { mv.totalProposalsMin = null; mv.totalProposalsMax = null; },
  accepted:       (mv) => { mv.acceptedMin = null; mv.acceptedMax = null; },
  activityRange:  (mv) => { mv.lastActivityAfter = null; mv.lastActivityBefore = null; },
  hostingStatus:  (mv) => { mv.hostingStatus = []; },
  projectStatus:  (mv) => { mv.projectStatus = []; },
  billingData:    (mv) => { mv.billingData = []; },
  documentsStatus: (mv) => { mv.documentsStatus = []; },
  diagnosticStatus: (mv) => { mv.diagnosticStatus = []; },
  emailStatus:    (mv) => { mv.emailStatus = []; },
};

function clearChip(key) {
  const mv = { ...props.modelValue };
  CHIP_RESET[key]?.(mv);
  emit('update:modelValue', mv);
}
</script>
