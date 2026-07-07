<template>
  <ConfirmModal
    v-model="confirmState.open"
    :title="confirmState.title"
    :message="confirmState.message"
    :confirm-text="confirmState.confirmText"
    :cancel-text="confirmState.cancelText"
    :variant="confirmState.variant"
    @confirm="handleConfirmed"
    @cancel="handleCancelled"
  />
  <TabSplitLayout>
    <template #main>
  <!-- Current JSON (read-only) -->
  <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
      <div>
        <h3 class="text-sm font-medium text-text-default">JSON de la propuesta</h3>
        <p class="text-xs text-text-subtle mt-0.5">Representación JSON completa — se actualiza al guardar cambios en otras pestañas.</p>
      </div>
      <div class="flex items-center gap-2 flex-shrink-0">
        <BaseButton variant="secondary" size="sm" :disabled="jsonExportLoading" @click="refreshExportJson">
          <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': jsonExportLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Actualizar
        </BaseButton>
        <BaseButton variant="secondary" size="sm" @click="copyExportJson">
          <DocumentDuplicateIcon class="w-3.5 h-3.5" />
          {{ jsonCopied ? '¡Copiado!' : 'Copiar' }}
        </BaseButton>
        <BaseButton variant="secondary" size="sm" @click="downloadExportJson">
          <ArrowDownTrayIcon class="w-3.5 h-3.5" />
          Descargar
        </BaseButton>
      </div>
    </div>

    <div v-if="jsonExportLoading" class="text-center py-8 text-text-subtle text-sm">
      Cargando JSON...
    </div>
    <template v-else>
      <JsonStatsPanel class="mb-4" :stats="proposalJsonStats" test-id="proposal-json-stats" />
      <textarea
        :value="exportJsonString"
        readonly
        data-testid="proposal-export-json-textarea"
        :rows="JSON_TEXTAREA_ROWS"
        class="w-full px-4 py-3 border border-border-default rounded-xl text-xs font-mono leading-relaxed
               bg-surface-raised text-text-default outline-none resize-y cursor-text select-all"
      />
    </template>
  </div>

    </template>

    <template #aside>
  <!-- Import JSON -->
  <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
    <h3 class="text-sm font-medium text-text-default mb-1">Importar JSON</h3>
    <p class="text-xs text-text-subtle mb-4">Pega o sube un JSON para reemplazar el contenido de la propuesta (metadata + secciones).</p>

    <div class="flex items-center gap-3 mb-3">
      <label
        class="inline-flex items-center gap-2 px-3 py-1.5 border border-border-default rounded-lg text-xs
               text-text-default hover:bg-surface-raised cursor-pointer transition-colors"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        Subir .json
        <input type="file" accept=".json" class="hidden" @change="handleJsonFileUpload" />
      </label>
      <span v-if="jsonImportFileName" class="text-xs text-text-muted">{{ jsonImportFileName }}</span>
    </div>

    <textarea
      v-model="jsonImportRaw"
      data-testid="proposal-import-json-textarea"
      :rows="JSON_TEXTAREA_ROWS"
      placeholder='Pega aquí el JSON completo de la propuesta...'
      class="bg-input-bg w-full px-4 py-3 border border-border-default rounded-xl text-xs font-mono leading-relaxed
             focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-y"
      @input="parseImportJson"
    />

    <!-- Parse error -->
    <div v-if="jsonImportError" class="mt-2 text-sm text-danger-strong bg-danger-soft px-4 py-2 rounded-lg">
      {{ jsonImportError }}
    </div>

    <!-- Preview -->
    <div v-if="jsonImportParsed && !jsonImportError" class="mt-3 bg-primary-soft border border-primary/30 rounded-lg px-4 py-3">
      <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <span><span class="text-text-muted">Cliente:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.clientName }}</span></span>
        <span><span class="text-text-muted">Secciones:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.sectionCount }}</span></span>
        <span v-if="jsonImportPreview.epicCount != null"><span class="text-text-muted">Módulos (téc.):</span> <span class="font-medium text-text-default">{{ jsonImportPreview.epicCount }}</span></span>
        <span v-if="jsonImportPreview.investment"><span class="text-text-muted">Inversión:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.investment }}</span></span>
      </div>
    </div>

    <!-- Legacy format warning -->
    <LegacyFormatWarning
      v-if="jsonImportParsed && !jsonImportError"
      :issues="jsonImportLegacyIssues"
      :field-labels="LEGACY_FIELD_LABELS"
      action-label="Descarga la versión corregida y úsala para actualizar la propuesta:"
      @download="downloadMigratedProposalJson(jsonImportParsed)"
    />

    <!-- Apply button -->
    <div v-if="jsonImportParsed && !jsonImportError && !jsonImportLegacyIssues.length" class="mt-4 flex flex-wrap items-center gap-3">
      <button
        type="button"
        :disabled="proposalStore.isUpdating"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-xl font-medium text-sm
               hover:bg-primary transition-colors shadow-sm disabled:opacity-50 disabled:cursor-wait"
        @click="handleApplyImportJson"
      >
        <svg v-if="proposalStore.isUpdating" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        {{ proposalStore.isUpdating ? 'Aplicando...' : 'Aplicar JSON' }}
      </button>
      <p class="text-xs text-text-subtle">Esto reemplazará la metadata y todas las secciones de la propuesta.</p>
    </div>

  </div>
    </template>
  </TabSplitLayout>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { DocumentDuplicateIcon, ArrowDownTrayIcon } from '@heroicons/vue/24/outline';
import JsonStatsPanel from '~/components/BusinessProposal/admin/JsonStatsPanel.vue';
import TabSplitLayout from '~/components/panel/TabSplitLayout.vue';
import LegacyFormatWarning from '~/components/panel/LegacyFormatWarning.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useProposalStore } from '~/stores/proposals';
import { detectLegacyTechnicalFormat, downloadMigratedProposalJson, LEGACY_FIELD_LABELS } from '~/utils/proposalJsonMigration';
import { JSON_TEXTAREA_ROWS, makeJsonStats } from '~/utils/proposalJsonStats';

const props = defineProps({
  proposal: {
    type: Object,
    default: null,
  },
  active: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['applied']);

const proposalStore = useProposalStore();
const notify = usePanelNotify();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const EXPECTED_SECTION_KEYS = [
  'general', 'executiveSummary', 'contextDiagnostic', 'conversionStrategy',
  'designUX', 'creativeSupport', 'developmentStages', 'processMethodology',
  'valueAddedModules', 'functionalRequirements', 'timeline', 'investment',
  'proposalSummary', 'finalNote', 'nextSteps', 'technicalDocument',
];

const jsonExportLoading = ref(false);
const exportJsonData = ref(null);
const jsonCopied = ref(false);

const jsonImportRaw = ref('');
const jsonImportParsed = ref(null);
const jsonImportError = ref('');
const jsonImportFileName = ref('');
const jsonImportLegacyIssues = ref([]);

const exportJsonString = computed(() => {
  if (!exportJsonData.value) return '';
  return JSON.stringify(exportJsonData.value, null, 2);
});

const proposalJsonStats = makeJsonStats({
  sourceRef: exportJsonData,
  rawStringRef: exportJsonString,
  expectedKeys: EXPECTED_SECTION_KEYS,
  updatedAtRef: computed(() => props.proposal?.updated_at),
});

const jsonImportPreview = computed(() => {
  if (!jsonImportParsed.value) return {};
  const p = jsonImportParsed.value;
  const clientName = p.general?.clientName || '';
  const sectionCount = EXPECTED_SECTION_KEYS.filter((k) => k in p).length;
  const investment = p.investment?.totalInvestment || '';
  const epics = p.technicalDocument?.epics;
  const epicCount = Array.isArray(epics) ? epics.length : null;
  return { clientName, sectionCount, investment, epicCount };
});

async function refreshExportJson() {
  if (!props.proposal?.id) return;
  jsonExportLoading.value = true;
  try {
    const result = await proposalStore.exportProposalJSON(props.proposal.id);
    if (result.success) {
      exportJsonData.value = result.data;
    }
  } finally {
    jsonExportLoading.value = false;
  }
}

async function copyExportJson() {
  if (!exportJsonString.value) return;
  try {
    await navigator.clipboard.writeText(exportJsonString.value);
    jsonCopied.value = true;
    setTimeout(() => { jsonCopied.value = false; }, 2000);
  } catch (e) {
    console.error('Copy failed:', e);
  }
}

function downloadExportJson() {
  if (!exportJsonString.value || !props.proposal) return;
  const blob = new Blob([exportJsonString.value], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `proposal-${props.proposal.uuid || props.proposal.id}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function parseImportJson() {
  jsonImportError.value = '';
  jsonImportParsed.value = null;
  jsonImportLegacyIssues.value = [];

  const raw = jsonImportRaw.value.trim();
  if (!raw) return;

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    jsonImportError.value = 'JSON inválido. Revisa la sintaxis.';
    return;
  }

  if (typeof parsed !== 'object' || Array.isArray(parsed)) {
    jsonImportError.value = 'El JSON debe ser un objeto, no un array.';
    return;
  }

  if (!parsed.general || !parsed.general.clientName) {
    jsonImportError.value = 'El JSON debe incluir "general" con "clientName".';
    return;
  }

  jsonImportLegacyIssues.value = detectLegacyTechnicalFormat(parsed).issues;

  jsonImportParsed.value = parsed;
}

function handleJsonFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  jsonImportFileName.value = file.name;

  const reader = new FileReader();
  reader.onload = (e) => {
    jsonImportRaw.value = e.target.result;
    parseImportJson();
  };
  reader.readAsText(file);
}

function parseInvestmentString(str) {
  if (!str) return 0;
  if (typeof str === 'number') return str;
  const cleaned = String(str).replace(/[^0-9]/g, '');
  return cleaned ? Number(cleaned) : 0;
}

function handleApplyImportJson() {
  if (!jsonImportParsed.value || !props.proposal?.id) return;

  requestConfirm({
    title: 'Aplicar JSON',
    message: 'Esto reemplazará la metadata y todas las secciones de la propuesta. ¿Continuar?',
    variant: 'warning',
    confirmText: 'Aplicar',
    cancelText: 'Cancelar',
    onConfirm: async () => {
      const sections = { ...jsonImportParsed.value };
      delete sections._meta;
      delete sections._seller_prompt;

      const meta = jsonImportParsed.value._meta || {};
      const payload = {
        title: meta.title || props.proposal.title,
        client_name: jsonImportParsed.value.general?.clientName || props.proposal.client_name,
        client_email: meta.client_email || props.proposal.client_email || '',
        client_phone: meta.client_phone || props.proposal.client_phone || '',
        project_type: meta.project_type || props.proposal.project_type || '',
        market_type: meta.market_type || props.proposal.market_type || '',
        project_type_custom: meta.project_type_custom || props.proposal.project_type_custom || '',
        market_type_custom: meta.market_type_custom || props.proposal.market_type_custom || '',
        language: meta.language || props.proposal.language || 'es',
        total_investment: parseInvestmentString(meta.total_investment || jsonImportParsed.value.investment?.totalInvestment) || Number(props.proposal.total_investment) || 0,
        currency: meta.currency || jsonImportParsed.value.investment?.currency || props.proposal.currency || 'COP',
        expires_at: meta.expires_at || (props.proposal.expires_at ? props.proposal.expires_at : null),
        reminder_days: meta.reminder_days || props.proposal.reminder_days || 10,
        urgency_reminder_days: meta.urgency_reminder_days || props.proposal.urgency_reminder_days || 15,
        discount_percent: meta.discount_percent ?? props.proposal.discount_percent ?? 0,
        sections,
      };

      const result = await proposalStore.updateProposalFromJSON(props.proposal.id, payload);
      if (result.success) {
        notify.success({ title: 'Propuesta actualizada desde JSON.' });
        jsonImportRaw.value = '';
        jsonImportParsed.value = null;
        jsonImportFileName.value = '';
        jsonImportLegacyIssues.value = [];

        // Let the page sync its local form with the updated proposal.
        emit('applied');

        // Refresh the export JSON view
        await refreshExportJson();
      } else {
        const errors = result.errors;
        notify.error({
          title: 'Error al aplicar el JSON.',
          detail: errors
            ? (typeof errors === 'object'
              ? Object.entries(errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
              : String(errors))
            : '',
        });
      }
    },
  });
}

// Auto-load JSON export when the page switches to the json tab
watch(() => props.active, (isActive) => {
  if (isActive && props.proposal?.id) {
    refreshExportJson();
  }
});
</script>
