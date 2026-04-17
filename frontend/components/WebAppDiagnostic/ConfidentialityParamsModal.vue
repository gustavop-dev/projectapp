<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/50" @click="$emit('cancel')" />

        <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
          <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 px-6 py-4 rounded-t-2xl z-10">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Acuerdo de Confidencialidad</h2>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Datos para rellenar la plantilla. Los campos vacíos quedarán como
              <span class="font-mono">_______________</span> en el PDF.
            </p>
          </div>

          <form class="overflow-y-auto flex-1 px-6 py-5 space-y-6" @submit.prevent="handleSave">
            <section>
              <h3 class="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400 mb-3">
                Cliente
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <label class="block">
                  <span class="text-xs text-gray-500 dark:text-white/70">Razón social / Nombre</span>
                  <input v-model="form.client_full_name" type="text" class="nda-input" />
                </label>
                <label class="block">
                  <span class="text-xs text-gray-500 dark:text-white/70">NIT / C.C.</span>
                  <input v-model="form.client_cedula" type="text" class="nda-input" />
                </label>
                <label class="block sm:col-span-2">
                  <span class="text-xs text-gray-500 dark:text-white/70">Representante legal</span>
                  <input v-model="form.client_legal_representative" type="text" class="nda-input" />
                </label>
                <label class="block sm:col-span-2">
                  <span class="text-xs text-gray-500 dark:text-white/70">Correo electrónico</span>
                  <input v-model="form.client_email" type="email" class="nda-input" />
                </label>
              </div>
            </section>

            <section>
              <h3 class="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400 mb-3">
                Consultor (Project App)
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <label class="block">
                  <span class="text-xs text-gray-500 dark:text-white/70">Razón social / Nombre</span>
                  <input v-model="form.contractor_full_name" type="text" class="nda-input" />
                </label>
                <label class="block">
                  <span class="text-xs text-gray-500 dark:text-white/70">NIT / C.C.</span>
                  <input v-model="form.contractor_cedula" type="text" class="nda-input" />
                </label>
                <label class="block sm:col-span-2">
                  <span class="text-xs text-gray-500 dark:text-white/70">Correo electrónico</span>
                  <input v-model="form.contractor_email" type="email" class="nda-input" />
                </label>
              </div>
            </section>

            <section>
              <h3 class="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400 mb-3">
                Datos del acuerdo
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <label class="block sm:col-span-2">
                  <span class="text-xs text-gray-500 dark:text-white/70">Ciudad</span>
                  <input v-model="form.contract_city" type="text" class="nda-input" />
                </label>
                <label class="block">
                  <span class="text-xs text-gray-500 dark:text-white/70">Día</span>
                  <input v-model="form.contract_day" type="text" placeholder="Ej: 16" class="nda-input" />
                </label>
                <label class="block">
                  <span class="text-xs text-gray-500 dark:text-white/70">Mes</span>
                  <input v-model="form.contract_month" type="text" placeholder="Ej: abril" class="nda-input" />
                </label>
                <label class="block">
                  <span class="text-xs text-gray-500 dark:text-white/70">Año</span>
                  <input v-model="form.contract_year" type="text" placeholder="Ej: 2026" class="nda-input" />
                </label>
                <label class="block sm:col-span-2">
                  <span class="text-xs text-gray-500 dark:text-white/70">Cláusula penal (valor)</span>
                  <input v-model="form.penal_clause_value" type="text" class="nda-input" />
                </label>
              </div>
            </section>

            <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
          </form>

          <div class="border-t border-gray-100 dark:border-gray-700 px-6 py-4 rounded-b-2xl bg-white dark:bg-gray-800">
            <div class="flex items-center justify-end gap-3">
              <button type="button"
                class="px-4 py-2 text-sm text-gray-600 dark:text-white hover:text-gray-800 dark:hover:text-white transition-colors"
                @click="$emit('cancel')">Cancelar</button>
              <button type="button" :disabled="saving"
                class="inline-flex items-center gap-1.5 px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
                @click="handleSave">
                <svg v-if="saving" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ saving ? 'Generando...' : 'Guardar y generar PDF' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';

const props = defineProps({
  visible: { type: Boolean, default: false },
  diagnostic: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['cancel', 'saved']);

const store = useDiagnosticsStore();

const DEFAULTS = {
  contractor_full_name: 'Project App SAS',
  contract_city: 'Medellín',
  penal_clause_value: 'CINCUENTA SALARIOS MÍNIMOS MENSUALES LEGALES VIGENTES (50 SMMLV)',
  contractor_email: 'team@projectapp.co',
};

const EMPTY_FORM = {
  client_full_name: '',
  client_cedula: '',
  client_legal_representative: '',
  client_email: '',
  contractor_full_name: '',
  contractor_cedula: '',
  contractor_email: '',
  contract_city: '',
  contract_day: '',
  contract_month: '',
  contract_year: '',
  penal_clause_value: '',
};

const form = ref({ ...EMPTY_FORM });
const saving = ref(false);
const error = ref('');

watch(
  () => props.visible,
  (val) => {
    if (!val) return;
    error.value = '';
    const stored = props.diagnostic?.confidentiality_params || {};
    const clientName = props.diagnostic?.client?.name || '';
    const clientEmail = props.diagnostic?.client?.email || '';
    form.value = {
      ...EMPTY_FORM,
      ...DEFAULTS,
      client_full_name: stored.client_full_name || clientName,
      client_email: stored.client_email || clientEmail,
      ...stored,
    };
  },
);

async function handleSave() {
  saving.value = true;
  error.value = '';
  const payload = {};
  Object.keys(EMPTY_FORM).forEach((key) => {
    const value = (form.value[key] || '').trim();
    if (value) payload[key] = value;
  });
  const result = await store.updateConfidentialityParams(props.diagnostic.id, payload);
  saving.value = false;
  if (result.success) {
    emit('saved', result.data);
  } else {
    error.value = result.error || 'No se pudo guardar.';
  }
}
</script>

<style scoped>
.nda-input {
  @apply mt-1 w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-500 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
