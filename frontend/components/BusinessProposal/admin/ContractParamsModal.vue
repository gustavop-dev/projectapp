<template>
  <BaseModal
    :model-value="visible"
    :size="contractSource === 'custom' && showPreview ? '5xl' : 'lg'"
    @update:model-value="(v) => !v && $emit('cancel')"
  >
    <div>
      <div class="sticky top-0 bg-surface border-b border-border-muted px-6 py-4 rounded-t-2xl z-10">
            <h2 class="text-lg font-semibold text-text-default">
              {{ isEditing ? 'Editar contrato de desarrollo' : 'Generar contrato de desarrollo' }}
            </h2>
            <p class="text-xs text-text-muted mt-1">
              Usa el contrato por defecto con datos del cliente, o sube un contrato personalizado en Markdown.
            </p>
          </div>

          <form class="px-6 py-5 space-y-6" @submit.prevent="handleSubmit">
            <!-- Source toggle -->
            <BaseSegmented
              v-model="contractSource"
              class="max-w-md"
              full-width
              :options="[
                { value: 'default', label: 'Contrato por defecto' },
                { value: 'custom', label: 'Contrato personalizado' },
              ]"
            />

            <!-- DEFAULT MODE: contract params form -->
            <template v-if="contractSource === 'default'">
              <!-- Contractor (seller) section -->
              <fieldset>
                <legend class="text-sm font-semibold text-text-brand mb-3">EL CONTRATISTA (tu empresa)</legend>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Nombre completo</label>
                    <BaseInput v-model="form.contractor_full_name" type="text" size="sm" />
                  </div>
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Cedula</label>
                    <BaseInput v-model="form.contractor_cedula" type="text" size="sm" />
                  </div>
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Email de notificacion</label>
                    <BaseInput v-model="form.contractor_email" type="email" size="sm" />
                  </div>
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Ciudad del contrato</label>
                    <BaseInput v-model="form.contract_city" type="text" size="sm" />
                  </div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Banco</label>
                    <BaseInput v-model="form.bank_name" type="text" size="sm" />
                  </div>
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Tipo de cuenta</label>
                    <BaseSelect
                      v-model="form.bank_account_type"
                      size="sm"
                      :options="[{ value: 'Ahorros', label: 'Ahorros' }, { value: 'Corriente', label: 'Corriente' }]"
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Numero de cuenta</label>
                    <BaseInput v-model="form.bank_account_number" type="text" size="sm" />
                  </div>
                </div>
              </fieldset>

              <!-- Client (contratante) section -->
              <fieldset>
                <legend class="text-sm font-semibold text-text-brand mb-3">EL CONTRATANTE (cliente)</legend>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Nombre completo</label>
                    <BaseInput v-model="form.client_full_name" type="text" size="sm" />
                  </div>
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Cedula *</label>
                    <BaseInput v-model="form.client_cedula" type="text" size="sm" placeholder="Ej: 1.234.567.890" />
                  </div>
                  <div class="sm:col-span-2">
                    <label class="block text-xs text-text-muted mb-1">Email de notificacion</label>
                    <BaseInput v-model="form.client_email" type="email" size="sm" />
                  </div>
                </div>
              </fieldset>

              <!-- Contract date -->
              <fieldset>
                <legend class="text-sm font-semibold text-text-brand mb-3">Datos del contrato</legend>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Fecha del contrato</label>
                    <BaseInput v-model="form.contract_date" type="date" size="sm" />
                  </div>
                </div>
              </fieldset>
            </template>

            <!-- CUSTOM MODE: markdown editor -->
            <template v-else>
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label class="block text-sm font-medium text-text-default">Contenido del contrato (Markdown)</label>
                  <div class="flex items-center gap-2">
                    <label
                      class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg cursor-pointer
                             bg-surface-raised text-text-muted hover:bg-border-muted transition-colors"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      Cargar .md
                      <input type="file" accept=".md,.markdown,.txt" class="hidden" @change="handleFileUpload" />
                    </label>
                    <button type="button"
                      :class="['inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors',
                        showPreview
                          ? 'bg-success-soft text-success-strong hover:opacity-90'
                          : 'bg-surface-raised text-text-muted hover:bg-border-muted']"
                      @click="showPreview = !showPreview"
                    >
                      {{ showPreview ? 'Ocultar preview' : 'Vista previa' }}
                    </button>
                  </div>
                </div>
                <div :class="showPreview ? 'grid grid-cols-1 lg:grid-cols-2 gap-4' : ''">
                  <textarea
                    v-model="customMarkdown"
                    rows="14"
                    placeholder="# Contrato de prestacion de servicios&#10;&#10;Pega o escribe tu contrato en formato Markdown..."
                    class="w-full px-4 py-3 border border-input-border rounded-xl text-sm font-mono leading-relaxed
                           bg-input-bg text-input-text placeholder:text-text-subtle
                           focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-y"
                  ></textarea>
                  <div
                    v-if="showPreview"
                    class="border border-border-default rounded-xl bg-surface overflow-y-auto"
                    style="min-height: 20rem; max-height: 36rem;"
                  >
                    <div class="px-3 py-2 border-b border-border-muted bg-surface-raised rounded-t-xl">
                      <span class="text-xs font-medium text-text-muted uppercase tracking-wide">Vista previa</span>
                    </div>
                    <div
                      v-if="customMarkdown.trim()"
                      class="markdown-preview px-5 py-4 text-text-default"
                      v-html="previewHtml"
                    ></div>
                    <div v-else class="flex items-center justify-center h-48 text-sm text-text-subtle">
                      Escribe markdown para ver la vista previa...
                    </div>
                  </div>
                </div>
              </div>

              <!-- Contract date (also for custom) -->
              <fieldset>
                <legend class="text-sm font-semibold text-text-brand mb-3">Datos del contrato</legend>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs text-text-muted mb-1">Fecha del contrato</label>
                    <BaseInput v-model="form.contract_date" type="date" size="sm" />
                  </div>
                </div>
              </fieldset>
            </template>

            <!-- Actions -->
            <div class="flex items-center justify-end gap-3 pt-4 border-t border-border-muted">
              <BaseButton variant="ghost" size="md" @click="$emit('cancel')">
                Cancelar
              </BaseButton>
              <BaseButton
                type="submit"
                variant="primary"
                size="md"
                :loading="saving"
                :disabled="saving || (contractSource === 'custom' && !customMarkdown.trim())"
              >
                {{ saving ? 'Generando...' : (isEditing ? 'Actualizar contrato' : 'Generar contrato y negociar') }}
              </BaseButton>
            </div>
          </form>
    </div>
  </BaseModal>
</template>

<script setup>
import { ref, watch, computed, onBeforeUnmount } from 'vue';
import DOMPurify from 'dompurify';

const { parseMarkdown } = useMarkdownPreview();

const props = defineProps({
  visible: { type: Boolean, default: false },
  proposal: { type: Object, default: () => ({}) },
  initialParams: { type: Object, default: () => ({}) },
  isEditing: { type: Boolean, default: false },
  saving: { type: Boolean, default: false },
});

const emit = defineEmits(['confirm', 'cancel']);

const proposalStore = useProposalStore();
const companyDefaults = ref({});
const contractSource = ref('default');
const customMarkdown = ref('');
const showPreview = ref(false);

const debouncedMarkdown = ref('');
let debounceTimer = null;
onBeforeUnmount(() => { clearTimeout(debounceTimer); });
watch(customMarkdown, (val) => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => { debouncedMarkdown.value = val; }, 200);
}, { immediate: true });

const previewHtml = computed(() => DOMPurify.sanitize(parseMarkdown(debouncedMarkdown.value)));

const form = ref({
  contractor_full_name: '',
  contractor_cedula: '',
  contractor_email: '',
  bank_name: '',
  bank_account_type: 'Ahorros',
  bank_account_number: '',
  contract_city: 'Medellín',
  client_full_name: '',
  client_cedula: '',
  client_email: '',
  contract_date: new Date().toISOString().slice(0, 10),
});

async function loadDefaults() {
  const result = await proposalStore.fetchCompanySettings();
  if (result.success) {
    companyDefaults.value = result.data;
  }
}

function resetForm() {
  const defaults = companyDefaults.value;
  const existing = props.initialParams || {};
  const p = props.proposal || {};

  contractSource.value = existing.contract_source || 'default';
  customMarkdown.value = existing.custom_contract_markdown || '';

  form.value = {
    contractor_full_name: existing.contractor_full_name || defaults.contractor_full_name || '',
    contractor_cedula: existing.contractor_cedula || defaults.contractor_cedula || '',
    contractor_email: existing.contractor_email || defaults.contractor_email || '',
    bank_name: existing.bank_name || defaults.bank_name || '',
    bank_account_type: existing.bank_account_type || defaults.bank_account_type || 'Ahorros',
    bank_account_number: existing.bank_account_number || defaults.bank_account_number || '',
    contract_city: existing.contract_city || defaults.contract_city || 'Medellín',
    client_full_name: existing.client_full_name || p.client_name || '',
    client_cedula: existing.client_cedula || '',
    client_email: existing.client_email || p.client_email || '',
    contract_date: existing.contract_date || new Date().toISOString().slice(0, 10),
  };
}

watch(() => props.visible, async (val) => {
  if (val) {
    if (!companyDefaults.value.contractor_full_name) {
      await loadDefaults();
    }
    resetForm();
  }
});

function handleFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    customMarkdown.value = e.target?.result || '';
  };
  reader.readAsText(file);
}

function handleSubmit() {
  if (contractSource.value === 'custom') {
    emit('confirm', {
      contract_source: 'custom',
      custom_contract_markdown: customMarkdown.value,
      contract_date: form.value.contract_date,
    });
  } else {
    emit('confirm', {
      contract_source: 'default',
      ...form.value,
    });
  }
}
</script>

